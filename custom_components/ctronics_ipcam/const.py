"""Constants for the Ctronics IP Camera (Hi3510) integration.

Every CGI command / field name in here was captured live from this exact
camera's local web UI via a browser network-request capture (model
C6F0SpZ0N0PpL2, firmware V30.1.60.11.88), NOT copied from a generic Hi3510
datasheet. Where a value is inferred rather than directly observed, it says so.
"""
from __future__ import annotations

from datetime import timedelta

DOMAIN = "ctronics_ipcam"
PLATFORMS = [
    "switch",
    "number",
    "button",
    "select",
    "binary_sensor",
    "image",
    "camera",
]

# ── Config / options keys ───────────────────────────────────────────────
CONF_PRESET_COUNT = "preset_count"
CONF_ALARM_FOLDER = "alarm_folder"
CONF_OFF_DELAY = "off_delay"
CONF_ALARM_PREFIX = "alarm_prefix"
CONF_SNAPSHOT_FOLDER = "snapshot_folder"

DEFAULT_PORT = 80
DEFAULT_PRESET_COUNT = 4
# The camera's "Voreinstellung" control is a dropdown 1-8, so 8 is the
# hardware maximum — offering more would just create dead buttons.
MAX_PRESET_COUNT = 8
DEFAULT_SCAN_INTERVAL = 30  # seconds, for the CGI settings poll

# ── Alarm folder watching ───────────────────────────────────────────────
# The camera has no HTTP push and no pollable "person detected" flag. Its
# only real-time signal is that it FTPs a snapshot when its AI detection
# fires, so we watch the folder those snapshots land in.
DEFAULT_OFF_DELAY = 30  # seconds the sensor stays on after the last snapshot

# The camera doesn't upload into the configured folder directly — it creates
# <folder>/<YYYY-MM-DD>/images/ underneath, so the folder is scanned
# recursively.
#
# It also uploads two different kinds of file into the same place, told apart
# by the first letter of the file name (confirmed from the FTP server log):
#   A26091517455710.jpg  -> Alarm, i.e. a real detection
#   P26091517410710.jpg  -> periodic "Auto-Schnappschuss", once a minute
# Only names starting with this prefix count as a detection, and only those
# are ever deleted — anything else in the folder is left alone. Set the
# option to an empty string to treat every image as a detection.
DEFAULT_ALARM_PREFIX = "A"
FOLDER_POLL_INTERVAL = timedelta(seconds=2)
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png")
# Don't delete a file that may still be uploading.
DELETE_GRACE_SECONDS = 5

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
