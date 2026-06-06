import json
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2


HOST = "0.0.0.0"
PORT = 8080

CAMERA_INDEX = 0
WIDTH = 640
HEIGHT = 480
FPS = 30
JPEG_QUALITY = 80

latest_frame = None
latest_status = "starting"
latest_brightness = 0.0
latest_result = {
    "status": latest_status,
    "brightness": latest_brightness,
    "bright": False,
}
lock = threading.Lock()


def process_frame(frame):
    """Apply OpenCV processing and return the processed frame plus result data."""
    brightness = float(frame.mean())
    bright = brightness >= 80.0

    label = "BRIGHT" if bright else "DARK"
    color = (0, 255, 0) if bright else (0, 165, 255)

    cv2.putText(
        frame,
        f"OpenCV {label} brightness={brightness:.1f}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        color,
        2,
        cv2.LINE_AA,
    )

    result = {
        "status": "streaming",
        "brightness": round(brightness, 1),
        "bright": bright,
        "label": label.lower(),
    }
    return frame, result


def camera_loop():
    global latest_frame, latest_status, latest_brightness, latest_result

    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, FPS)

    if not cap.isOpened():
        with lock:
            latest_status = "cannot open camera"
            latest_result = {
                "status": latest_status,
                "brightness": latest_brightness,
                "bright": False,
                "label": "error",
            }
        print("cannot open camera")
        return

    print("camera opened")

    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            with lock:
                latest_status = "failed to read frame"
                latest_result = {
                    "status": latest_status,
                    "brightness": latest_brightness,
                    "bright": False,
                    "label": "error",
                }
            time.sleep(0.2)
            continue

        frame, result = process_frame(frame)

        with lock:
            latest_frame = frame
            latest_status = result["status"]
            latest_brightness = result["brightness"]
            latest_result = result

        time.sleep(1 / FPS)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_index()
        elif self.path == "/stream.mjpg":
            self.send_stream()
        elif self.path == "/snapshot.jpg":
            self.send_snapshot()
        elif self.path == "/health":
            self.send_health()
        elif self.path == "/result.json":
            self.send_result_json()
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "not found")

    def get_jpeg(self):
        with lock:
            frame = None if latest_frame is None else latest_frame.copy()

        if frame is None:
            return None

        ok, encoded = cv2.imencode(
            ".jpg",
            frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY],
        )
        if not ok:
            return None

        return encoded.tobytes()

    def send_index(self):
        html = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>OpenCV Camera</title>
  <style>
    body {
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      background: #f4f7fb;
      font-family: Arial, sans-serif;
      color: #1f2933;
    }
    main {
      width: min(960px, calc(100vw - 32px));
      display: grid;
      gap: 14px;
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: end;
      gap: 16px;
    }
    h1 {
      margin: 0;
      font-size: 28px;
    }
    .viewer {
      aspect-ratio: 4 / 3;
      background: #111827;
      border: 1px solid #d9e2ec;
      border-radius: 8px;
      overflow: hidden;
      display: grid;
      place-items: center;
    }
    img {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }
    .meta {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      color: #52606d;
      font-size: 14px;
    }
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>OpenCV Camera</h1>
        <div class="meta">Host Debian OpenCV stream</div>
      </div>
      <a href="/snapshot.jpg" target="_blank">Snapshot</a>
    </header>
    <section class="viewer">
      <img src="/stream.mjpg" alt="OpenCV stream">
    </section>
    <div class="meta">
      <a href="/health" target="_blank">Health</a>
      <a href="/result.json" target="_blank">Result JSON</a>
    </div>
  </main>
</body>
</html>
"""
        data = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def send_snapshot(self):
        jpeg = self.get_jpeg()
        if jpeg is None:
            self.send_error(HTTPStatus.SERVICE_UNAVAILABLE, "no frame")
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(jpeg)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(jpeg)

    def send_stream(self):
        self.send_response(HTTPStatus.OK)
        self.send_header("Age", "0")
        self.send_header("Cache-Control", "no-cache, private")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.end_headers()

        while True:
            jpeg = self.get_jpeg()
            if jpeg is None:
                time.sleep(0.1)
                continue

            try:
                self.wfile.write(b"--frame\r\n")
                self.wfile.write(b"Content-Type: image/jpeg\r\n")
                self.wfile.write(f"Content-Length: {len(jpeg)}\r\n\r\n".encode("ascii"))
                self.wfile.write(jpeg)
                self.wfile.write(b"\r\n")
            except (BrokenPipeError, ConnectionResetError):
                break

            time.sleep(1 / FPS)

    def send_health(self):
        with lock:
            text = f"{latest_status}, brightness={latest_brightness:.1f}\n"

        data = text.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def send_result_json(self):
        with lock:
            payload = json.dumps(latest_result).encode("utf-8")

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)


threading.Thread(target=camera_loop, daemon=True).start()

server = ThreadingHTTPServer((HOST, PORT), Handler)
print(f"OpenCV camera server: http://0.0.0.0:{PORT}")
server.serve_forever()
