# SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
#
# SPDX-License-Identifier: MPL-2.0

import secrets
import string
from datetime import datetime, UTC

from arduino.app_utils import App
from arduino.app_bricks.web_ui import WebUI
from arduino.app_bricks.video_objectdetection import VideoObjectDetection
from arduino.app_peripherals.camera import WebSocketCamera


def generate_secret() -> str:
  # Generate a one-time 6-digit code used by the mobile app
  # to pair with the UNO Q over the local network.
  characters = string.digits
  return ''.join(secrets.choice(characters) for _ in range(6))


# Pairing secret displayed in the frontend QR code.
secret = generate_secret()

# WebUI hosts the browser frontend.
ui = WebUI()  # set use_tls=True to enable TLS encryption for HTTPS

# The phone camera acts as a remote video source.
# encrypt=True secures the pairing/transport setup.
camera = WebSocketCamera(secret=secret, encrypt=True)

# Forward camera status changes to the browser so the UI can switch
# between QR code, connected state, and live stream state.
camera.on_status_changed(lambda evt_type, data: ui.send_message(evt_type, data))

# Run object detection on frames received from the smartphone camera.
detection = VideoObjectDetection(camera, confidence=0.5, debounce_sec=0.0)

# When a browser tab connects, send the pairing information needed
# to generate the QR code and establish the phone-to-board link.
ui.on_connect(lambda sid: ui.send_message("welcome", {"client_name": camera.name, "secret": secret, "status": camera.status, "protocol": camera.protocol, "ip": camera.ip, "port": camera.port}))

# Allow the frontend confidence slider to override the detection threshold
# while the app is running.
ui.on_message("override_th", lambda sid, threshold: detection.override_threshold(threshold))

# Register a callback for when all objects are detected
def send_detections_to_ui(detections: dict):
  # The Brick returns a dictionary keyed by detected class name.
  # Each key may contain multiple detection results for the same class.
  for key, values in detections.items():
    for value in values:
      entry = {
        "content": key,
        "confidence": value.get("confidence"),
        "timestamp": datetime.now(UTC).isoformat()
      }

      # Push each detection to the browser so it can update
      # the recent detections list and feedback area.
      ui.send_message("detection", entry)

detection.on_detect_all(send_detections_to_ui)

# Keep the backend event loop alive.
App.run()
