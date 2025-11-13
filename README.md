# ESP8266 USB Screen Mirror

Small project to stream screenshots from a Linux (X11) desktop to an ESP8266-driven TFT via a USB serial connection.

This repository contains two files:

- `screen_mirror_usb.py` — Python script that captures the desktop using ffmpeg, resizes and encodes frames as JPEG, and streams them over a serial port.
- `screen_mirror_usb.ino` — Arduino/ESP sketch that receives JPEG frames over Serial and displays them on a TFT using TJpg_Decoder and TFT_eSPI.

## Features

- Capture a single frame from an X11 desktop and send it to an ESP8266 over USB serial.
- JPEG encoding with adjustable quality and target FPS.
- Simple handshaking using a `JPEG_FRAME_SIZE:<bytes>` header and `FRAME_DONE` acknowledgements.

## Requirements

On the host (Linux/X11):

- Python 3.7+ (3.10/3.11 recommended)
- ffmpeg (must support x11grab)
- pip packages: Pillow, pyserial

On the ESP8266:

- Arduino core for ESP8266
- Libraries: `TJpg_Decoder`, `TFT_eSPI`
- A compatible SPI TFT display wired and configured in `User_Setup.h` (or in `TFT_eSPI` configuration)
- Sufficient flash & RAM to allocate a JPEG buffer (the sketch uses a 40KB buffer)

## Installation (host)

1. Install system dependencies:

```sh
# Debian/Ubuntu example
sudo apt update
sudo apt install -y ffmpeg python3 python3-pip
```

2. Install Python packages:

```sh
python3 -m pip install --user pillow pyserial
```

3. Connect the ESP8266 by USB and find the serial port (example):

```sh
# list devices
ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null || true
```

Update `SERIAL_PORT` in `screen_mirror_usb.py` if needed (default: `/dev/ttyACM0`).

4. Ensure you have permission to access the serial device. Add your user to the `dialout` group on many distributions:

```sh
sudo usermod -a -G dialout $USER
# then log out/in
```

## Usage

1. Flash the `screen_mirror_usb.ino` sketch to your ESP8266 with the proper `TFT_eSPI` configuration (pinout/driver) for your display.

2. On the host machine run the Python script:

```sh
python3 screen_mirror_usb.py
```

The script captures the screen with ffmpeg, resizes to 320x240 (configurable), encodes as JPEG and sends it over serial in chunks.

## Configuration

Edit top-of-file constants in `screen_mirror_usb.py`:

- `SERIAL_PORT` — serial device path
- `BAUD_RATE` — 115200 by default
- `JPEG_QUALITY` — JPEG quality (0-100)
# ESP8266 USB Screen Mirror

Small project to stream screenshots from a Linux (X11) desktop to an ESP8266-driven TFT via a USB serial connection.

This repository contains two files:

- `screen_mirror_usb.py` — Python script that captures the desktop (uses `mss` for monitor capture), resizes and encodes frames as JPEG (optional TurboJPEG for faster encoding), and streams them over a serial port.
- `screen_mirror_usb.ino` — Arduino/ESP sketch that receives JPEG frames over Serial and displays them on a TFT using `TJpg_Decoder` and `TFT_eSPI`.

## Features

- Capture continuous screenshots from an X11 desktop and send them to an ESP8266 over USB serial.
- JPEG encoding with adjustable quality and target FPS.
- Simple handshaking using a `JPEG_FRAME_SIZE:<bytes>` header and `FRAME_DONE` acknowledgements.

## Requirements

On the host (Linux/X11):

- Python 3.7+ (3.10/3.11 recommended)
- pip packages: `Pillow`, `pyserial`, `mss`
- Optional: `libturbojpeg` and the `turbojpeg` Python package for faster JPEG encoding

On the ESP8266:

- Arduino core for ESP8266
- Libraries: `TJpg_Decoder`, `TFT_eSPI`
- Sufficient flash & RAM to allocate a JPEG buffer (the sketch uses a 40KB buffer)

## Installation (host)

1. Install system dependencies (Debian/Ubuntu example):

```sh
sudo apt update
sudo apt install -y python3 python3-pip
# Optional (for libturbojpeg backend):
sudo apt install -y libturbojpeg0-dev
```

2. Install Python packages:

```sh
python3 -m pip install --user pillow pyserial mss
# Optional: faster encoding with TurboJPEG
python3 -m pip install --user turbojpeg
```

3. Connect the ESP8266 by USB and find the serial port (example):

```sh
# list typical serial devices
ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null || true
```

The Python script will automatically scan for likely ESP devices but you can also pass a device path as an argument (see Usage). Ensure your user has permission to access the serial device. On many distros adding your user to the `dialout` group helps:

```sh
sudo usermod -a -G dialout $USER
# then log out/in
```

## Usage

1. Flash the `screen_mirror_usb.ino` sketch to your ESP8266 with the proper `TFT_eSPI` configuration (pinout/driver) for your display.

2. On the host machine run the Python script:

```sh
python3 screen_mirror_usb.py
```

By default the script will scan connected serial devices and connect to a port that looks like an ESP/USB-serial adapter. Configuration constants are at the top of `screen_mirror_usb.py` (baud rate, JPEG quality, target FPS, screen size and monitor number).

You can change behavior by editing the constants in the Python file, for example to force a specific serial port edit the `start_streaming()` call or add a small wrapper argument if you prefer.

## Configuration

Edit top-of-file constants in `screen_mirror_usb.py` if you want to change behavior:

- `BAUD_RATE` — must match the ESP side (default: 2000000 in this repo)
- `JPEG_QUALITY` — JPEG quality (0-100)
- `TARGET_FPS` — desired frames per second
- `CHUNK_SIZE` — bytes per serial write
- `SCREEN_SIZE` — width, height expected by the ESP8266 (default: 320x240)
- `MONITOR_NUMBER` — which monitor index to capture from (1 = primary)

In `screen_mirror_usb.ino` check:

- `JPEG_BUFFER_SIZE` — must be >= maximum JPEG frame size you expect
- `TFT_eSPI` configuration (in `User_Setup.h` or platformio.ini) for the correct display

## Troubleshooting

- If no image appears:
  - Confirm serial port path and that the ESP prints `Serial screen ready!` on boot.
  - Make sure `TFT_eSPI` is configured for your display orientation and pins.
  - Lower `JPEG_QUALITY` or reduce `SCREEN_SIZE` if transfers time out or the ESP runs out of memory.
  - If you installed `turbojpeg` but see errors, either uninstall it or ensure `libturbojpeg` is installed on your system.

- If you see `ERR:TOO_LARGE` on the ESP: increase `JPEG_BUFFER_SIZE` in the sketch or reduce JPEG quality / resize to a smaller `SCREEN_SIZE`.

- If you see `ERR:TIMEOUT`: the ESP did not receive all bytes within the timeout. Try increasing the receive timeout loop in the sketch or reducing the frame size/quality or lowering host-side delays between chunks.

- If X11 capture fails: verify the `mss` library can access your display (X11) and try a simple capture test using a tiny Python snippet:

```python
from mss import mss
with mss() as sct:
    print(sct.monitors)
```

## Notes & Next steps

- This project assumes X11. Wayland capture requires different capture methods (or compositor support).
- Consider adding a simple acknowledgement handshake after `FRAME_DONE` to the host for throttling.
- For higher frame rates and reliability, consider using a faster MCU (ESP32) or a direct USB protocol (e.g., USB CDC + flow control) or compress with an MJPEG stream.