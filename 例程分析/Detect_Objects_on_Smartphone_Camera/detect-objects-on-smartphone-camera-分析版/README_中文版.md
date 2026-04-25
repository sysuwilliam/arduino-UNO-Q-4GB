# Detect Objects on Smartphone Camera 中文版说明

## 项目名称

Detect Objects on Smartphone Camera

## 项目概述

这个示例演示如何把**手机摄像头**作为 Arduino UNO Q 的远程视频输入源，并在网页界面中实时完成**目标检测**。

和前面那些 `Python + sketch` 双端例程不同，这个项目的核心结构是：

- Python 后端负责摄像头连接、AI 推理和 Web UI 通信
- 前端网页负责二维码配对、视频显示、阈值调节和检测结果展示
- 手机通过 **Arduino IoT Remote** 把摄像头画面发送给 UNO Q

也就是说，这是一个更典型的 **Python 后端 + Web 前端 + 手机远程摄像头 + AI Brick** 的 App Lab 示例。

## 功能说明

这个示例完成了以下几件事：

- 生成一个二维码，让手机与 UNO Q 配对
- 使用手机摄像头作为远程视频流输入
- 使用 `video_objectdetection` Brick 对视频流做实时目标检测
- 在浏览器中显示实时视频
- 显示最近的检测结果、置信度和反馈动画
- 支持在网页中动态调整检测阈值

## 使用的 Bricks

本项目使用了两个核心 Brick：

- `web_ui`
  用于启动并管理网页界面

- `video_object_detection`
  用于对视频流中的对象进行检测

## 硬件与软件要求

### 硬件

- Arduino UNO Q 1 块
- 智能手机 1 台（iOS 或 Android）
- 用于打开网页界面的电脑 1 台

### 软件

- Arduino App Lab
- Arduino IoT Remote App

## 如何使用该示例

1. 确保 UNO Q 已连接到本地网络。
2. 在 Arduino App Lab 中启动该 App。
3. 在浏览器中打开对应网页界面。
4. 网页会显示二维码。
5. 在手机上打开 Arduino IoT Remote，选择：

   `Stream phone camera to UNO Q`

6. 使用手机扫描网页二维码。
7. 配对成功后，网页会显示来自手机的实时视频流。
8. 将手机对准不同物体，网页会显示检测结果。

## 工作原理

这个项目的工作链路可以概括为：

```text
手机摄像头
-> WebSocketCamera
-> VideoObjectDetection Brick
-> Python 后端
-> Web UI
-> 浏览器显示结果
```

更具体一点：

1. Python 先生成一个 6 位配对密钥。
2. Python 使用这个密钥初始化 `WebSocketCamera`。
3. 当前端浏览器连接时，后端把密钥、协议、IP、端口发给网页。
4. 网页根据这些信息生成二维码。
5. 手机扫描二维码后，与 UNO Q 建立远程摄像头连接。
6. `VideoObjectDetection` Brick 读取远程视频流并完成目标检测。
7. Python 将检测结果推送到前端。
8. 前端显示最近检测结果、反馈动画和视频流。

## 前后端分工

### Python 后端

主要负责：

- 生成配对密钥
- 初始化远程摄像头
- 初始化目标检测 Brick
- 监听前端连接
- 把检测结果推送给网页
- 接收前端发送的阈值调整请求

### 前端网页

主要负责：

- 展示二维码
- 展示视频流
- 管理置信度滑块
- 展示最近检测结果
- 根据某些对象显示特殊反馈动画

## 这个项目和前面例程的区别

和 `Blink LED`、`Weather Forecast on LED Matrix` 这些例程相比，这个项目有几个明显不同点：

- 没有 `sketch.ino`
- 不依赖 Router Bridge 去驱动 MCU 硬件
- 重点不在 GPIO，而在 **Web UI + AI Brick + 手机摄像头输入**
- 是一个更完整的前后端协同应用

## 高层数据流

整个系统的数据流可以写成：

```text
手机摄像头
-> 远程摄像头连接
-> UNO Q Python 后端
-> VideoObjectDetection Brick
-> 检测结果
-> Web UI
-> 浏览器反馈
```

## 代码理解

### 后端 `python/main.py`

后端主要完成三件事：

1. 建立连接
2. 执行检测
3. 向前端发送结果

核心对象包括：

- `WebUI()`
- `WebSocketCamera(...)`
- `VideoObjectDetection(...)`

### 前端 `assets/app.js`

前端主要完成四件事：

1. 连接后端 Socket.IO
2. 根据后端数据生成二维码
3. 显示视频和检测结果
4. 处理置信度滑块和反馈区

### 页面结构 `assets/index.html`

页面分为三大区域：

- 顶部状态区
- 左侧视频 / 二维码区域
- 右侧控制与结果区域

## 结论

这个例程比前面的硬件控制例程更复杂，也更接近真实应用。  
它展示了 Arduino App Lab 在 UNO Q 上非常有代表性的一种开发模式：

- 通过 **Bricks** 获得高级能力
- 通过 **Web UI** 提供交互界面
- 通过 **手机** 扩展输入设备
- 通过 **Python 后端** 组织业务逻辑

如果前面的例程是“桥接通信入门”，那么这个例程更像是“UNO Q 上 AI + Web + 移动端协作”的综合示例。
