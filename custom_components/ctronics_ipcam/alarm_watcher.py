"""Watches the folder the camera uploads its alarm snapshots into.

Why this exists: the camera's AI person detection can only announce itself by
FTP, e-mail or SD card — there is no webhook and no status field to poll. So
the camera is pointed at a folder on the Home Assistant machine, and a new
image appearing in that folder *is* the detection event.

Only the newest snapshot is kept; older ones are removed so the folder can't
grow without bound as more cameras are added.
"""
from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import (
    DELETE_GRACE_SECONDS,
    FOLDER_POLL_INTERVAL,
    IMAGE_SUFFIXES,
)

_LOGGER = logging.getLogger(__name__)


class AlarmFolderWatcher:
    """Turns "a new image appeared" into a detection event entities can use."""

    def __init__(self, hass: HomeAssistant, folder: str, off_delay: int) -> None:
        self.hass = hass
        self.folder = Path(folder)
        self.off_delay = off_delay

        self.detected = False
        self.latest_file: Path | None = None
        self.last_detected: datetime | None = None

        self._listeners: list[Callable[[], None]] = []
        self._unsub_poll: Callable[[], None] | None = None
        self._unsub_off: Callable[[], None] | None = None
        self._last_mtime = 0.0

    # ── entity plumbing ──────────────────────────────────────────────

    @callback
    def async_add_listener(self, update_callback: Callable[[], None]) -> Callable[[], None]:
        """Register an entity to be told when something changes."""
        self._listeners.append(update_callback)

        @callback
        def _remove() -> None:
            if update_callback in self._listeners:
                self._listeners.remove(update_callback)

        return _remove

    @callback
    def _notify(self) -> None:
        for update_callback in list(self._listeners):
            update_callback()

    # ── lifecycle ────────────────────────────────────────────────────

    async def async_start(self) -> None:
        await self.hass.async_add_executor_job(self._prepare_folder)
        # Treat whatever is already lying there as old, so restarting Home
        # Assistant doesn't instantly report a detection from a stale image.
        self._last_mtime = await self.hass.async_add_executor_job(self._newest_mtime)
        self._unsub_poll = async_track_time_interval(
            self.hass, self._async_poll, FOLDER_POLL_INTERVAL
        )
        _LOGGER.debug("Watching %s for alarm snapshots", self.folder)

    @callback
    def async_stop(self) -> None:
        if self._unsub_poll is not None:
            self._unsub_poll()
            self._unsub_poll = None
        if self._unsub_off is not None:
            self._unsub_off()
            self._unsub_off = None

    # ── polling ──────────────────────────────────────────────────────

    async def _async_poll(self, _now: datetime | None = None) -> None:
        try:
            files = await self.hass.async_add_executor_job(self._scan)
        except OSError as err:
            _LOGGER.debug("Cannot read %s: %s", self.folder, err)
            return

        if not files:
            return

        newest_mtime, newest_path = files[-1]
        if newest_mtime <= self._last_mtime:
            return

        self._last_mtime = newest_mtime
        self.latest_file = newest_path
        self.last_detected = dt_util.utcnow()
        self.detected = True
        self._notify()
        self._schedule_off()

        await self.hass.async_add_executor_job(self._cleanup, newest_path)

    @callback
    def _schedule_off(self) -> None:
        """(Re)start the countdown that clears the sensor after the last image."""
        if self._unsub_off is not None:
            self._unsub_off()
        self._unsub_off = async_call_later(self.hass, self.off_delay, self._async_clear)

    @callback
    def _async_clear(self, _now: datetime) -> None:
        self._unsub_off = None
        self.detected = False
        self._notify()

    async def async_image_bytes(self) -> bytes | None:
        """The most recent snapshot, for the image entity."""
        path = self.latest_file
        if path is None:
            return None
        try:
            return await self.hass.async_add_executor_job(path.read_bytes)
        except OSError as err:
            _LOGGER.debug("Cannot read %s: %s", path, err)
            return None

    # ── blocking helpers, all run in the executor ────────────────────

    def _prepare_folder(self) -> None:
        try:
            self.folder.mkdir(parents=True, exist_ok=True)
        except OSError as err:
            _LOGGER.warning("Cannot create %s: %s", self.folder, err)

    def _scan(self) -> list[tuple[float, Path]]:
        """All image files in the folder, oldest first."""
        found: list[tuple[float, Path]] = []
        with os.scandir(self.folder) as entries:
            for entry in entries:
                if not entry.is_file():
                    continue
                if not entry.name.lower().endswith(IMAGE_SUFFIXES):
                    continue
                try:
                    found.append((entry.stat().st_mtime, Path(entry.path)))
                except OSError:
                    continue
        found.sort()
        return found

    def _newest_mtime(self) -> float:
        try:
            files = self._scan()
        except OSError:
            return 0.0
        return files[-1][0] if files else 0.0

    def _cleanup(self, keep: Path) -> None:
        """Delete every snapshot except the newest one.

        Files touched in the last few seconds are left alone — they may still
        be uploading, and deleting a half-written file mid-transfer would only
        confuse the camera's FTP client.
        """
        cutoff = time.time() - DELETE_GRACE_SECONDS
        try:
            files = self._scan()
        except OSError:
            return
        for mtime, path in files:
            if path == keep or mtime > cutoff:
                continue
            try:
                path.unlink()
            except OSError as err:
                _LOGGER.debug("Cannot delete %s: %s", path, err)
