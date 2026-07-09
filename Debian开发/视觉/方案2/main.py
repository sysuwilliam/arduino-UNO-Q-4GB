"""
================================================================================
动态矩形中心检测系统 - Debian OpenCV 版本（方案2：评分机制算法）
================================================================================

基于 OpenCV 的动态矩形中心检测系统，在 Arduino UNO Q Debian 主机上运行。
移植自视觉代码的 CenterGet 算法，采用评分机制选择最佳矩形。

【整体架构】
1. 图像采集模块：通过摄像头实时捕获视频帧
2. 矩形检测模块：检测图像中的矩形区域并提取顶点坐标
3. 矩形验证模块：验证检测到的四边形是否为标准矩形（多重验证）
4. 评分机制：根据角度和面积计算综合得分，选择最佳矩形
5. 中心计算模块：计算矩形的几何中心（对角线交点）
6. HTTP服务模块：提供Web界面和API接口

【图像处理流程】
输入图像 → 灰度化 → 高斯模糊 → 二值化 → Canny边缘检测 → 轮廓查找 
→ 多边形拟合 → 多重验证（面积/顶点/边界/角度/边长）→ 评分机制 
→ 选择最佳矩形 → 中心计算 → 结果可视化

【算法特点】
- 多重验证：6重筛选条件，降低误检率
- 评分机制：角度得分(60%) + 面积得分(40%)，平衡精度和实用性
- 鲁棒性好：适应不同大小、位置、角度的矩形

================================================================================
"""

import json
import threading
import time
import math
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2
import numpy as np

# HTTP服务配置
HOST = "0.0.0.0"
PORT = 8080

# 摄像头配置
CAMERA_INDEX = 0
WIDTH = 640
HEIGHT = 480
FPS = 30
JPEG_QUALITY = 80

# 图像预处理参数
threshold_value = 144  # 二值化阈值
canny_low_threshold = 50  # Canny低阈值
canny_high_threshold = 150  # Canny高阈值
gaussian_blur_size = 5  # 高斯模糊核大小

# 矩形验证参数
min_area = 500  # 最小面积
border_threshold = 5  # 边界距离阈值
angle_min = 70  # 最小角度
angle_max = 110  # 最大角度
max_length_ratio = 5  # 最大边长比例

# 面积阈值参数（用于最终筛选）
S_THRESHOLD = 2000
THRESHOLD_MIN = 500
THRESHOLD_MAX = 10000
THRESHOLD_STEP = 500

# 全局状态
latest_frame = None
latest_status = "starting"
latest_result = {
    "status": latest_status,
    "rect_detected": False,
    "center": None,
    "error": None,
    "vertices": None,
    "area": 0,
    "score": 0,
}
lock = threading.Lock()


def preprocess_image(img):
    """
    图像预处理
    
    参数：
        img: 输入图像（BGR格式）
    
    返回：
        thresh: 二值化后的图像
    
    处理流程：
        BGR → 灰度 → 高斯模糊 → 二值化
    """
    # 灰度化
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 高斯模糊（降噪）
    blurred = cv2.GaussianBlur(gray, (gaussian_blur_size, gaussian_blur_size), 0)
    
    # 二值化
    _, thresh = cv2.threshold(blurred, threshold_value, 255, cv2.THRESH_BINARY)
    
    return thresh


def calculate_equidistant_center(pts):
    """
    计算矩形的几何中心（对角线交点）
    
    参数：
        pts: 四个顶点坐标，shape=(4, 2)
    
    返回：
        (x, y): 中心坐标
    
    原理：
        矩形的两条对角线交点即为几何中心
        通过求解两条直线的交点得到
    """
    pts = np.array(pts, dtype=np.float32)
    if len(pts) != 4:
        return None
    
    # 两条对角线
    diag1_start, diag1_end = pts[0], pts[2]
    diag2_start, diag2_end = pts[1], pts[3]
    
    # 直线方程: ax + by + c = 0
    a1 = diag1_end[1] - diag1_start[1]
    b1 = diag1_start[0] - diag1_end[0]
    c1 = diag1_end[0] * diag1_start[1] - diag1_start[0] * diag1_end[1]
    
    a2 = diag2_end[1] - diag2_start[1]
    b2 = diag2_start[0] - diag2_end[0]
    c2 = diag2_end[0] * diag2_start[1] - diag2_start[0] * diag2_end[1]
    
    # 计算交点
    denom = a1 * b2 - a2 * b1
    if denom != 0:
        x = (b1 * c2 - b2 * c1) / denom
        y = (a2 * c1 - a1 * c2) / denom
    else:
        # 如果对角线平行，则计算几何中心
        x = np.mean(pts[:, 0])
        y = np.mean(pts[:, 1])
    
    return (int(round(x)), int(round(y)))


def CenterGet(img, return_pts=False):
    """
    矩形中心检测算法（带评分机制）
    
    参数：
        img: 输入图像（BGR格式）
        return_pts: 是否返回顶点坐标
    
    返回：
        如果 return_pts=False: 返回中心坐标 (x, y) 或 None
        如果 return_pts=True: 返回 (中心坐标, 顶点坐标, 得分) 或 (None, None, 0)
    
    算法流程：
        1. 图像预处理（灰度化、模糊、二值化）
        2. Canny边缘检测
        3. 轮廓检测
        4. 遍历轮廓，进行多重验证：
           - 面积过滤
           - 多边形拟合
           - 顶点数验证
           - 边界检查
           - 角度验证
           - 边长比例验证
        5. 计算评分（角度得分 + 面积得分）
        6. 选择评分最高的矩形
        7. 计算中心点
    """
    # 图像预处理
    frame = preprocess_image(img)
    
    # Canny边缘检测
    edges = cv2.Canny(frame, canny_low_threshold, canny_high_threshold)
    
    # 轮廓检测
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 初始化最佳轮廓变量
    best_contour = None
    best_score = -1
    best_center = None
    best_approx = None
    
    # 处理每个轮廓以寻找类矩形
    for contour in contours:
        # === 验证1：面积过滤 ===
        area = cv2.contourArea(contour)
        if area < min_area:
            continue
        
        # === 验证2：多边形拟合 ===
        perimeter = cv2.arcLength(contour, True)
        epsilon = 0.01 * perimeter
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # === 验证3：顶点数筛选 ===
        if len(approx) != 4:
            continue
        
        # 提取角点坐标
        pts = approx.reshape(4, 2).astype(int)
        
        # === 验证4：边界检查 ===
        h, w = frame.shape[:2]
        if not all(border_threshold < pt[0] < w - border_threshold and
                    border_threshold < pt[1] < h - border_threshold for pt in pts):
            continue
        
        # === 验证5：角度验证 ===
        angles = []
        for i in range(4):
            p_prev = pts[(i - 1) % 4]
            p_curr = pts[i]
            p_next = pts[(i + 1) % 4]
            
            vec1 = p_prev - p_curr
            vec2 = p_next - p_curr
            
            angle = math.degrees(math.atan2(vec2[1], vec2[0]) - math.atan2(vec1[1], vec1[0]))
            angle = abs(angle)
            if angle > 180:
                angle = 360 - angle
            angles.append(angle)
        
        # 检查角度是否在合理范围内
        if not all(angle_min < angle < angle_max for angle in angles):
            continue
        
        # === 验证6：边长比例验证 ===
        lengths = []
        for i in range(4):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % 4]
            length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            lengths.append(length)
        
        max_len = max(lengths)
        min_len = min(lengths)
        
        if max_len / min_len > max_length_ratio:
            continue
        
        # === 计算评分 ===
        # 角度得分（与90度的平均偏差，越小越好）
        angle_deviation = sum(abs(angle - 90) for angle in angles) / 4
        angle_score = 100 - angle_deviation  # 满分100分
        
        # 面积得分（归一化处理，越大越好）
        max_possible_area = (w * h) / 2  # 假设最大可能面积为图像面积的一半
        area_score = min(100, (area / max_possible_area) * 100)
        
        # 综合得分（角度权重60%，面积权重40%）
        total_score = 0.6 * angle_score + 0.4 * area_score
        
        # === 更新最佳轮廓 ===
        if total_score > best_score:
            best_score = total_score
            best_contour = contour
            best_approx = approx
            
            # 计算中心点
            M = cv2.moments(contour)
            if M['m00'] != 0:
                best_center = calculate_equidistant_center(pts)
            else:
                best_center = None
    
    # 返回结果
    if best_contour is not None and best_center is not None:
        if return_pts:
            return best_center, best_approx, best_score
        return best_center
    else:
        if return_pts:
            return None, None, 0
        return None


def process_frame(frame):
    """处理帧并返回处理后的帧和结果数据"""
    global S_THRESHOLD
    
    # 使用CenterGet算法检测矩形
    center, approx, score = CenterGet(frame, return_pts=True)
    
    rect_detected = False
    error = None
    vertices = None
    area = 0
    
    if center is not None and approx is not None:
        # 提取四个顶点
        pts = approx.reshape(4, 2).astype(int)
        
        # 计算面积
        area = cv2.contourArea(approx)
        
        # 面积阈值验证
        if area > S_THRESHOLD:
            rect_detected = True
            vertices = [[int(pts[i][0]), int(pts[i][1])] for i in range(4)]
            
            # 绘制矩形边框（绿色）
            for i in range(4):
                next_i = (i + 1) % 4
                cv2.line(frame, (pts[i][0], pts[i][1]), 
                        (pts[next_i][0], pts[next_i][1]), (0, 255, 0), 3)
            
            # 绘制顶点（红色）
            for i in range(4):
                cv2.circle(frame, (pts[i][0], pts[i][1]), 5, (0, 0, 255), -1)
            
            # 绘制中心点（绿色，大圆）
            cv2.circle(frame, center, 8, (0, 255, 0), -1)
            
            # 显示中心坐标
            text = f"Center: ({center[0]}, {center[1]})"
            cv2.putText(frame, text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            
            # 计算与图像中心的偏差
            center_x = WIDTH // 2
            center_y = HEIGHT // 2
            error_x = center_x - center[0]
            error_y = center_y - center[1]
            error = [error_x, error_y]
            
            # 显示偏差
            error_text = f"Error: ({error_x:+04d}, {error_y:+04d})"
            cv2.putText(frame, error_text, (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            
            # 显示得分
            score_text = f"Score: {score:.1f}"
            cv2.putText(frame, score_text, (10, 110),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
    
    # 显示当前面积阈值
    threshold_text = f"S_THRESHOLD: {S_THRESHOLD}"
    cv2.putText(frame, threshold_text, (10, frame.shape[0] - 20),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    
    # 显示检测状态
    status_text = "RECT DETECTED" if rect_detected else "NO RECT"
    status_color = (0, 255, 0) if rect_detected else (0, 0, 255)
    cv2.putText(frame, status_text, (frame.shape[1] - 200, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
    
    result = {
        "status": "streaming",
        "rect_detected": rect_detected,
        "center": center,
        "error": error,
        "vertices": vertices,
        "area": int(area),
        "score": round(score, 2),
        "s_threshold": S_THRESHOLD,
    }
    
    return frame, result


def camera_loop():
    """摄像头循环采集线程"""
    global latest_frame, latest_status, latest_result
    
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
                "rect_detected": False,
                "center": None,
                "error": None,
                "vertices": None,
                "area": 0,
                "score": 0,
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
                    "rect_detected": False,
                    "center": None,
                    "error": None,
                    "vertices": None,
                    "area": 0,
                    "score": 0,
                }
            time.sleep(0.2)
            continue
        
        frame, result = process_frame(frame)
        
        with lock:
            latest_frame = frame
            latest_status = result["status"]
            latest_result = result
        
        time.sleep(1 / FPS)


class Handler(BaseHTTPRequestHandler):
    """HTTP请求处理器"""
    
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
        elif self.path == "/config":
            self.send_config()
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "not found")
    
    def do_POST(self):
        if self.path == "/threshold/increase":
            self.increase_threshold()
        elif self.path == "/threshold/decrease":
            self.decrease_threshold()
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "not found")
    
    def get_jpeg(self):
        """获取JPEG图像数据"""
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
        """发送主页HTML"""
        html = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>矩形中心检测系统 - 方案2（评分机制）</title>
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
    .controls {
      display: flex;
      gap: 12px;
      margin-top: 8px;
    }
    button {
      padding: 8px 16px;
      border: 1px solid #d9e2ec;
      border-radius: 4px;
      background: white;
      cursor: pointer;
      font-size: 14px;
    }
    button:hover {
      background: #f4f7fb;
    }
    .info {
      background: #e8f4f8;
      padding: 12px;
      border-radius: 4px;
      font-size: 13px;
      line-height: 1.6;
    }
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>矩形中心检测系统</h1>
        <div class="meta">Arduino UNO Q - 方案2（评分机制算法）</div>
      </div>
      <a href="/snapshot.jpg" target="_blank">快照</a>
    </header>
    <section class="viewer">
      <img src="/stream.mjpg" alt="实时视频流">
    </section>
    <div class="info">
      <strong>算法特点：</strong><br>
      • 多重验证：面积、顶点、边界、角度、边长比例 6重筛选<br>
      • 评分机制：角度得分(60%) + 面积得分(40%)，选择最佳矩形<br>
      • 鲁棒性好：适应不同大小、位置、角度的矩形
    </div>
    <div class="meta">
      <a href="/health" target="_blank">健康检查</a>
      <a href="/result.json" target="_blank">检测结果</a>
      <a href="/config" target="_blank">配置信息</a>
    </div>
    <div class="controls">
      <button onclick="fetch('/threshold/increase', {method: 'POST'}).then(() => location.reload())">增加面积阈值 (+)</button>
      <button onclick="fetch('/threshold/decrease', {method: 'POST'}).then(() => location.reload())">减少面积阈值 (-)</button>
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
        """发送快照"""
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
        """发送MJPEG视频流"""
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
        """发送健康检查"""
        with lock:
            text = f"{latest_status}\n"
        
        data = text.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)
    
    def send_result_json(self):
        """发送检测结果JSON"""
        with lock:
            payload = json.dumps(latest_result).encode("utf-8")
        
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)
    
    def send_config(self):
        """发送配置信息"""
        config = {
            "s_threshold": S_THRESHOLD,
            "threshold_min": THRESHOLD_MIN,
            "threshold_max": THRESHOLD_MAX,
            "threshold_step": THRESHOLD_STEP,
            "threshold_value": threshold_value,
            "canny_low_threshold": canny_low_threshold,
            "canny_high_threshold": canny_high_threshold,
            "gaussian_blur_size": gaussian_blur_size,
            "min_area": min_area,
            "border_threshold": border_threshold,
            "angle_min": angle_min,
            "angle_max": angle_max,
            "max_length_ratio": max_length_ratio,
        }
        payload = json.dumps(config).encode("utf-8")
        
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)
    
    def increase_threshold(self):
        """增加面积阈值"""
        global S_THRESHOLD
        S_THRESHOLD = min(THRESHOLD_MAX, S_THRESHOLD + THRESHOLD_STEP)
        print(f"面积阈值增加到: {S_THRESHOLD}")
        
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(f"Threshold increased to {S_THRESHOLD}".encode("utf-8"))
    
    def decrease_threshold(self):
        """减少面积阈值"""
        global S_THRESHOLD
        S_THRESHOLD = max(THRESHOLD_MIN, S_THRESHOLD - THRESHOLD_STEP)
        print(f"面积阈值减少到: {S_THRESHOLD}")
        
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(f"Threshold decreased to {S_THRESHOLD}".encode("utf-8"))


# 启动摄像头线程
threading.Thread(target=camera_loop, daemon=True).start()

# 启动HTTP服务器
server = ThreadingHTTPServer((HOST, PORT), Handler)
print(f"矩形中心检测服务（方案2-评分机制）: http://0.0.0.0:{PORT}")
server.serve_forever()