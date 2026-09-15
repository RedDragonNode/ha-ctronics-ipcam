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

DEFAULT_PORT = 80
DEFAULT_PRESET_COUNT = 4
# The camera's "Voreinstellung" control is a dropdown 1-8, so 8 is the
# hardware maximum — offering more would just create dead buttons.
MAX_PRESET_COUNT = 8
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
