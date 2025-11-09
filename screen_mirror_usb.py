import serial
import io
import time
import subprocess
from PIL import Image

# ===================== CONFIGURAÇÕES =====================
SERIAL_PORT = "/dev/ttyACM0"   # Porta do ESP8266 (ajuste conforme necessário)
BAUD_RATE = 115200
JPEG_QUALITY = 60
TARGET_FPS = 25
CHUNK_SIZE = 4096
SCREEN_SIZE = (320, 240)       # Resolução para o ESP8266
# =========================================================

def capture_screen_ffmpeg():
    """Captura 1 frame da tela via ffmpeg (funciona em X11, Wayland e SSH)."""
    cmd = [
        "ffmpeg",
        "-f", "x11grab",
        "-video_size", "1920x1080",
        "-i", ":0.0",
        "-frames:v", "1",
        "-f", "image2pipe",
        "-vcodec", "png",
        "-"
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    img_data = proc.stdout.read()
    proc.stdout.close()
    try:
        img = Image.open(io.BytesIO(img_data)).convert("RGB")
        img = img.resize(SCREEN_SIZE, Image.Resampling.BILINEAR)
        return img
    except Exception as e:
        print("Erro ao capturar frame:", e)
        return None

# =========================================================

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
print("Connected to ESP8266 via Serial")

try:
    while True:
        start = time.time()
        img = capture_screen_ffmpeg()
        if img is None:
            time.sleep(1)
            continue

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=JPEG_QUALITY)
        jpeg_data = buf.getvalue()

        # Envia tamanho
        ser.write(f"JPEG_FRAME_SIZE:{len(jpeg_data)}\n".encode())
        time.sleep(0.05)

        # Envia em blocos
        for i in range(0, len(jpeg_data), CHUNK_SIZE):
            ser.write(jpeg_data[i:i+CHUNK_SIZE])
            time.sleep(0.005)

        elapsed = time.time() - start
        time.sleep(max(0, (1/TARGET_FPS) - elapsed))

except KeyboardInterrupt:
    print("\nEncerrando...")
    ser.close()
