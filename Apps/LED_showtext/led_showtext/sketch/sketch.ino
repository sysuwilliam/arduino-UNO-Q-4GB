#include <ArduinoGraphics.h>
#include <Arduino_LED_Matrix.h>
#include <Arduino_RouterBridge.h>

// Board-side display object for the 8x13 LED matrix.
Arduino_LED_Matrix matrix;

// Current message to scroll. It starts empty and will be set by Python
// after reading python/led_text.txt.
String currentText = "";

// Draw one full scrolling-text animation using the current string.
// ArduinoGraphics provides the text API, while Arduino_LED_Matrix provides
// the actual hardware driver for the UNO Q LED matrix.
void renderScrollingText(const String& text) {
  matrix.beginDraw();
  matrix.background(0x000000);
  matrix.clear();

  // Font_5x7 is a practical choice for the 8x13 LED matrix.
  matrix.stroke(0xFFFFFF);
  matrix.textFont(Font_5x7);
  matrix.textScrollSpeed(70);
  matrix.beginText(0, 1, 0xFFFFFF);
  matrix.print(text);
  matrix.endText(SCROLL_LEFT);
  matrix.endDraw();
}

// RouterBridge RPC entrypoint exposed to the Python side.
// Python calls Bridge.call("set_text", text), then the sketch stores the
// value and immediately redraws the matrix with the new message.
bool setText(String text) {
  if (text.length() == 0) {
    return false;
  }

  currentText = text;
  renderScrollingText(currentText);
  return true;
}

void setup() {
  // Initialize the LED matrix hardware and the Bridge transport.
  matrix.begin();
  Bridge.begin();

  // Register the RPC method in the main-loop-safe context because it updates
  // display state and redraws hardware-facing content.
  Bridge.provide_safe("set_text", setText);

  // Clear the matrix at boot. The actual message will be pushed by Python
  // after it reads python/led_text.txt.
  matrix.beginDraw();
  matrix.background(0x000000);
  matrix.clear();
  matrix.endDraw();
}

void loop() {
  // Keep replaying the current scrolling animation so the message loops
  // continuously instead of scrolling only once.
  if (currentText.length() > 0) {
    renderScrollingText(currentText);
  }
}
