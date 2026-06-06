# OpenCV Detection

This project runs directly on the Arduino UNO Q host Debian system. It does not
run inside an App Lab container because the App Lab container cannot reliably
open `/dev/video0` with OpenCV.

## What It Does

- Opens the USB camera with OpenCV.
- Applies simple frame processing in `process_frame()`.
- Serves a browser preview on port `8080`.
- Exposes machine-readable OpenCV results through `/result.json`.

## Run

On the UNO Q host Debian terminal:

```bash
cd "/home/arduino/ArduinoApps/opencv-detection"
./run_host.sh
```

Or:

```bash
cd "/home/arduino/ArduinoApps/opencv-detection"
python3 main.py
```

Open from your computer:

```text
http://<board-ip>:8080
```

For example:

```text
http://10.233.80.145:8080
```

## Endpoints

- `/` - Web preview page.
- `/stream.mjpg` - MJPEG video stream.
- `/snapshot.jpg` - Single JPEG frame.
- `/health` - Plain text status.
- `/result.json` - Latest OpenCV result for other programs.

Example `/result.json`:

```json
{
  "status": "streaming",
  "brightness": 92.4,
  "bright": true,
  "label": "bright"
}
```

## Where To Add OpenCV Processing

Edit `process_frame(frame)` in `main.py`.

The function should return:

```python
return frame, result
```

- `frame` is the processed image to display.
- `result` is a dictionary exposed at `/result.json`.

## Run In Background

```bash
cd "/home/arduino/ArduinoApps/opencv-detection"
nohup ./run_host.sh > opencv.log 2>&1 &
```

View logs:

```bash
tail -f "/home/arduino/ArduinoApps/opencv-detection/opencv.log"
```

Stop:

```bash
pkill -f "/home/arduino/ArduinoApps/opencv-detection/main.py"
```

## Sending OpenCV Results To The MCU Later

Recommended architecture:

```text
Host Debian OpenCV service
  -> http://127.0.0.1:8080/result.json
  -> App Lab Python bridge app
  -> RouterBridge
  -> MCU sketch
```

Reason:

- OpenCV should run on host Debian because it can open the camera there.
- RouterBridge should run inside App Lab because App Lab provides the Bridge
  runtime.
- The two sides can communicate through HTTP.

Minimal App Lab Python bridge example:

```python
import time
import urllib.request
import json

from arduino.app_utils import App, Bridge


RESULT_URL = "http://host.docker.internal:8080/result.json"


def read_result():
    with urllib.request.urlopen(RESULT_URL, timeout=1) as response:
        return json.loads(response.read().decode("utf-8"))


def loop():
    try:
        result = read_result()
        Bridge.call("set_detection", result["label"], result["brightness"])
    except Exception as exc:
        print(f"Failed to forward OpenCV result: {exc}")

    time.sleep(0.5)


App.run(user_loop=loop)
```

Depending on App Lab networking, `host.docker.internal` may not resolve. If it
does not, use the board IP instead:

```python
RESULT_URL = "http://10.233.80.145:8080/result.json"
```

Minimal MCU sketch side:

```cpp
#include <Arduino_RouterBridge.h>

bool setDetection(String label, float brightness) {
  // Use the OpenCV result here: LED matrix, GPIO, buzzer, etc.
  return true;
}

void setup() {
  Bridge.begin();
  Bridge.provide_safe("set_detection", setDetection);
}

void loop() {
}
```
