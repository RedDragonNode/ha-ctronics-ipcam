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
| Live video stream | ✅ | ✅ (same streams, on one device) |
| Generic motion detection | ✅ | — (use ONVIF) |
| AI person detection on/off | ❌ | ✅ |
| Detection threshold | ❌ | ✅ |
| Auto-tracking (Smart Track) | ❌ | ✅ |
| IR LED mode (auto/on/off) | ❌ | ✅ |
| IRCut switching time | ❌ | ✅ |
| PTZ preset buttons | partly | ✅ |
| PTZ move / scan | partly | ✅ |
| Save and delete presets | ❌ | ✅ |
| Full-resolution still snapshot | partly | ✅ |

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
| Move up/down/left/right | `button` | Nudges the camera; see *PTZ* below |
| Zoom in/out, Focus ± | `button` | Only with a varifocal lens — off by default |
| Centre position | `button` | Sends the camera home |
| Scan left/right, up/down | `button` | Starts a patrol sweep — runs until stopped |
| Stop | `button` | Halts any movement or sweep |
| PTZ speed | `number` (1–8) | Speed used for every movement |
| Preset number | `number` (1–64) | Which slot save/delete act on |
| Save preset / Delete preset | `button` | Stores or clears that slot |
| Main stream | `camera` | The camera's full-resolution RTSP stream |
| Second stream | `camera` | The lower-resolution RTSP stream |
| Snapshot | `camera` | Full-resolution still straight from the camera, no stream needed |
| Save snapshot | `button` | Grabs a fresh still and writes it to disk |

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

After setup, the entry's **Configure** dialog holds the rest: how many PTZ
preset buttons to create (0–8), where the *Save snapshot* button writes to, and the RTSP port and stream
paths.

### PTZ

The camera has no concept of "move one step". It starts moving when the
button in its own interface goes down and stops when it comes back up. A
Home Assistant button has no hold, so a direction press sends the movement,
waits **PTZ step duration** (default 400 ms, in the options), then sends
stop. Shorten it for finer aim, lengthen it to cover ground faster. The
stop is sent even if the movement call fails, so a half-sent command cannot
leave the camera panning forever.

*Scan left/right* and *up/down* start a patrol sweep that keeps going — use
*Stop* to end it.

**Zoom and focus are off by default.** The C6F0SpZ0N0PpL2 has a fixed lens:
its firmware accepts `zoomin` / `zoomout` / `focusin` / `focusout` because
the Hi3510 platform is shared across models, but nothing moves. The camera
cannot be asked which kind of lens it has either — `getcapability` only
reports `cap_cvbs`. If your model has a varifocal lens, switch on **Lens has
zoom and focus** in the options to get the four buttons.

Focus + and − map to `focusin` / `focusout`. The camera's own web interface
has these two wired to the opposite buttons, so if the direction feels
inverted, that is why.

### Presets

The camera stores up to **64** presets — tested on the device: 64 works, 65
does not. It offers no way to ask which of them are in use, so the
integration cannot discover them; you pick how many recall buttons to create
in the options and rename them in Home Assistant. Saving and deleting reach
all 64 regardless, through the **Preset number** entity.

(The camera's own web interface shows a 1-8 dropdown, but that one belongs to
the alarm feature — "drive to preset N on alarm" — which really is limited to
8. The preset field itself has no limit in the page at all.)

Positions can be stored from Home Assistant: aim the camera, set **Preset
number** to the slot you want, then press **Save preset**. **Delete preset**
clears that slot. Preset numbering in the camera's UI starts at 1 while the
API counts from 0; the integration handles that mapping, so "Preset number 1"
is the camera's preset 1.

### Streams

The two RTSP streams are also exposed by Home Assistant's ONVIF integration.
Having them here too means the whole camera — streams, snapshot, presets and
settings — sits on one device instead of two. Pick whichever you prefer;
running both costs the camera two connections only while something is
actually watching.

The stream addresses are **not** read from the camera: ONVIF hands Home
Assistant its URLs directly, so there was nothing to read them off, and the
defaults below are the ones Ctronics documents.

```
rtsp://<user>:<pass>@<camera-ip>:554/11   # main stream
rtsp://<user>:<pass>@<camera-ip>:554/12   # second stream
```

If a stream stays black, check the real address (open it in VLC) and correct
the port/path in the entry's **Configure** dialog — no new release needed.
Both stream entities use the HTTP still below as their preview image, which
is sharper and cheaper than decoding an RTSP keyframe.

### Snapshots

Besides the RTSP stream, the camera serves a still image of the full 3840x2160
sensor frame over plain HTTP — no stream has to be running, so it costs the
camera far less than pulling a frame out of RTSP:

```
http://<camera-ip>/tmpfs/auto.jpg   # refreshed by the camera itself
http://<camera-ip>/tmpfs/snap.jpg   # grabs a frame now
```

The `camera` entity polls `auto.jpg` (at most every 2 s), the *Save snapshot*
button asks for a fresh `snap.jpg` and falls back to `auto.jpg` if a firmware
lacks it. Saved files are named `<entry>_<YYYY-MM-DD>_<HH-MM-SS>.jpg` and go
to `/media/ctronics` by default, which Home Assistant's own **Media** panel
browses — so they can be viewed and downloaded from the UI with no
`allowlist_external_dirs` entry. Every save also fires a
`ctronics_ipcam_snapshot_saved` event carrying the path, to hook automations
onto.

## Known limitations

- The IRCut value's *read* command is guessed (`getircutattr`). If your
  firmware doesn't have it, the integration notices, stops asking, and simply
  keeps the last value you set. Writing works either way.
- Image settings (brightness, contrast, flip, …) are understood but not yet
  exposed.
- **No "person detected" sensor.** The camera offers no webhook and nothing
  pollable that reports a detection; its only signal is the snapshot it
  pushes over FTP/e-mail/SD. An earlier version watched that FTP folder, but
  it was dropped because the ONVIF integration's own motion sensor covers the
  same events. Use `binary_sensor.<camera>_cell_motion_detection` from ONVIF
  — note it pulses for about a second per event, so use it as an automation
  *trigger*, not as a condition.
- Video, OSD, audio, alarm and system settings are documented in
  [`API.md`](API.md) but not exposed as entities yet.

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
| Go to preset | — | `preset&-act=goto&-status=1&-number=<0-63>` |
| PTZ move | — | `ptzctrl.cgi?-step=0&-act=<action>&-speed=<1-8>` |
| Save preset | — | `preset&-act=set&-status=1&-number=<0-63>` |
| Delete preset | — | `preset&-act=set&-status=0&-number=<0-63>` |

`-act` accepts `up`, `down`, `left`, `right`, `home`, `stop`, `zoomin`,
`zoomout`, `focusin`, `focusout`, `hscan`, `vscan`.

Outside the CGI, two plain HTTP still-image endpoints (both full 3840x2160):

| Purpose | URL |
|---|---|
| Self-refreshing still | `/tmpfs/auto.jpg` |
| Capture a frame now | `/tmpfs/snap.jpg` |

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

## Where this came from

The commands were first reverse-engineered by capturing the camera's own web
interface in a browser, then **verified against that interface's source code**,
which the camera serves from `/web/`. [`API.md`](API.md) is the full
inventory extracted from it: every read and write command of every settings
page, with its parameters.

## Credits

The request/response conventions of the Hi3510 CGI family were cross-checked
against [spagonic/ha-hi3510](https://github.com/spagonic/ha-hi3510), an
integration for closely related cameras. Everything specific to this model
was captured from the device itself.

## License

MIT
