# Ctronics IP Camera for Home Assistant

Home Assistant integration for Ctronics pan/tilt IP cameras that run the
Hi3510 / "Hipcam" firmware — the ones whose local web interface lives at
`http://<camera-ip>/web/admin.html`.

It talks to the camera's **native local HTTP API only**. No cloud, no app, no
account. Everything it does was reverse-engineered by capturing the camera's
own web interface with browser developer tools.

> **Unofficial.** Not affiliated with Ctronics. Developed against a
> **C6F0SpZ0N0PpL2** (4K indoor pan/tilt, firmware `V30.1.60.11.88`). Other
> Hi3510-based models will probably work, but nothing else has been tested.

## Why this exists

Home Assistant's built-in ONVIF integration already gives you the video
stream, PTZ and generic motion detection for these cameras — and you should
keep using it for that. What ONVIF does *not* expose is the camera's own
feature set:

| | ONVIF | This integration |
|---|---|---|
| Video stream, snapshots | ✅ | — (use ONVIF) |
| Generic motion detection | ✅ | — (use ONVIF) |
| AI person detection on/off | ❌ | ✅ |
| Detection threshold | ❌ | ✅ |
| Auto-tracking (Smart Track) | ❌ | ✅ |
| IR LED mode (auto/on/off) | ❌ | ✅ |
| IRCut switching time | ❌ | ✅ |
| PTZ preset buttons | partly | ✅ |

Run both side by side: ONVIF for the picture, this one for the camera's
own settings.

## Entities

| Entity | Type | What it does |
|---|---|---|
| AI person detection | `switch` | The camera's "Intelligente Identifizierung" / smart human-shape detection |
| Auto-tracking | `switch` | Smart Track — camera follows a detected person |
| Detection threshold | `number` (1–100) | Sensitivity of the AI detection |
| IR LED control | `select` | `Auto` / `On` / `Off` for the infrared LEDs |
| IRCut switching time | `number` (1–1024) | How long the IR-cut filter waits before switching |
| Go to preset _n_ | `button` | Drives the camera to a stored PTZ preset |

All labels are translated (English and German included).

## Installation

### HACS (custom repository)

1. HACS → three-dot menu → **Custom repositories**
2. Add this repository's URL, category **Integration**
3. Find "Ctronics IP Camera" in HACS and download it
4. **Restart Home Assistant**
5. Settings → Devices & Services → **Add integration** → "Ctronics IP Camera"

### Manual

Copy `custom_components/ctronics_ipcam/` into your Home Assistant
`config/custom_components/` folder, restart, then add the integration.

## Configuration

You need the camera's IP address and the admin login you use for its web
interface. Give the camera a **static IP / DHCP reservation** — the
integration addresses it by IP.

After setup, the entry's **Configure** dialog lets you choose how many PTZ
preset buttons to create (0–8).

### Presets

The camera stores up to **8** presets and offers no way to ask which of them
are actually in use, so the integration cannot discover them — you pick the
number of buttons yourself and rename them in Home Assistant.

Save the positions on the camera first (its web interface, *Überwachen* tab:
move the camera, pick a preset number, press *Senden*). Preset numbering in
the camera's UI starts at 1; the API counts from 0, and this integration
handles that mapping for you — "Go to preset 1" drives to the camera's
preset 1.

## Known limitations

- **No "person detected" sensor.** The camera can only push an alarm via
  FTP, e-mail or SD card — there is no webhook and nothing to poll. A working
  workaround is to let the camera FTP its alarm snapshots to Home Assistant
  and watch that folder; folding this into the integration is the next
  planned step.
- The IRCut value's *read* command is guessed (`getircutattr`). If your
  firmware doesn't have it, the integration notices, stops asking, and simply
  keeps the last value you set. Writing works either way.
- Image settings (brightness, contrast, flip, …) are understood but not yet
  exposed.

## The camera's local API

Documented here because it is hard to find anywhere else. Base path on this
firmware — note the `/web/` prefix, which some other Hi3510 cameras don't
have:

```
http://<camera-ip>/web/cgi-bin/hi3510/param.cgi?cmd=<command>&-<param>=<value>
http://<camera-ip>/web/cgi-bin/hi3510/ptzctrl.cgi?-step=0&-act=stop&-speed=1
```

HTTP Basic Auth with the camera's admin credentials. Reads answer with
`var key="value";` lines, writes with `[Succeed]` or `[Error]`.

| Purpose | Read | Write |
|---|---|---|
| AI person detection | `getsmdattr` | `setsmdattr&-smd_enable=0\|1` |
| Threshold & extras | `getsmdex` | `setsmdex&-smd_rect=&-smd_gthresh=&-smd_type=` |
| Alarm trigger type | `getmdalarm&-aname=type` | `setmdalarm&-aname=type&-switch=on\|off` |
| Auto-tracking | `getsmartrackattr` | `setsmartrackattr&-smartrack_enable=0\|1` |
| IR LED mode | `getinfrared` | `setinfrared&-infraredstat=auto\|open\|close` |
| IRCut time | `getircutattr` (unverified) | `setircutattr&-saradc_switch_value=<1-1024>` |
| PTZ motor settings | `getmotorattr` | `setmotorattr&-tiltscan=&-tiltspeed=&-panscan=&-panspeed=&-movehome=&-ptzalarmmask=` |
| Image settings | `getimageattr` | `setimageattr&-brightness=&-contrast=&-saturation=&-sharpness=&-mirror=&-flip=&…` |
| Go to preset | — | `preset&-act=goto&-status=1&-number=<0-7>` |

Two things that cost real debugging time:

1. **Every parameter carries a leading dash — `-number` included.** Sending
   `number=2` instead of `-number=2` makes the camera silently ignore it and
   drive to its default position, which looks exactly like "every preset
   button goes to the same place".
2. **Stop the PTZ before recalling a preset.** The camera's own interface
   always fires `ptzctrl.cgi?-step=0&-act=stop&-speed=1` first, so this
   integration does too.

Requests also carry `Cookie: cookmun=1` and a `Referer` header, mirroring
what the camera's own interface sends.

## Credits

The request/response conventions of the Hi3510 CGI family were cross-checked
against [spagonic/ha-hi3510](https://github.com/spagonic/ha-hi3510), an
integration for closely related cameras. Everything specific to this model
was captured from the device itself.

## License

MIT
