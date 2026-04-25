# app.yaml 解析

原始文件内容：

```yaml
name: Detect Objects on Smartphone Camera
description: This example showcases object detection within a live feed from a smartphone's camera.
ports:
- 8080
bricks:
- arduino:video_object_detection:
    devices:
    - remote_camera_0
- arduino:web_ui: {}
icon: 📽️
```

## 1. `name`

```yaml
name: Detect Objects on Smartphone Camera
```

表示这个 App 在 Arduino App Lab 中显示的名称。

## 2. `description`

```yaml
description: This example showcases object detection within a live feed from a smartphone's camera.
```

表示应用简介。  
它说明这个示例的主要能力是：

- 使用手机摄像头视频流进行目标检测

## 3. `ports`

```yaml
ports:
- 8080
```

说明这个 App 需要开放的端口。  
通常是因为 Web UI 或相关服务需要通过该端口对外提供访问。

## 4. `bricks`

```yaml
bricks:
- arduino:video_object_detection:
    devices:
    - remote_camera_0
- arduino:web_ui: {}
```

这是整个配置中最关键的部分。

### `arduino:video_object_detection`

它表示：

- 应用使用目标检测 Brick

并且指定输入设备：

```yaml
devices:
  - remote_camera_0
```

这说明模型输入不是本地摄像头，而是：

- `remote_camera_0`

也就是远程手机摄像头。

### `arduino:web_ui`

表示应用还会启动一个 Web UI Brick，用来托管网页界面。

## 5. `icon`

```yaml
icon: 📽️
```

这是 App Lab 中显示的图标。

## 总结

这个 `app.yaml` 很清楚地反映了项目的定位：

- 这是一个视频目标检测应用
- 输入设备是远程手机摄像头
- 界面通过 Web UI 提供

因此它不是一个传统的单文件硬件控制项目，而是一个依赖 Brick 组合完成的 App Lab 全栈示例。
