import time
from pathlib import Path

from arduino.app_utils import App, Bridge

# Text source file inside the App Lab container.
# Updating this file is the user-facing way to change the text on the LED matrix.
TEXT_FILE = Path("/app/python/led_text.txt")

# Polling interval for checking whether the text file content changed.
POLL_INTERVAL_SEC = 0.5

# Cache the last successfully pushed text so we only notify the MCU when needed.
last_sent_text = None

print("LED matrix text app started.")
print(f"Edit {TEXT_FILE} to update the scrolling text.")


def read_text_file() -> str:
    """Read the current text from disk.

    Returns an empty string if the file does not exist or if the content is blank
    after stripping whitespace.
    """
    try:
        text = TEXT_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""

    return text


def send_text_if_changed() -> None:
    """Push updated text to the MCU only when the file content actually changes."""
    global last_sent_text

    text = read_text_file()
    if not text or text == last_sent_text:
        return

    # The sketch exposes a RouterBridge RPC named "set_text".
    # Once the call succeeds, the MCU redraws the scrolling message immediately.
    ok = Bridge.call("set_text", text)
    if ok:
        last_sent_text = text
        print(f"Updated LED text: {text}")
    else:
        print(f"Failed to update LED text: {text}")


def loop():
    """Main App loop: poll the text file and forward updates to the sketch."""
    send_text_if_changed()
    time.sleep(POLL_INTERVAL_SEC)


App.run(user_loop=loop)
