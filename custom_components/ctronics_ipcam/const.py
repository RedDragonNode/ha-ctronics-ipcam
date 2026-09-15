"""Constants for the Ctronics IP Camera (Hi3510) integration.

Every CGI command / field name in here was captured live from this exact
camera's local web UI via a browser network-request capture (model
C6F0SpZ0N0PpL2, firmware V30.1.60.11.88), NOT copied from a generic Hi3510
datasheet. Where a value is inferred rather than directly observed, it says so.
"""
from __future__ import annotations

DOMAIN = "ctronics_ipcam"
PLATFORMS = ["switch", "number", "button", "select"]

# ── Config / options keys ───────────────────────────────────────────────
CONF_PRESET_COUNT = "preset_count"

DEFAULT_PORT = 80
DEFAULT_PRESET_COUNT = 4
# The camera's "Voreinstellung" control is a dropdown 1-8, so 8 is the
# hardware maximum — offering more would just create dead buttons.
MAX_PRESET_COUNT = 8
DEFAULT_SCAN_INTERVAL = 30  # seconds

# ── CGI endpoints ────────────────────────────────────────────────────────
# Confirmed: this firmware serves the Hi3510 CGI nested under /web/, unlike
# some other Hi3510-based cameras that use /cgi-bin/ directly.
CGI_PARAM_PATH = "/web/cgi-bin/hi3510/param.cgi"
CGI_PTZCTRL_PATH = "/web/cgi-bin/hi3510/ptzctrl.cgi"

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
