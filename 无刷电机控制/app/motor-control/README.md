# Brushless Motor Control

这是一个用于 Arduino UNO Q 的 App Lab 项目，用来通过 SimpleFOCmini 驱动板控制 1 个无刷电机。

当前程序运行在 UNO Q 的 MCU 侧 `sketch/sketch.ino` 中，使用 SimpleFOC 做闭环角度控制。Python 侧 `python/main.py` 负责启动 Web UI、接收网页调参命令，并通过 RouterBridge 调用 MCU 侧接口。实时 FOC 控制仍然只放在 MCU 侧。

## 当前任务

程序完成的任务：

- 通过 UNO Q 的 `D3`、`D5`、`D6` 输出三路 PWM 到 SimpleFOCmini 驱动板。
- 通过 UNO Q 的 `D8` 控制驱动板 `EN` 使能脚。
- 通过 I2C 读取 AS5600 磁编码器角度。
- 使用 SimpleFOC 的 `MotionControlType::angle` 做闭环位置控制。
- 通过串口命令或 Web UI 设置目标角度，角度单位为弧度。
- 通过 Web UI 实时修改关键参数并查看遥测波形。

## 接线

当前代码对应的接线如下：

| 模块 | 引脚 | 连接 |
|---|---|---|
| SimpleFOCmini | PWM1/PWM2/PWM3 | UNO Q `D3` / `D5` / `D6` |
| SimpleFOCmini | EN | UNO Q `D8` |
| SimpleFOCmini | VIN/GND | 电源板 `10V` / `GND` |
| SimpleFOCmini | VCC/GND | 电源板 `3V3` / `GND` |
| AS5600 编码器 | SDA/SCL | UNO Q `SDA` / `SCL` |
| AS5600 编码器 | VCC/GND | 电源板 `3V3` / `GND` |
| 无刷电机 | 三相线 | SimpleFOCmini 三相输出 |
| UNO Q | GND | 电源板 `GND` |

所有模块必须共地。

## 关键参数

当前代码中的关键参数：

```cpp
constexpr int PWM_U_PIN = 3;
constexpr int PWM_V_PIN = 5;
constexpr int PWM_W_PIN = 6;
constexpr int ENABLE_PIN = 8;

constexpr float POWER_SUPPLY_VOLTAGE = 10.0f;
constexpr float STARTUP_VOLTAGE_LIMIT = 1.5f;
constexpr float STARTUP_VELOCITY_LIMIT = 10.0f;
constexpr int MOTOR_POLE_PAIRS = 7;
```

首次测试时 `motor.voltage_limit` 被限制为 `1.5V`，这是为了降低电机抖动、发热或接线错误时的风险。确认电机运行稳定后，再逐步提高限压。

## 运行方式

1. 在 App Lab 中安装 sketch library：`Simple FOC`。
2. 确认 sketch library 中也包含 `Arduino_RouterBridge`；当前 `sketch/sketch.yaml` 已经写入依赖。
3. 确认电机供电、逻辑供电、编码器供电和共地接线正确。
4. 点击 App Lab 右上角 `Run`。
5. App Lab 会启动 Web UI，通常可以通过浏览器访问 `<board-name>.local:7000` 或板子的 IP 地址端口 `7000`。
6. 也可以打开 MCU 串口监视器，波特率设置为 `115200`，继续使用串口命令。

示例命令：

```text
T0
T1.57
T3.14
```

角度单位是弧度：

$$
1.57 \text{ rad} \approx 90^\circ
$$

$$
3.14 \text{ rad} \approx 180^\circ
$$

## Web UI 功能

Web UI 位于：

```text
assets/index.html
assets/app.js
assets/style.css
```

网页当前提供：

- 目标角度滑条和数字输入，单位支持 `rad` 和 `deg`。
- `Hold` 按钮：把当前电机角度设置为新的目标角度。
- `Zero` 按钮：目标角度设置为 `0 rad`。
- `Enable/Disable` 按钮：启用或禁用电机输出。
- `voltage_limit` 实时调节。
- `velocity_limit` 实时调节。
- `P_angle` 实时调节。
- 速度环 `P/I/D` 实时调节。
- 实时波形图：显示目标角度、当前角度和角度误差。
- 状态卡片：显示当前角度、目标角度、误差、速度、限压和电机使能状态。
- Auto Tune：执行小阶跃测试，自动扫描安全候选参数并推荐表现最好的一组。
- Auto Tune 可选继续调节：速度环 `D`、`velocity_limit`、`voltage_limit`。

网页与 MCU 的数据流：

```text
Web UI
  -> Socket.IO
  -> python/main.py
  -> RouterBridge
  -> sketch/sketch.ino
  -> SimpleFOC
```

MCU 侧保留高频实时控制：

```cpp
motor.loopFOC();
motor.move(target_angle);
```

Python 侧每 `50ms` 读取一次 MCU 遥测数据，并推送给 Web UI 画波形。

## Auto Tune 自动调参

Auto Tune 在 Python 侧实现，不抓取网页 DOM，而是直接读取 MCU 遥测数据。这比爬取 `http://<board-ip>:7000` 页面更稳定，也更快。

当前自动调参流程：

1. 在网页中设置 `Step rad`、`Max voltage` 和 `Max velocity`。
2. 点击 `Auto Tune`。
3. Python 后端记录当前参数和当前角度。
4. 后端把电机目标设为当前角度，进入短暂稳定阶段。
5. 后端按多阶段策略搜索候选参数。
6. 每组候选参数都会执行正反两个大阶跃，以及正反两个小角度阶跃：

```text
current angle -> current angle + Step rad
current angle -> current angle - Step rad
current angle -> current angle + small step
current angle -> current angle - small step
```

7. 程序记录阶跃响应，并计算：

- settling time：进入误差阈值后的稳定时间。
- overshoot：超调量。
- steady error：尾段平均稳态误差。
- jitter：尾段角度抖动。
- small steady error：小角度阶跃尾段平均误差。
- small jitter：小角度阶跃尾段抖动。
- small final error：小角度阶跃最后一刻仍剩下的误差。
- score：综合评分，越低越好。

8. 如果勾选了 `Tune D after PID`，程序会在基础 `P/I` 参数确定后继续扫描很小的速度环 `D` 值。
9. 如果勾选了 `Tune velocity limit`，程序会在安全范围内比较不同 `velocity_limit`。
10. 如果勾选了 `Tune voltage limit`，程序会在不超过 `Max voltage` 的范围内比较不同 `voltage_limit`。
11. 测试结束后，程序自动应用确认阶段通过的推荐参数，包括推荐的 `D`、限速和限压。

当前 Auto Tune 搜索策略：

| 阶段 | 作用 |
|---|---|
| `coarse_angle` | 粗扫 `P_angle`，先找到大致合适的角度环增益 |
| `fine_angle` | 围绕粗扫最佳结果细扫 `P_angle` |
| `velocity_pi` | 固定最佳 `P_angle`，扫描速度环 `P/I` 组合 |
| `velocity_d` | 可选阶段，固定 `P_angle` 和速度环 `P/I`，只扫描很小的速度环 `D` |
| `velocity_limit` | 可选阶段，在 `8 rad/s ~ Max velocity` 内寻找更合适的限速 |
| `voltage_limit` | 可选阶段，在 `0.5V ~ Max voltage` 内寻找更合适的限压 |
| `confirm` | 对最终推荐参数做确认测试 |

默认阶段顺序是：

```text
coarse_angle -> fine_angle -> velocity_pi -> confirm
```

如果三个可选项都勾选，阶段顺序变为：

```text
coarse_angle -> fine_angle -> velocity_pi -> velocity_d -> velocity_limit -> voltage_limit -> confirm
```

评分倾向：

- 优先排除明显过调、发散、速度尖峰和振荡的候选。
- 对小角度阶跃的最终误差、稳态误差和尾段抖动施加更高权重。
- 小角度保持误差超过阈值的候选会被淘汰，即使它的大角度响应很快。
- 在满足小角度保持稳定的前提下，再选择响应更快的参数。

默认安全边界：

| 参数 | 范围 |
|---|---|
| `Step rad` | `0.1 ~ 1.0 rad` |
| `Max voltage` | `0.5 ~ 4.0 V` |
| `Max velocity` | `8 ~ 35 rad/s` |
| 基础 Auto Tune `velocity_limit` | `min(15 rad/s, Max velocity)` |
| 可选 Auto Tune `velocity_limit` | `8 rad/s ~ Max velocity` |

当前候选参数主要扫描：

- `P_angle`
- `PID_velocity.P`
- `PID_velocity.I`
- `PID_velocity.D`，仅在勾选 `Tune D after PID` 后扫描，候选值保持在很小范围内
- `voltage_limit`，仅在勾选 `Tune voltage limit` 后扫描，永远不超过 `Max voltage`
- `velocity_limit`，仅在勾选 `Tune velocity limit` 后扫描，永远不超过 `Max velocity`

如果点击 `Stop Tune`，程序会停止测试并恢复开始前的参数。

如果想手动应用推荐参数，可以点击 `Apply Best`。

调参建议：

- 先不勾选可选项，跑一次基础 Auto Tune，确认电机方向正确且没有明显撞限位或发热。
- 如果基础结果响应慢或小角度保持不好，再勾选 `Tune D after PID` 测试小 `D` 值。
- `Tune velocity limit` 会影响响应速度和速度尖峰；限速太低会慢，太高可能更容易超调和抖动。
- `Tune voltage limit` 会影响可用力矩；限压太低可能拖不动或残余误差大，太高可能更容易过冲、发热或抖动。
- 每个候选仍会经过早停判断，出现明显过调、发散、速度尖峰或振荡时会提前跳过。

## 注意事项

- `10V` 电机供电只能接驱动板 `VIN`，不要接到 UNO Q 或编码器的 `VCC`。
- 第一次运行时建议电源限流，并让电机空载测试。
- 如果电机抖动、不转或发热，先停止运行，检查三相线顺序、编码器方向、磁铁安装位置和极对数。
- 如果编译提示找不到 `SimpleFOC.h`，说明没有安装 `Simple FOC` 库。
- 如果 Web UI 无法打开，确认 `app.yaml` 中存在 `arduino:web_ui` brick，并确认 App Lab 运行在支持网络访问的模式。
- 如果 Web UI 显示遥测失败，优先检查 MCU 是否成功编译运行、`Arduino_RouterBridge` 是否安装、以及 `sketch.ino` 是否打印 `Motor ready.`。
- Auto Tune 会让电机自动执行多个小角度阶跃。测试时应让电机空载、远离机械限位，并确保可以随时断电。

## 维护约定

以后每次修改 `sketch/sketch.ino`、接线方式、控制模式或关键参数时，都要同步更新这个 README。
