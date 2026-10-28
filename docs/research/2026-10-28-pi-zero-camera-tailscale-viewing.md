# Pi Zero 2 W camera viewing over Tailscale

**Date:** 2026-10-28

## Question

What ready-made interfaces can provide simple, remote live video for the
scratch-built pen plotter? The proposed camera node is a Raspberry Pi Zero 2 W
with a Raspberry Pi Camera Module 3 Wide (120-degree class) reachable over
Tailscale, without adding a Klipper-style printer controller.

## Conclusion

Tailscale provides the private network; it does not provide a camera page.
Install one media server on the Pi and open that server through the camera
Pi's tailnet address or MagicDNS name.

The best fit for "type one address and watch in a browser" is **go2rtc**:

```text
http://<camera-pi-tailscale-ip>:1984/stream.html?src=plotter
```

The Raspberry Pi camera documentation supplies a tested go2rtc configuration
that runs `rpicam-vid`, has a browser UI, and can emit WebRTC, RTSP, HLS, and
other formats. It avoids bundling its own libcamera implementation, so it uses
the Raspberry Pi OS camera stack installed on the Pi.

**MediaMTX** is the strongest alternative. It has native Raspberry Pi camera
support and a browser URL of the form
`http://<camera-pi-tailscale-ip>:8889/plotter`; it also publishes an RTSP URL
for VLC, Home Assistant, or other players.

**muStreamer** is attractive when only MJPEG plus snapshots are needed. Its
built-in HTTP interface is lightweight and very simple to consume, but Camera
Module 3 requires it to run through `libcamerify`, and MJPEG uses more network
bandwidth than H.264.

The lowest-dependency option is Raspberry Pi's own `rpicam-vid` TCP stream.
It is reliable and easy to start, but it has no browser interface: open the
TCP URL with VLC or `ffplay`.

Do not install Klipper, Mainsail, Fluidd, or Moonraker just to get a camera.
Those systems need a printer-control stack that this plotter does not have.
Their camera panes also ultimately consume a webcam stream from a media
server. For a viewing-only plotter camera, install the media server directly.

## Option comparison

| Option | Browser page | Usable protocols | Relative setup cost | Best use |
|---|---|---|---|---|
| go2rtc | Yes, port 1984 | WebRTC, MSE/MP4, HLS, RTSP, MJPEG | Low: one binary plus YAML | Default choice for phone and desktop viewing |
| MediaMTX | Yes, port 8889 for WebRTC and 8888 for HLS | WebRTC, HLS, RTSP | Low: one binary; native Pi camera source | Simple standalone server or several clients |
| muStreamer | Yes, port 8080 | MJPEG and snapshots | Medium: build/install and use `libcamerify` for Camera Module 3 | Snapshot-friendly or maximum browser compatibility |
| `rpicam-vid` TCP | No built-in page | MPEG-TS/H.264 over TCP | Lowest: Raspberry Pi camera package only | VLC-only local or tailnet viewing |

The Raspberry Pi project documents MediaMTX, MistServer, and go2rtc as
third-party servers confirmed to work with its camera system. It gives working
installation and browser examples for MediaMTX and go2rtc.

## Recommended stack

Use Raspberry Pi OS Lite without a desktop. The desktop is unnecessary and
competes with the Pi Zero 2 W for memory and CPU.

### go2rtc

The Raspberry Pi documentation's stream configuration can be reduced to:

```yaml
streams:
  plotter:
    - exec:rpicam-vid -n -t 0 --width 1280 --height 720 --framerate 10 --codec libav --libav-format mpegts --low-latency -o -
```

Start go2rtc, then open:

```text
http://<camera-pi-tailscale-ip>:1984/stream.html?src=plotter
```

This receives a 720p, 10 fps H.264 stream. Ten frames per second is sufficient
for observing pen contact, paper motion, and gross faults while reducing Wi-Fi,
encoder, and Tailscale bandwidth compared with 1080p30. Increase to 15 fps or
1080p only after measuring the actual installation.

Relevant endpoints are available from the same process:

| Purpose | Address |
|---|---|
| Browser UI | `http://<camera-ip>:1984/` |
| Plotter stream page | `http://<camera-ip>:1984/stream.html?src=plotter` |
| RTSP for VLC/player | `rtsp://<camera-ip>:8554/plotter` |

go2rtc describes itself as a zero-dependency application, automatically
selects a browser-supported format, and can output RTSP and WebRTC. Its API
also permits `exec` sources, so the UI should remain restricted to the tailnet.

### MediaMTX

The native Raspberry Pi camera path is:

```yaml
paths:
  plotter:
    source: rpiCamera
    sourceOnDemand: yes
    rpiCameraWidth: 1280
    rpiCameraHeight: 720
    rpiCameraFPS: 10
```

Start MediaMTX, then open:

```text
http://<camera-pi-tailscale-ip>:8889/plotter
```

RTSP is available at `rtsp://<camera-pi-tailscale-ip>:8554/plotter`. MediaMTX
natively supports Raspberry Pi cameras on Bookworm and Trixie for both 32-bit
and 64-bit Raspberry Pi OS.

### Raspberry Pi camera tools without a media page

For a VLC-only test, the authoritative Raspberry Pi TCP example is:

```bash
rpicam-vid -t 0 -n --codec libav --libav-format mpegts \
  -o "tcp://0.0.0.0:5000?listen=1"
```

Open `tcp://<camera-pi-tailscale-ip>:5000` in VLC. This is a useful first test
of camera, focus, lighting, and Tailscale connectivity before adding a media
server, but it is not the final phone-friendly interface.

### muStreamer

muStreamer exposes a built-in HTTP page and MJPEG stream, normally on port 8080.
For Camera Module 3, its own documentation requires a V4L2 compatibility layer:

```bash
sudo modprobe bcm2835-v4l2
libcamerify ./ustreamer --host :: --encoder=m2m-image
```

Use this only if MJPEG and still-image snapshots matter more than bandwidth.
Install and verify the current Raspberry Pi OS dependencies rather than copying
an old mjpg-streamer recipe; Camera Module 3 uses libcamera, not the legacy
MMAL camera stack.

## Tailscale access

On the camera Pi, install and authenticate Tailscale, then find its address:

```bash
tailscale ip -4
```

That returns the `100.x.y.z` address used by the example URLs. MagicDNS can
replace the address with the Pi's hostname if it is enabled.

No router port-forward is required. The service is reachable by devices allowed
by the tailnet and Tailscale ACLs. Do not enable Tailscale Funnel for a camera
feed unless public internet access is intentionally required; Serve is the
tailnet-only option.

For an HTTPS MagicDNS URL instead of `http://100.x...`, first prove the stream
works directly by tailnet IP, then run this on the Pi:

```bash
tailscale serve --bg <local-media-server-port>
```

Tailscale Serve proxies a service only within the tailnet and automatically
provisions TLS. Verify WebRTC playback through the proxy; if UDP negotiation is
awkward, use the server's HLS page or fall back to direct tailnet access.

## Camera and mounting notes

The Camera Module 3 Wide specification lists a 102-degree horizontal and
67-degree vertical field of view and a focus range of approximately 5 cm to
infinity. That is enough to cover a large plotting bed, but the useful frame
edge is narrower than the headline 120-degree diagonal figure. Place it above
or above-front of the bed rather than using an extreme side angle; wide-angle
foreshortening makes line and contact judgement harder toward the corners.

Verify the physical ribbon before enclosure work: a Pi Zero uses a narrower
camera-board connector than a full-size Raspberry Pi, so use the appropriate
Pi Zero camera cable rather than assuming the Camera Module 3 ribbon fits the
board directly.

Use diffuse lighting. A camera whose auto-exposure is fighting a moving gantry
shadow or glossy paper can make a healthy plot look like a contact fault.

## Security and reliability boundaries

- Keep the camera node independent of grblHAL, the RP23CNC, and the toolhead
  controller. Viewing must never participate in motion or force-control timing.
- Restrict the camera Pi to tailnet access. go2rtc and muStreamer are
  unauthenticated by default, and go2rtc's exec-capable API is especially
  powerful if exposed beyond trusted devices.
- Avoid Tailscale Funnel unless public access is deliberate.
- Start with one viewer, 1280x720, and 10 fps. Check for dropped frames,
  sustained high CPU, throttling, and camera disconnects before increasing
  resolution or frame rate.
- Run `tailscale status` while viewing. A `direct` path is preferable to a
  `relay` path for latency and available bandwidth.

This research did not install or benchmark the camera on the actual plotter.
The Pi Zero 2 W, Camera Module 3 Wide, and Tailscale combination remains to be
verified at the final mounting distance, lighting, power supply, and remote
viewing location.

## Primary sources

- Raspberry Pi camera streaming guide, including TCP, RTSP, MediaMTX, and
  go2rtc recipes:
  <https://www.raspberrypi.com/documentation/computers/camera_software.html#streaming-video-over-a-network>
  and its source
  <https://github.com/raspberrypi/documentation/blob/master/documentation/asciidoc/accessories/camera/streaming.adoc>.
- Raspberry Pi Camera Module 3 and hardware specifications:
  <https://www.raspberrypi.com/documentation/computers/camera.html#camera-module-3>
  and
  <https://www.raspberrypi.com/documentation/computers/camera.html#hardware-specification>.
- MediaMTX Raspberry Pi camera support:
  <https://github.com/bluenviron/mediamtx/blob/main/docs/4-static-sources/9-raspberry-pi-cameras.md>.
- MediaMTX browser endpoints:
  <https://github.com/bluenviron/mediamtx/blob/main/docs/5-read/07-web-browsers.md>.
- go2rtc features, ports, outputs, and security warning:
  <https://github.com/AlexxIT/go2rtc>.
- muStreamer HTTP, MJPEG, Camera Module 3, and `libcamerify` behavior:
  <https://github.com/pikvm/ustreamer>.
- Tailscale `serve` behavior and tailnet-only scope:
  <https://tailscale.com/docs/reference/tailscale-cli/serve>.
- Tailscale IPv4 address command and MagicDNS usage:
  <https://tailscale.com/docs/reference/tailscale-cli>.
