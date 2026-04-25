# 😀 LED_showtext

`LED_showtext` 是一个面向 **Arduino UNO Q** 的 Arduino App Lab 示例工程，用于在板载 **8 x 13 LED 矩阵** 上循环滚动显示文本。

这个工程采用了 UNO Q 常见的双端架构：

- `python/main.py` 运行在 Linux / MPU 侧，负责读取文本文件并把变化推送给 MCU
- `sketch/sketch.ino` 运行在 MCU 侧，负责真正驱动 LED 矩阵并滚动显示文本
- 两端通过 `Arduino_RouterBridge` 通信

## 工作原理

文本更新链路如下：

1. Python 端读取 `python/led_text.txt`
2. 如果文件内容发生变化，Python 调用 `Bridge.call("set_text", text)`
3. MCU 侧通过 `setText(...)` 接收到新的字符串
4. Sketch 端重绘 LED 矩阵，并在 `loop()` 中持续重播滚动动画

这种设计的好处是：

- 不需要每次改文本都重新改 Arduino 代码
- 不需要每次改文本都重新编译 Sketch
- Python 可以作为上层输入源，后续也很容易换成 Web UI、按钮、网络接口等方式

## 项目结构

```text
led_showtext/
├── app.yaml                 # App 元数据
├── README.md                # 项目说明
├── 开发说明.md              # 后续扩展和维护说明
├── python/
│   ├── main.py              # Linux / MPU 侧控制逻辑
│   └── led_text.txt         # 当前要显示的文本内容
└── sketch/
    ├── sketch.ino           # MCU 侧 LED 矩阵显示逻辑
    └── sketch.yaml          # Sketch 平台和库依赖
```

## 核心文件说明

### `python/main.py`

职责：

- 轮询 `python/led_text.txt`
- 检查文件内容是否变化
- 通过 `RouterBridge` 把新文本发送给 Sketch

关键点：

- 轮询频率由 `POLL_INTERVAL_SEC` 控制
- 空文本会被忽略
- 已发送文本会缓存，避免重复发送相同内容

### `sketch/sketch.ino`

职责：

- 初始化 UNO Q 的 LED 矩阵
- 注册 `set_text` RPC 接口
- 用 `ArduinoGraphics` 绘制滚动文本
- 持续循环播放当前文本

关键点：

- 使用 `Font_5x7` 字体，比较适合 8x13 的矩阵尺寸
- 使用 `SCROLL_LEFT` 实现从右向左滚动
- 开机先清屏，等待 Python 推送第一条有效文本

### `python/led_text.txt`

这是最常改的文件。  
只要 App 正在运行，修改并保存这个文件后，LED 矩阵会在约 0.5 秒内切换成新的滚动文本。

## 使用方法

1. 在 Arduino App Lab 中打开此工程
2. 启动 App
3. 打开 `python/led_text.txt`
4. 将文件内容改成你想显示的文本
5. 保存文件
6. 等待约 0.5 秒，LED 矩阵会自动更新并循环滚动显示新文本

例如：

```text
SYSU
```

或者：

```text
Hello UNO Q
```

## 依赖

Sketch 侧依赖：

- `Arduino_RouterBridge`
- `Arduino_LED_Matrix`
- `ArduinoGraphics`

Python 侧依赖：

- Arduino App Lab 内置的 `arduino.app_utils`

## 通信摘要

- Python -> MCU 的方法名：`set_text`
- Python 调用方式：`Bridge.call("set_text", text)`
- Sketch 注册方式：`Bridge.provide_safe("set_text", setText)`

## 注意事项

- UNO Q 的 LED 矩阵只有 **8 x 13**，因此长文本更适合滚动显示
- 复杂字符在这个尺寸下可能显示效果有限
- 如果 LED 矩阵一直为空，先检查 `python/led_text.txt` 是否包含非空内容
- 如果文本更新了但显示没有变化，先确认 App 是否正在运行

## 最常修改的文件

- 修改显示文本：`python/led_text.txt`
- 修改轮询频率：`python/main.py`
- 修改滚动速度、字体、显示逻辑：`sketch/sketch.ino`

## 扩展建议

如果后面要继续扩展这个工程，建议优先阅读：

- `开发说明.md`

里面会更详细地说明：

- 当前双端架构怎么工作
- 哪些位置适合接 Web UI、按钮输入或网络输入
- 如何加字符过滤、长度限制和显示模式切换
