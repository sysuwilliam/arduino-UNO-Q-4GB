#include <Arduino_LED_Matrix.h>

constexpr uint8_t MATRIX_ROWS = 8;
constexpr uint8_t MATRIX_COLS = 13;
constexpr uint16_t FRAME_SIZE = MATRIX_ROWS * MATRIX_COLS;

Arduino_LED_Matrix matrix;
uint8_t frame[FRAME_SIZE];

uint16_t pixelIndex(uint8_t row, uint8_t col) {
  return row * MATRIX_COLS + col;
}

void clearFrame() {
  for (uint16_t i = 0; i < FRAME_SIZE; ++i) {
    frame[i] = 0;
  }
}

void drawRectangle(uint8_t top, uint8_t left, uint8_t height, uint8_t width, uint8_t brightness, bool filled) {
  if (height == 0 || width == 0) {
    return;
  }

  uint8_t bottom = top + height - 1;
  uint8_t right = left + width - 1;

  if (bottom >= MATRIX_ROWS || right >= MATRIX_COLS) {
    return;
  }

  for (uint8_t row = top; row <= bottom; ++row) {
    for (uint8_t col = left; col <= right; ++col) {
      bool isBorder = row == top || row == bottom || col == left || col == right;
      if (filled || isBorder) {
        frame[pixelIndex(row, col)] = brightness;
      }
    }
  }
}

void showFrame() {
  matrix.draw(frame);
}

void setup() {
  matrix.begin();
  matrix.setGrayscaleBits(8);

  clearFrame();
  drawRectangle(1, 2, 6, 9, 255, false);
  showFrame();
  delay(1000);
}

void loop() {
  clearFrame();
  drawRectangle(1, 2, 6, 9, 255, false);
  showFrame();
  delay(800);

  clearFrame();
  drawRectangle(2, 3, 4, 7, 255, true);
  showFrame();
  delay(800);

  for (uint8_t inset = 0; inset < 4; ++inset) {
    clearFrame();
    drawRectangle(inset, inset, MATRIX_ROWS - inset * 2, MATRIX_COLS - inset * 2, 255, false);
    showFrame();
    delay(250);
  }
}
