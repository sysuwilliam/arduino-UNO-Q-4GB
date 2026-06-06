# OpenCV Detection

This project uses the host Debian system for OpenCV camera access.

Run the OpenCV service on the board host:

```bash
cd "/home/arduino/ArduinoApps/opencv detection/opencv-detection"
python3 python/debian_opencv_server.py
```

Then open:

```text
http://<board-ip>:8080
```

If you also run this App Lab project, its WebUI page on port 7000 embeds the
host service running on port 8080.
