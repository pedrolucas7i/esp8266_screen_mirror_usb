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
- `TARGET_FPS` — desired frames per second
- `CHUNK_SIZE` — bytes per serial write
- `SCREEN_SIZE` — width, height expected by the ESP8266

In `screen_mirror_usb.ino` check:

- `JPEG_BUFFER_SIZE` — must be >= maximum JPEG frame size you expect
- `TFT_eSPI` configuration (in `User_Setup.h` or platformio.ini) for the correct display

## Troubleshooting

- If no image appears:
  - Confirm serial port path and that the ESP prints `Serial screen ready!` on boot.
  - Make sure `TFT_eSPI` is configured for your display orientation and pins.
  - Lower `JPEG_QUALITY` or increase `CHUNK_SIZE` if transfers time out.

- If you see `ERR:TOO_LARGE` on the ESP: increase `JPEG_BUFFER_SIZE` in the sketch or reduce JPEG quality / resize to a smaller `SCREEN_SIZE`.

- If you see `ERR:TIMEOUT`: the ESP did not receive all bytes within the timeout. Try increasing the receive timeout loop in the sketch or reducing the frame size/quality or lowering host-side delays between chunks.

- If ffmpeg fails: verify X11 display is accessible and `ffmpeg -f x11grab -video_size 1920x1080 -i :0.0 -frames:v 1 out.png` works from your shell.

## Notes & Next steps

- This project assumes X11. Wayland capture requires different ffmpeg input (or wlroots support).
- Consider adding a simple acknowledgement handshake after `FRAME_DONE` to the host for throttling.
- For higher frame rates and reliability, consider using a faster MCU (ESP32) or a direct USB protocol (e.g., USB CDC + flow control) or compress with MJPEG stream.
