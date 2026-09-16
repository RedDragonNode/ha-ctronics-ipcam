"""Async client for this camera's native Hi3510 CGI API.

The camera identifies itself with the HTTP response header ``Server: Hipcam``
and exposes its native (non-ONVIF) control surface at
``/web/cgi-bin/hi3510/param.cgi``, confirmed by capturing the camera's own
web UI's network traffic. The GET-based single-command request/response
pattern below (query-string params, ``var key="value";`` response body,
``[Succeed]``/``[Error]`` markers on writes) is the standard convention used
across Hi3510-family cameras, including the community ``ha-hi3510``
integration for a near-identical Ctronics model — reused here since our own
capture only observed the browser's batched POST form-submit, not a bare
single-command GET. This should be verified against this camera on first
real use (the config flow's connection test already does this for reads);
if a write ever silently fails, capture that specific request the same way
the read commands were captured and adjust here.
"""
from __future__ import annotations

import asyncio
import logging
import re
from urllib.parse import quote

import aiohttp

from .const import (
    CGI_PARAM_PATH,
    CGI_PTZCTRL_PATH,
    SNAPSHOT_PATH_CACHED,
    SNAPSHOT_PATH_FRESH,
    SNAPSHOT_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)

_RESPONSE_RE = re.compile(r'var\s+(\w+)\s*=\s*"?([^";]*)"?\s*;')


class CtronicsApiError(Exception):
    """Base error for all API problems."""


class CtronicsAuthError(CtronicsApiError):
    """Wrong username/password."""


class CtronicsConnectionError(CtronicsApiError):
    """Camera unreachable / timed out."""


class CtronicsCommandError(CtronicsApiError):
    """Camera answered but rejected the command."""


class CtronicsClient:
    """Thin async wrapper around the camera's param.cgi endpoint."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        username: str,
        password: str,
        port: int = 80,
    ) -> None:
        self._session = session
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._auth = aiohttp.BasicAuth(username, password)
        self._base_url = f"http://{host}:{port}{CGI_PARAM_PATH}"
        self._ptz_url = f"http://{host}:{port}{CGI_PTZCTRL_PATH}"
        self._timeout = aiohttp.ClientTimeout(total=10)
        # A 4K still is far bigger than a CGI reply, so it gets its own budget.
        self._image_timeout = aiohttp.ClientTimeout(total=SNAPSHOT_TIMEOUT)
        # Set to False once a command turns out not to exist on this firmware,
        # so we stop re-requesting a known 404 on every refresh.
        self._ircut_supported: bool | None = None
        # The camera's own web UI always sends these; without them some write
        # commands (e.g. preset goto) were observed to silently no-op.
        self._extra_headers = {
            "Cookie": "cookmun=1",
            "Referer": f"http://{host}/web/mainpage.html",
        }

    @staticmethod
    def _build_query(cmd: str, params: dict[str, str] | None) -> str:
        """Build the query string by hand.

        The camera expects raw ``-prefixed`` keys and (per the "preset"
        command) sometimes a key with no dash at all, so we do not let a
        generic dict-based query builder reshape anything — every key is
        sent byte-for-byte as given.
        """
        parts = [f"cmd={quote(cmd, safe='')}"]
        for key, value in (params or {}).items():
            parts.append(f"{key}={quote(str(value), safe='')}")
        return "&".join(parts)

    async def _get(self, cmd: str, params: dict[str, str] | None = None) -> str:
        url = f"{self._base_url}?{self._build_query(cmd, params)}"
        _LOGGER.debug("GET %s", url)
        try:
            async with self._session.get(
                url, auth=self._auth, timeout=self._timeout, headers=self._extra_headers
            ) as resp:
                if resp.status == 401:
                    raise CtronicsAuthError("HTTP 401 Unauthorized")
                resp.raise_for_status()
                return await resp.text()
        except CtronicsApiError:
            raise
        except aiohttp.ClientError as err:
            raise CtronicsConnectionError(f"{self._host}: {err}") from err
        except TimeoutError as err:
            raise CtronicsConnectionError(f"Timeout reaching {self._host}") from err

    async def _get_raw(self, base_url: str, params: dict[str, str]) -> str:
        """GET a URL whose query string has no leading cmd= (e.g. ptzctrl.cgi)."""
        parts = [f"{key}={quote(str(value), safe='')}" for key, value in params.items()]
        url = f"{base_url}?{'&'.join(parts)}"
        _LOGGER.debug("GET %s", url)
        try:
            async with self._session.get(
                url, auth=self._auth, timeout=self._timeout, headers=self._extra_headers
            ) as resp:
                if resp.status == 401:
                    raise CtronicsAuthError("HTTP 401 Unauthorized")
                resp.raise_for_status()
                return await resp.text()
        except CtronicsApiError:
            raise
        except aiohttp.ClientError as err:
            raise CtronicsConnectionError(f"{self._host}: {err}") from err
        except TimeoutError as err:
            raise CtronicsConnectionError(f"Timeout reaching {self._host}") from err

    @staticmethod
    def parse(text: str) -> dict[str, str]:
        """Parse a ``var key="value";`` (or ``var key=value;``) response body."""
        if "[Error]" in text:
            raise CtronicsCommandError(text.strip())
        return {m.group(1): m.group(2) for m in _RESPONSE_RE.finditer(text)}

    async def execute(self, cmd: str, params: dict[str, str] | None = None) -> dict[str, str]:
        """Run a read (``get...``) command and return the parsed key/value pairs."""
        text = await self._get(cmd, params)
        return self.parse(text)

    async def execute_set(self, cmd: str, params: dict[str, str]) -> bool:
        """Run a write (``set...``) command. Returns True on an explicit success marker.

        Some firmwares don't echo ``[Succeed]`` on every set command, so a
        request that came back without an ``[Error]`` (raised above) is also
        treated as accepted — callers should re-read the value afterwards
        (the coordinator refresh after every write does this) to confirm.
        """
        text = await self._get(cmd, params)
        ok = "[Succeed]" in text or "[Error]" not in text
        _LOGGER.debug("SET %s -> %s (ok=%s)", cmd, text.strip()[:200], ok)
        return ok

    # ── AI person detection ("Intelligente Identifizierung") ───────────

    async def get_smd_enabled(self) -> bool:
        data = await self.execute("getsmdattr")
        return data.get("smd_enable", "0") == "1"

    async def set_smd_enabled(self, enable: bool) -> bool:
        return await self.execute_set("setsmdattr", {"-smd_enable": "1" if enable else "0"})

    async def get_smd_ex(self) -> dict[str, str]:
        """Returns smd_rect, smd_gthresh (threshold 1-100), smd_type."""
        return await self.execute("getsmdex")

    async def set_smd_threshold(self, threshold: int, smd_rect: str = "0", smd_type: str = "0") -> bool:
        """Set the detection threshold (1-100).

        The camera's own UI always resubmits smd_rect/smd_type alongside
        smd_gthresh in one save, so we do the same to avoid resetting fields
        we don't otherwise expose yet. Pass the currently-known smd_rect/
        smd_type (e.g. from the coordinator) to preserve them.
        """
        return await self.execute_set(
            "setsmdex",
            {"-smd_rect": smd_rect, "-smd_gthresh": str(threshold), "-smd_type": smd_type},
        )

    # ── Auto-Tracking ("Smart Track") ───────────────────────────────────

    async def get_smartrack_enabled(self) -> bool:
        data = await self.execute("getsmartrackattr")
        return data.get("smartrack_enable", "0") == "1"

    async def set_smartrack_enabled(self, enable: bool) -> bool:
        return await self.execute_set(
            "setsmartrackattr", {"-smartrack_enable": "1" if enable else "0"}
        )

    # ── IR LED control (Einstellungen -> Medien -> Bild) ──────────────
    #
    # Note: the `setlightattr -light_enable` field that the "Terminal" page
    # submits is NOT this — toggling it had no observable effect on the
    # camera, so it is deliberately not exposed as an entity.

    async def get_infrared_mode(self) -> str | None:
        """Current IR mode: "auto", "open" (always on) or "close" (always off).

        Returns None if the camera doesn't answer, so the entity shows
        "unknown" rather than a wrong value.
        """
        try:
            data = await self.execute("getinfrared")
        except CtronicsApiError as err:
            _LOGGER.debug("getinfrared failed: %s", err)
            return None
        return data.get("infraredstat")

    async def set_infrared_mode(self, mode: str) -> bool:
        # Confirmed live capture: cmd=setinfrared&-infraredstat=open ("Ein").
        return await self.execute_set("setinfrared", {"-infraredstat": mode})

    async def get_ircut_switch_value(self) -> int | None:
        """IRCut switching time (1-1024).

        The write command is confirmed (``setircutattr -saradc_switch_value``);
        the matching read name is inferred from it, since every other get/set
        pair on this camera is symmetric. If it turns out not to exist we stop
        asking and the entity simply keeps the last value the user set.
        """
        if self._ircut_supported is False:
            return None
        try:
            data = await self.execute("getircutattr")
        except CtronicsApiError as err:
            _LOGGER.debug("getircutattr not supported by this firmware: %s", err)
            self._ircut_supported = False
            return None
        raw = data.get("saradc_switch_value", "")
        if not raw.isdigit():
            self._ircut_supported = False
            return None
        self._ircut_supported = True
        return int(raw)

    async def set_ircut_switch_value(self, value: int) -> bool:
        # Confirmed live capture: cmd=setircutattr&-saradc_switch_value=80
        return await self.execute_set(
            "setircutattr", {"-saradc_switch_value": str(value)}
        )

    # ── RTSP ─────────────────────────────────────────────────────────

    def rtsp_url(self, path: str, port: int) -> str:
        """Build the RTSP URL for one of the camera's streams.

        Credentials are percent-encoded, because a camera password may well
        contain ``@`` or ``:`` and would otherwise break the URL.
        """
        user = quote(self._username, safe="")
        secret = quote(self._password, safe="")
        return f"rtsp://{user}:{secret}@{self._host}:{port}/{path.lstrip('/')}"

    # ── Still-image snapshots ────────────────────────────────────────

    async def get_snapshot(self, fresh: bool = False) -> bytes:
        """Fetch a still JPEG straight from the camera.

        Confirmed live 2026-09-15 against this camera: both ``/tmpfs/auto.jpg``
        and ``/tmpfs/snap.jpg`` return a full 3840x2160 JPEG. This is not a
        CGI call and not the ONVIF/RTSP stream — it is the camera's own
        still-image endpoint, so it works even while nothing is streaming.

        ``fresh=True`` asks the camera to grab a frame now (snap.jpg) and
        falls back to the self-refreshing auto.jpg if a firmware ever drops
        it. The response is checked for a real JPEG header, because this
        camera answers some unknown paths with an HTML error page and
        HTTP 200 rather than a 404.
        """
        paths = (
            (SNAPSHOT_PATH_FRESH, SNAPSHOT_PATH_CACHED)
            if fresh
            else (SNAPSHOT_PATH_CACHED,)
        )
        last_error: Exception | None = None

        for path in paths:
            url = f"http://{self._host}:{self._port}{path}"
            try:
                async with self._session.get(
                    url,
                    auth=self._auth,
                    timeout=self._image_timeout,
                    headers=self._extra_headers,
                ) as resp:
                    if resp.status == 401:
                        raise CtronicsAuthError("HTTP 401 Unauthorized")
                    resp.raise_for_status()
                    data = await resp.read()
            except CtronicsAuthError:
                raise
            except (aiohttp.ClientError, TimeoutError) as err:
                last_error = err
                _LOGGER.debug("Snapshot %s failed: %s", path, err)
                continue

            if not data.startswith(b"\xff\xd8"):
                last_error = CtronicsCommandError(f"{path} did not return a JPEG")
                _LOGGER.debug("Snapshot %s returned %d non-JPEG bytes", path, len(data))
                continue

            return data

        raise CtronicsConnectionError(
            f"No snapshot from {self._host}: {last_error}"
        )

    # ── PTZ presets ──────────────────────────────────────────────────

    async def ptz_command(self, action: str, speed: int = 1) -> None:
        """Send one raw PTZ action.

        Verified against the camera's own web UI source (``js/js.js``)::

            ptzctrl.cgi?-step=0&-act=<action>&-speed=<1-8>

        Valid actions there: up, down, left, right, home, stop, zoomin,
        zoomout, focusin, focusout, hscan, vscan.
        """
        await self._get_raw(
            self._ptz_url, {"-step": "0", "-act": action, "-speed": str(speed)}
        )

    async def ptz_stop(self) -> None:
        """Stop any in-progress PTZ motion."""
        await self.ptz_command("stop")

    async def ptz_step(self, action: str, speed: int, duration_ms: int) -> None:
        """Nudge the camera: start moving, wait, then stop.

        The camera's UI moves on mouse-down and stops on mouse-up, so a
        movement has no natural length of its own. A Home Assistant button
        press has no "hold", so the duration stands in for how long the user
        would have held the mouse down. The stop is sent even if the move
        call fails, so a half-sent command can't leave the camera panning
        forever.
        """
        try:
            await self.ptz_command(action, speed)
            await asyncio.sleep(duration_ms / 1000)
        finally:
            await self.ptz_stop()

    async def ptz_preset_goto(self, number: int) -> bool:
        """Move to a stored PTZ preset.

        Confirmed twice over: first from a live capture, later from the
        camera's own source (``mainpage9.html``)::

            param.cgi?cmd=preset&-act=goto&-status=1&-number=<N>

        Every parameter carries a leading dash, ``-number`` included. Sending
        it as plain ``number`` makes the camera ignore it and fall back to its
        default position — which looks like "every preset goes to the same
        spot". Camera numbering is zero-based: the UI computes
        ``form_preset.value - 1``, so "Voreinstellung 1" is -number=0.
        """
        await self.ptz_stop()
        return await self.execute_set(
            "preset", {"-act": "goto", "-status": "1", "-number": str(number)}
        )

    async def ptz_preset_save(self, number: int) -> bool:
        """Store the current position as a preset.

        From the camera's source: ``-act=set&-status=1``.
        """
        return await self.execute_set(
            "preset", {"-act": "set", "-status": "1", "-number": str(number)}
        )

    async def ptz_preset_delete(self, number: int) -> bool:
        """Clear a stored preset.

        Same command as saving, with ``-status=0`` instead of 1.
        """
        return await self.execute_set(
            "preset", {"-act": "set", "-status": "0", "-number": str(number)}
        )
