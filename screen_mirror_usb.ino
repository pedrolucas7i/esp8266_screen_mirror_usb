#include <TJpg_Decoder.h>
#include <TFT_eSPI.h>
#include <SPI.h>

TFT_eSPI tft = TFT_eSPI();   // Objeto do display

#define JPEG_BUFFER_SIZE (40*1024)
uint8_t *jpeg_buffer = NULL;
uint32_t jpeg_buffer_pos = 0;
uint32_t expected_jpeg_size = 0;

// Callback do TJpg_Decoder
bool tft_output(int16_t x, int16_t y, uint16_t w, uint16_t h, uint16_t *bitmap) {
  if (y >= tft.height()) return false;
  tft.pushImage(x, y, w, h, bitmap);
  return true;
}

void setup() {
  Serial.begin(921600);
  tft.init();
  tft.setRotation(1);
  tft.fillScreen(TFT_BLACK);

  // Aloca buffer JPEG
  jpeg_buffer = (uint8_t *)malloc(JPEG_BUFFER_SIZE);
  if (jpeg_buffer == NULL) {
    Serial.println("Error: Failed to allocate buffer!");
    while (1);
  }

  TJpgDec.setJpgScale(1);
  TJpgDec.setSwapBytes(true);
  TJpgDec.setCallback(tft_output);

  tft.setTextColor(TFT_WHITE);
  tft.setCursor(10, 10);
  tft.println("Serial screen ready!");
}

void loop() {
  // Verifica se recebemos a linha com tamanho JPEG
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.startsWith("JPEG_FRAME_SIZE:")) {
      expected_jpeg_size = line.substring(16).toInt();
      jpeg_buffer_pos = 0;

      if (expected_jpeg_size > JPEG_BUFFER_SIZE) {
        Serial.println("ERR:TOO_LARGE");
        expected_jpeg_size = 0;
        return;
      }

      // Aguarda todos os bytes do JPEG
      uint32_t start = millis();
      while (jpeg_buffer_pos < expected_jpeg_size && millis() - start < 3000) {
        while (Serial.available() && jpeg_buffer_pos < expected_jpeg_size) {
          jpeg_buffer[jpeg_buffer_pos++] = Serial.read();
        }
        yield(); // permite outras tarefas
      }

      if (jpeg_buffer_pos == expected_jpeg_size) {
        TJpgDec.drawJpg(0, 0, jpeg_buffer, expected_jpeg_size);
        Serial.println("FRAME_DONE");
      } else {
        Serial.println("ERR:TIMEOUT");
      }
    }
  }
}
