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
  # 生成一个 6 位数字密钥。
  # 这个密钥会被前端写入二维码，供手机扫码后完成配对。
  characters = string.digits
  return ''.join(secrets.choice(characters) for _ in range(6))


# 当前会话的手机配对密钥。
secret = generate_secret()

# WebUI 负责网页前端和浏览器通信。
ui = WebUI()  # 如果要启用 HTTPS，可设置 use_tls=True

# WebSocketCamera 把手机摄像头当作远程视频输入源。
# encrypt=True 表示连接流程会使用加密配对信息。
camera = WebSocketCamera(secret=secret, encrypt=True)

# 当摄像头状态变化时，立即把事件推送给前端。
# 前端会根据这些事件切换二维码视图、已连接视图或视频流视图。
camera.on_status_changed(lambda evt_type, data: ui.send_message(evt_type, data))

# 视频目标检测 Brick。
# 这里将手机摄像头作为输入源，并设置默认置信度阈值为 0.5。
detection = VideoObjectDetection(camera, confidence=0.5, debounce_sec=0.0)

# 当前端浏览器建立连接时，把配对所需的信息发送给网页。
# 前端收到后会生成二维码，供手机 App 扫码连接。
ui.on_connect(lambda sid: ui.send_message("welcome", {
    "client_name": camera.name,
    "secret": secret,
    "status": camera.status,
    "protocol": camera.protocol,
    "ip": camera.ip,
    "port": camera.port
}))

# 前端置信度滑块变化时，会发送 override_th 消息到后端。
# 后端收到后，动态修改模型检测阈值。
ui.on_message("override_th", lambda sid, threshold: detection.override_threshold(threshold))


# 注册一个“检测结果回调函数”。
# 只要模型识别到对象，就会进入这里。
def send_detections_to_ui(detections: dict):
  # detections 是一个按“目标类别”分组的字典。
  # 同一个类别下可能有多个检测结果。
  for key, values in detections.items():
    for value in values:
      entry = {
        "content": key,
        "confidence": value.get("confidence"),
        "timestamp": datetime.now(UTC).isoformat()
      }

      # 将每条检测结果推送给前端页面。
      # 前端会把它显示在 recent detections 列表和反馈区。
      ui.send_message("detection", entry)


# 把回调挂到 VideoObjectDetection Brick 上。
detection.on_detect_all(send_detections_to_ui)

# 启动 App 主循环。
# 这里没有显式 user_loop，因为这个项目主要依赖事件回调来驱动。
App.run()
