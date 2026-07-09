# Debian OpenCV

Basic host-Debian OpenCV camera service for Arduino UNO Q.

This project runs directly on the UNO Q Debian host, not inside an App Lab
container. It opens the USB camera with OpenCV and serves a browser preview on
port `8080`.

## Run

```bash
cd "/home/arduino/ArduinoApps/debian-opencv"
./run_host.sh
```

Open:

```text
http://<board-ip>:8080
```

Example:

```text
http://10.233.80.145:8080
```

## Endpoints

- `/` - Web preview page.
- `/stream.mjpg` - MJPEG video stream.
- `/snapshot.jpg` - Single JPEG frame.
- `/health` - Plain text status.
- `/result.json` - Latest OpenCV result.

Example `/result.json`:

```json
{
  "status": "streaming",
  "brightness": 92.4,
  "bright": true,
  "label": "bright"
}
```

## Add Processing

Edit `process_frame(frame)` in `main.py`.

The function returns:

```python
return frame, result
```

- `frame` is the processed image to display.
- `result` is the JSON object served at `/result.json`.

## Background Run

```bash
cd "/home/arduino/ArduinoApps/debian-opencv"
nohup ./run_host.sh > opencv.log 2>&1 &
```

Stop:

```bash
pkill -f "/home/arduino/ArduinoApps/debian-opencv/main.py"
```
