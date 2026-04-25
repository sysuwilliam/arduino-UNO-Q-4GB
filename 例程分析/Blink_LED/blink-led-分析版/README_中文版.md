# Blink LED 中文版说明

## 项目名称

Blink LED

## 项目概述

`Blink` 示例会让开发板上的板载 LED 每隔 1 秒切换一次状态。这个例程展示了如何通过 Python 和 Arduino 之间的 Router Bridge 通信，实现最基础的 LED 控制。

## 功能说明

这个示例实现的是一个最简单的“LED 闪烁”应用：

- Python 脚本持续运行，并按照固定的 1 秒周期切换一次 LED 状态。
- Arduino 草图负责真正控制 LED 硬件引脚。
- Python 和 Arduino 之间通过 Router Bridge 建立调用关系。

从职责划分来看：

- Python 端负责“时间控制”和“状态切换逻辑”。
- Arduino 端负责“底层硬件控制”。
- Router Bridge 负责“把 Python 的请求传递给 Arduino”。

## 使用的 Bricks

这个示例**不使用任何 Bricks 模块**。

它演示的是 Python 和 Arduino 之间的直接 Router Bridge 通信。

## 硬件与软件要求

### 硬件

- Arduino UNO Q 1 块
- USB-C 数据线 1 根（用于供电和下载程序）

### 软件

- Arduino App Lab

补充说明：

你也可以把 Arduino UNO Q 当作单板计算机（SBC）来运行这个例程。此时通常需要连接 USB-C 扩展坞，并外接鼠标、键盘和显示器。

## 如何使用该示例

1. 在 Arduino App Lab 中运行该应用。
2. 观察开发板上的 LED。
3. LED 会每隔 1 秒自动切换一次亮灭状态。

## 工作原理

应用启动后，系统会执行以下流程：

### 1. Python 端负责计时与状态切换

Python 脚本中有一个循环逻辑：

```python
from arduino.app_utils import *
import time

led_state = False

while True:
    time.sleep(1)
    led_state = not led_state
    Bridge.call("set_led_state", led_state)
```

它的核心作用是：

- 每隔 1 秒暂停一次；
- 将 `led_state` 从 `False` 和 `True` 之间来回切换；
- 每次切换后，调用 `Bridge.call("set_led_state", led_state)`，把新的 LED 状态发送给 Arduino。

### 2. Arduino 端向 Python 暴露可调用函数

Arduino 在 `setup()` 中注册了一个可被 Python 调用的函数：

```cpp
Bridge.provide("set_led_state", set_led_state);
```

这表示：

- Python 端以后只要调用名字为 `set_led_state` 的桥接接口；
- Router Bridge 就会把请求转发到 Arduino 里的 `set_led_state` 函数。

### 3. Arduino 端控制硬件 LED

Arduino 中实际执行控制的代码是：

```cpp
void set_led_state(bool state) {
    digitalWrite(LED_BUILTIN, state ? LOW : HIGH);
}
```

这段代码的含义是：

- 当 `state` 为 `true` 时，写入 `LOW`；
- 当 `state` 为 `false` 时，写入 `HIGH`。

这里需要特别注意：**这块板子的板载 LED 使用了反相逻辑**。

也就是说：

- `LOW` 表示 LED 亮；
- `HIGH` 表示 LED 灭。

这种现象常见于板载 LED 的连接方式中，因为 LED 可能不是以“高电平点亮”的方式接线。

## 高层数据流

整个例程的数据流可以概括为：

```text
Python 定时循环 -> Router Bridge -> Arduino LED 控制函数 -> 板载 LED
```

## 代码理解

### Python 后端 `main.py`

Python 部分负责时间和状态逻辑：

- `import time`
  用于提供 `sleep()` 等计时函数。

- `led_state = False`
  用一个布尔变量记录 LED 当前目标状态。

- `loop()`
  作为应用反复执行的用户逻辑函数。

- `time.sleep(1)`
  让程序暂停 1 秒，从而形成闪烁节奏。

- `led_state = not led_state`
  每轮循环都将状态取反，实现亮灭切换。

- `Bridge.call("set_led_state", led_state)`
  通过 Router Bridge 把新的状态传给 Arduino。

### Arduino 硬件端 `sketch.ino`

Arduino 部分负责引脚初始化与硬件控制：

- `pinMode(LED_BUILTIN, OUTPUT)`
  把板载 LED 对应的引脚配置为输出模式。

- `Bridge.begin()`
  初始化 Router Bridge 通信系统。

- `Bridge.provide(...)`
  注册可供 Python 调用的函数。

- `set_led_state(bool state)`
  根据 Python 传来的布尔值控制 LED 亮灭。

- 空的 `loop()`
  由于 LED 控制逻辑已经由 Python 驱动，所以 Arduino 主循环中不再额外处理任务。

## 结论

这个例程虽然简单，但非常适合作为以下主题的入门样例：

- Python 与 Arduino 协同工作
- Router Bridge 的基本调用模式
- 板载 LED 控制
- GPIO 输出的基本概念
- 软硬件分工设计

它说明了一个很重要的思路：**高层逻辑可以写在 Python 中，底层硬件动作交给 Arduino 处理，两者通过桥接接口配合完成任务。**
