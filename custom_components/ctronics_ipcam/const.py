"""Constants for the Ctronics IP Camera (Hi3510) integration.

Every CGI command / field name in here was captured live from this exact
camera's local web UI via a browser network-request capture (model
C6F0SpZ0N0PpL2, firmware V30.1.60.11.88), NOT copied from a generic Hi3510
datasheet. Where a value is inferred rather than directly observed, it says so.
"""
from __future__ import annotations

DOMAIN = "ctronics_ipcam"
PLATFORMS = ["switch", "number", "button", "select", "camera"]

# ── Config / options keys ───────────────────────────────────────────────
CONF_PRESET_COUNT = "preset_count"
CONF_SNAPSHOT_FOLDER = "snapshot_folder"
CONF_RTSP_PORT = "rtsp_port"
CONF_RTSP_MAIN_PATH = "rtsp_main_path"
CONF_RTSP_SUB_PATH = "rtsp_sub_path"
CONF_PTZ_STEP_MS = "ptz_step_ms"
CONF_HAS_ZOOM_FOCUS = "has_zoom_focus"

DEFAULT_PORT = 80
DEFAULT_PRESET_COUNT = 4
# 64, established by testing on the device: preset 64 works, 65 does not.
#
# An earlier version capped this at 8, taken from a dropdown in the camera's
# web interface. That was wrong: the dropdown belongs to the alarm feature
# ("drive to preset N on alarm"), which really does offer only 0-7. The
# preset field itself is a free text input with maxlength="3" and no
# validation anywhere in the page's JavaScript, and the firmware accepts up
# to 64.
MAX_PRESET_COUNT = 64
DEFAULT_SCAN_INTERVAL = 30  # seconds, for the CGI settings poll

# ── CGI endpoints ────────────────────────────────────────────────────────
# Confirmed: this firmware serves the Hi3510 CGI nested under /web/, unlike
# some other Hi3510-based cameras that use /cgi-bin/ directly.
CGI_PARAM_PATH = "/web/cgi-bin/hi3510/param.cgi"
CGI_PTZCTRL_PATH = "/web/cgi-bin/hi3510/ptzctrl.cgi"

# ── Still-image snapshots ───────────────────────────────────────────────
# Confirmed live 2026-09-15 by opening both URLs in a browser against this
# camera (firmware V30.1.60.11.88): each returns a full 3840x2160 JPEG.
#   auto.jpg — the snapshot the camera refreshes by itself. Cheap to fetch,
#              may be a moment old. Used for the camera entity's polling.
#   snap.jpg — asks the camera to grab a frame now. Used for the save button.
SNAPSHOT_PATH_CACHED = "/tmpfs/auto.jpg"
SNAPSHOT_PATH_FRESH = "/tmpfs/snap.jpg"
# A 4K JPEG is ~0.5-1.5 MB, so it needs a longer timeout than a CGI call.
SNAPSHOT_TIMEOUT = 30
# Minimum seconds between two image fetches for the camera entity. The
# camera is a small embedded device; polling it harder than this gains
# nothing because auto.jpg doesn't refresh faster anyway.
SNAPSHOT_FRAME_INTERVAL = 2.0

# ── RTSP streams ────────────────────────────────────────────────────────
# NOT captured from this camera — these are the paths Ctronics documents for
# its cameras and the ones the Hi3510 family commonly uses. The camera's
# ONVIF service hands Home Assistant its stream URLs directly, so there was
# nothing to read them off. They are therefore exposed as options: if a
# stream stays black, check the real address (e.g. open
# rtsp://<ip>:554/11 in VLC) and correct the path here rather than waiting
# for a new release.
DEFAULT_RTSP_PORT = 554
DEFAULT_RTSP_MAIN_PATH = "11"  # main stream, full resolution
DEFAULT_RTSP_SUB_PATH = "12"  # second stream, lower resolution

# Where the "save snapshot" button writes to. /media is browsable in Home
# Assistant's own Medien panel, so saved images can be viewed and downloaded
# from the UI without any extra configuration.
DEFAULT_SNAPSHOT_FOLDER = "/media/ctronics"
EVENT_SNAPSHOT_SAVED = f"{DOMAIN}_snapshot_saved"

# ── IR LED control ──────────────────────────────────────────────────────
# Confirmed: cmd=setinfrared&-infraredstat=open was sent when picking "Ein"
# in Einstellungen -> Medien -> Bild -> IR-LED-Steuerung.
IR_MODE_AUTO = "auto"
IR_MODE_ON = "open"
IR_MODE_OFF = "close"
IR_MODES = [IR_MODE_AUTO, IR_MODE_ON, IR_MODE_OFF]

# IRCut switching time, captured as -saradc_switch_value=80; the UI labels the
# field 1-1024 ("the larger the value, the longer the switching time").
IRCUT_MIN = 1
IRCUT_MAX = 1024

# ── PTZ ─────────────────────────────────────────────────────────────────
# Read straight out of the camera's own web UI source (js/js.js,
# mainpage9.html), so these are the exact commands the camera itself sends:
#
#   ptzctrl.cgi?-step=0&-act=<action>&-speed=<1-8>
#   param.cgi?cmd=preset&-act=set &-status=1&-number=<0-63>  save
#   param.cgi?cmd=preset&-act=goto&-status=1&-number=<0-63>  recall
#   param.cgi?cmd=preset&-act=set &-status=0&-number=<0-63>  delete
#
# The UI fires the movement on mouse-down and "stop" on mouse-up. A button
# press in Home Assistant has no "hold", so a step action sends the move,
# waits PTZ step duration, then stops.
PTZ_STEP_ACTIONS = (
    "up",
    "down",
    "left",
    "right",
    "zoomin",
    "zoomout",
    "focusin",
    "focusout",
)
# The C6F0SpZ0N0PpL2 has a fixed lens: no optical zoom, no focus motor. Its
# firmware still accepts zoomin/zoomout/focusin/focusout because the Hi3510
# platform is shared across models, but nothing moves. There is no way to
# ask the camera either — getcapability only reports cap_cvbs. So the four
# buttons are off by default and can be switched on for a model that does
# have a varifocal lens.
DEFAULT_HAS_ZOOM_FOCUS = False
# These the camera's UI fires without a following stop: "home" re-centres,
# the two scans keep running until something stops them.
PTZ_INSTANT_ACTIONS = ("home", "hscan", "vscan", "stop")

# The speed dropdown in the camera's UI offers exactly 1-8.
PTZ_SPEED_MIN = 1
PTZ_SPEED_MAX = 8
DEFAULT_PTZ_SPEED = 4

DEFAULT_PTZ_STEP_MS = 400
PTZ_STEP_MS_MIN = 50
PTZ_STEP_MS_MAX = 5000
