#include <TJpg_Decoder.h>
#include <TFT_eSPI.h>
#include <SPI.h>
#include <user_interface.h>

TFT_eSPI tft = TFT_eSPI();

#define JPEG_BUFFER_SIZE (40*1024)  // Adjust according to available RAM
#define CHUNK_TIMEOUT 200           // ms

uint8_t *buffer = NULL;
uint32_t expected_frame_size = 0;

// TJpg_Decoder callback
bool tft_output(int16_t x, int16_t y, uint16_t w, uint16_t h, uint16_t *bitmap) {
  if (y >= tft.height()) return false;
  tft.pushImage(x, y, w, h, bitmap);
  return true;
}

void setup() {
  SPI.setFrequency(60000000);
  Serial.begin(2000000);   // High-speed serial (1.5 Mbps)
  tft.init();
  tft.setRotation(1);
  tft.fillScreen(TFT_BLACK);

  buffer = (uint8_t*)malloc(JPEG_BUFFER_SIZE);
  if (!buffer) {
    Serial.println("ERROR: Failed to allocate buffer!");
    while(1);
  }

  TJpgDec.setJpgScale(1);
  TJpgDec.setSwapBytes(true);
  TJpgDec.setCallback(tft_output);

  tft.setTextColor(TFT_WHITE);
  tft.setCursor(10, 10);
  tft.println("Serial screen ready!");

  system_update_cpu_freq(160);  // 160 MHz CPU
}

// Read frame header like "JPEG_FRAME_SIZE:12345"
bool read_frame_header(uint32_t &size) {
  char line[32];
  if (Serial.readBytesUntil('\n', line, sizeof(line)-1) <= 0) return false;
  line[strcspn(line, "\r\n")] = 0;
  if (strncmp(line, "JPEG_FRAME_SIZE:", 16) == 0) {
    size = atoi(line + 16);
    return true;
  }
  return false;
}

// Receive full frame in chunks
bool receive_frame(uint8_t *buf, uint32_t size, uint32_t timeout_ms = CHUNK_TIMEOUT) {
  uint32_t pos = 0;
  uint32_t start = millis();
  while (pos < size) {
    int avail = Serial.available();
    if (avail > 0) {
      if (avail > size - pos) avail = size - pos;
      Serial.readBytes(buf + pos, avail);
      pos += avail;
      start = millis();  // reset timeout
    }
    if (millis() - start > timeout_ms) return false;
    yield();
  }
  return true;
}

void loop() {
  if (Serial.available()) {
    if (!read_frame_header(expected_frame_size)) return;
    if (expected_frame_size > JPEG_BUFFER_SIZE) {
      Serial.println("ERR:TOO_LARGE");
      return;
    }

    // Receive frame in chunks
    if (!receive_frame(buffer, expected_frame_size)) {
      Serial.println("ERR:TIMEOUT");
      return;
    }

    // Decode and display
    TJpgDec.drawJpg(0, 0, buffer, expected_frame_size);

    // ACK to sender
    Serial.println("FRAME_DONE");
  }
}
