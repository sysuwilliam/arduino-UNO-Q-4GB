# 矩形中心检测系统

基于 OpenCV 的动态矩形中心检测系统，在 Arduino UNO Q Debian 主机上运行。

## 功能特性

- **实时矩形检测**：检测图像中的矩形区域并提取顶点坐标
- **矩形验证**：验证检测到的四边形是否为标准矩形
- **中心计算**：计算矩形的几何中心（对角线交点）
- **偏差计算**：计算矩形中心与图像中心的偏差
- **Web界面**：提供浏览器实时预览和参数调整

## 运行

```bash
cd "/home/arduino/ArduinoApps/方案1"
./run_host.sh
```

打开浏览器访问：

```text
http://<board-ip>:8080
```

示例：

```text
http://10.233.80.145:8080
```

## HTTP 端点

- `/` - Web 预览页面
- `/stream.mjpg` - MJPEG 视频流
- `/snapshot.jpg` - 单帧 JPEG 快照
- `/health` - 健康检查
- `/result.json` - 检测结果（JSON格式）
- `/config` - 配置信息（JSON格式）
- `/threshold/increase` (POST) - 增加面积阈值
- `/threshold/decrease` (POST) - 减少面积阈值

## 结果格式

`/result.json` 示例：

```json
{
  "status": "streaming",
  "rect_detected": true,
  "center": [320, 240],
  "error": [0, 0],
  "vertices": [[100, 100], [540, 100], [540, 380], [100, 380]],
  "area": 152000,
  "s_threshold": 2000
}
```

字段说明：
- `status`: 当前状态
- `rect_detected`: 是否检测到标准矩形
- `center`: 矩形中心坐标 [x, y]
- `error`: 与图像中心的偏差 [dx, dy]
- `vertices`: 矩形四个顶点坐标
- `area`: 矩形面积
- `s_threshold`: 当前面积阈值

## 参数调整

### Web界面调整
在 Web 页面点击按钮调整面积阈值

### API调整
```bash
# 增加阈值
curl -X POST http://<board-ip>:8080/threshold/increase

# 减少阈值
curl -X POST http://<board-ip>:8080/threshold/decrease
```

## 图像处理流程

```
输入图像 → 高斯模糊 → Canny边缘检测 → 轮廓查找 → 多边形拟合 
→ 四边形筛选 → 矩形验证 → 中心计算 → 结果可视化
```

详细步骤：
1. **高斯模糊**：降噪处理，减少边缘检测中的噪声干扰
2. **Canny边缘检测**：提取图像中的边缘信息
3. **轮廓查找**：从边缘图像中提取所有轮廓
4. **多边形拟合**：使用Douglas-Peucker算法将轮廓拟合为多边形
5. **四边形筛选**：筛选出具有4个顶点的凸多边形
6. **矩形验证**：
   - 计算四条边的长度
   - 验证对边是否平行
   - 验证邻边是否垂直
   - 验证面积是否满足阈值
7. **中心计算**：计算两条对角线的交点作为矩形中心
8. **结果可视化**：绘制矩形边框、顶点、中心点及坐标信息

## 可调参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| canny_thresh1 | 50 | Canny边缘检测低阈值 |
| canny_thresh2 | 150 | Canny边缘检测高阈值 |
| approx_epsilon | 0.04 | 多边形拟合精度 |
| area_min_ratio | 0.001 | 最小面积比例 |
| gaussian_blur_size | 5 | 高斯模糊核大小 |
| S_THRESHOLD | 2000 | 面积阈值 |
| length_threshold | 120 | 边长差异阈值 |

## 后台运行

```bash
cd "/home/arduino/ArduinoApps/方案1"
nohup ./run_host.sh > rect_detection.log 2>&1 &
```

停止：

```bash
pkill -f "/home/arduino/ArduinoApps/方案1/main.py"
```

## 应用场景

- 工业视觉定位
- 机器人导航
- 自动对焦系统
- 目标跟踪
- 电赛视觉任务

## 技术特点

- 直接在 Debian 主机运行，性能高
- 线程安全的帧处理
- 实时 MJPEG 流式传输
- RESTful API 接口
- 可通过 Web 或 API 动态调整参数