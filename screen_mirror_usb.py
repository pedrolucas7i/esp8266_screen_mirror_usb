import serial
import serial.tools.list_ports
import io
import time
from PIL import Image
import mss

try:
    from turbojpeg import TurboJPEG
    jpeg_encoder = TurboJPEG()
except Exception:
    jpeg_encoder = None

# ===================== CONFIGURATION =====================
BAUD_RATE = 2000000            # Must match the ESP8266 code
JPEG_QUALITY = 50              # 30–80 recommended for smooth transmission
TARGET_FPS = 20                # ESP8266 can usually handle 10–20 FPS
CHUNK_SIZE = 2048              # Size of serial transmission chunks
SCREEN_SIZE = (320, 240)       # Output resolution for the TFT display
MONITOR_NUMBER = 1             # Usually 1 = main monitor
# ==========================================================


def find_esp8266_port():
    """Scan available serial ports and return the one that looks like an ESP8266."""
    while True:
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            desc = (p.description or "").lower()
            hwid = (p.hwid or "").lower()
            if "esp" in desc or "ch340" in desc or "cp210" in desc or "usb serial" in desc or "ttyacm" in p.device.lower():
                print(f"[DETECT] Found possible ESP8266 on {p.device} ({p.description})")
                return p.device
        print("[WAIT] No ESP8266 detected. Please connect via USB...")
        time.sleep(2)


def capture_and_encode():
    """Capture the screen and return resized JPEG bytes."""
    with mss.mss() as sct:
        monitor = sct.monitors[MONITOR_NUMBER]
        sct_img = sct.grab(monitor)
        rgb_bytes = bytes(sct_img.rgb)

    # Convert raw bytes to Pillow Image and resize
    img = Image.frombuffer("RGB", sct_img.size, rgb_bytes, "raw", "RGB")
    img = img.resize(SCREEN_SIZE, Image.Resampling.BILINEAR)

    # Encode using TurboJPEG if available, otherwise Pillow
    if jpeg_encoder:
        arr = img.tobytes()
        jpeg_data = jpeg_encoder.encode(arr, quality=JPEG_QUALITY,
                                        pixel_format=0,
                                        width=SCREEN_SIZE[0],
                                        height=SCREEN_SIZE[1])
    else:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=JPEG_QUALITY)
        jpeg_data = buf.getvalue()

    return jpeg_data


def send_frame(ser, jpeg_data):
    """Send one JPEG frame to the ESP8266 via serial in safe chunks."""
    frame_size = len(jpeg_data)
    ser.reset_output_buffer()
    ser.write(f"JPEG_FRAME_SIZE:{frame_size}\n".encode())
    ser.flush()
    time.sleep(0.02)  # short delay to let the ESP8266 parse header

    # Send data in small chunks to avoid buffer overflow
    for i in range(0, frame_size, CHUNK_SIZE):
        ser.write(jpeg_data[i:i + CHUNK_SIZE])
        ser.flush()
        time.sleep(0.002)

    # Wait for ESP8266 acknowledgment (FRAME_DONE)
    start_wait = time.time()
    ack = b""
    while time.time() - start_wait < 2:
        if ser.in_waiting:
            ack += ser.readline()
            if b"FRAME_DONE" in ack:
                break

    return b"FRAME_DONE" in ack


def start_streaming(port_name):
    """Main streaming loop once the serial port is connected."""
    try:
        ser = serial.Serial(port_name, BAUD_RATE, timeout=1)
        time.sleep(2.0)  # Give ESP8266 time to boot
        print(f"[OK] Connected to {port_name} at {BAUD_RATE} baud.")

        frame_count = 0
        while True:
            start = time.time()

            jpeg_data = capture_and_encode()
            ok = send_frame(ser, jpeg_data)

            frame_count += 1
            elapsed = time.time() - start
            fps = 1.0 / elapsed if elapsed > 0 else 0
            status = "OK" if ok else "NO ACK"

            print(f"[FRAME {frame_count}] {len(jpeg_data)} bytes | {fps:.1f} FPS | {status}")

            # Maintain stable frame rate
            time.sleep(max(0, (1 / TARGET_FPS) - elapsed))

    except serial.SerialException:
        print("[ERROR] Serial connection lost. Reconnecting...")
        return False
    except KeyboardInterrupt:
        print("\n[STOP] User interrupted transmission.")
        ser.close()
        print("[CLOSED] Serial port closed.")
        raise SystemExit
    return True


def main():
    print("[INIT] Waiting for ESP8266 connection...")
    while True:
        port = find_esp8266_port()
        success = start_streaming(port)
        if not success:
            print("[RETRY] Reconnecting after 2 seconds...")
            time.sleep(2)


if __name__ == "__main__":
    main()
