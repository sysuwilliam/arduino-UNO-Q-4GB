# Arduino_RouterBridge 使用分析

## 1. 这个库是干什么的

`Arduino_RouterBridge` 是给 **Arduino UNO Q** 准备的一个通信封装库。  
它把 MCU 侧的 Arduino Sketch 和主机侧的 Router/App Lab 运行环境连接起来，让两边可以通过 **MessagePack RPC** 互相调用函数。

从官方 README 的描述看，这个库本质上是对 RPClite 的一层更易用封装，重点是：

- 提供一个全局 `Bridge` 对象
- 支持 MCU 主动调用主机侧方法
- 支持 MCU 暴露方法给主机侧调用
- 支持“线程不安全”和“线程安全”两种回调注册方式
- 提供 `Monitor` 作为调试输出通道
- 还封装了 `TCP client/server`、`UDP`、`HCI` 等能力入口

对 UNO Q 开发来说，最核心的部分其实就是：

- `Bridge.begin()`
- `Bridge.call(...)`
- `RpcCall.result(...)`
- `Bridge.notify(...)`
- `Bridge.provide(...)`
- `Bridge.provide_safe(...)`
- `Monitor.begin() / Monitor.print...`

---

## 2. 最常见的使用场景

在 UNO Q 的 App Lab 模型里，通常是：

- `sketch.ino` 跑在 MCU 上
- `main.py` 跑在 Linux/MPU 上
- 两边通过 Router Bridge 通信

典型分工：

- **MCU 侧**：控制 LED、GPIO、传感器、实时任务
- **Linux/Python 侧**：网络请求、AI、Web UI、数据处理

所以这个库最常见的两种用法是：

1. **MCU 调 Python**
   例如让 Python 去获取天气、访问 API、跑模型，再把结果返回给 MCU。

2. **Python 调 MCU**
   例如让 Python 控制 LED、引脚、电机、LED 矩阵等硬件。

---

## 3. 最小可用流程

### 3.1 头文件

```cpp
#include "Arduino_RouterBridge.h"
```

这个头文件会把几个常用模块一起带进来，包括：

- `bridge.h`
- `monitor.h`
- `tcp_client.h`
- `tcp_server.h`
- `hci.h`
- `udp_bridge.h`

### 3.2 初始化

最基本的初始化通常写在 `setup()` 里：

```cpp
void setup() {
    Bridge.begin();
}
```

从源码看，`Bridge.begin()` 主要做了这些事情：

- 初始化串口和底层传输
- 创建 RPC client / server
- 启动内部更新线程
- 调用 `$/reset` 清理旧的注册状态
- 尝试设置消息缓冲区大小

如果初始化失败，后续 RPC 调用通常都不会正常工作。

---

## 4. MCU 调主机侧方法

这是最常见的用法之一。

### 4.1 `Bridge.call(...)`

`Bridge.call(...)` 是一个**非阻塞创建调用对象**的接口，它返回一个 `RpcCall` 对象。

```cpp
RpcCall rpc = Bridge.call("add", 1.0, 2.0);
```

这一步只是创建调用对象，真正等待返回值通常发生在 `.result(...)`。

### 4.2 `result(...)`

```cpp
float sum;
if (Bridge.call("add", 1.0, 2.0).result(sum)) {
    // sum 有效
}
```

`result(...)` 的特点：

- 它是**阻塞等待**结果的
- 返回 `true` 表示 RPC 成功且结果类型匹配
- 返回 `false` 表示调用失败、参数不匹配、方法不存在，或结果类型不匹配
- 结果通过引用参数写回

### 4.3 错误处理

如果失败，可以读取错误信息：

```cpp
float value;
RpcCall rpc = Bridge.call("divide", 10.0, 0.0);

if (!rpc.result(value)) {
    int code = rpc.getErrorCode();
    String msg = rpc.getErrorMessage();
}
```

### 4.4 结果只能消费一次

这是这个库一个很重要的行为。

从源码看，`RpcCall.result(...)` 只能成功执行一次；再次调用会进入错误状态。  
因此一个 `RpcCall` 对象不要重复 `.result(...)`。

错误示意：

```cpp
RpcCall rpc = Bridge.call("hello");
String s;
rpc.result(s);   // 第一次
rpc.result(s);   // 第二次，不应这样做
```

### 4.5 类型必须匹配

RPC 返回什么类型，`result(...)` 就要用对应类型接。

例如对方返回 `bool`，你却用 `int` 去接，就可能失败：

```cpp
bool ok;
Bridge.call("is_ready").result(ok);   // 推荐
```

---

## 5. 不需要返回值时用 `notify(...)`

如果你只是发一个信号，不关心返回值，应该优先用：

```cpp
Bridge.notify("signal", 200);
```

而不是：

```cpp
Bridge.call("signal", 200);
```

原因很简单：

- `notify(...)` 是“只发送，不等结果”
- 语义更准确
- 开销更低
- 不会制造无意义的返回值等待

适合这些场景：

- 通知 Python 刷新状态
- 发送一次事件
- 触发日志、蜂鸣、简单动作

---

## 6. 把 MCU 函数暴露给主机侧

这就是 `provide(...)` 和 `provide_safe(...)` 的用途。

### 6.1 `Bridge.provide(...)`

```cpp
bool set_led(bool state) {
    digitalWrite(LED_BUILTIN, state ? LOW : HIGH);
    return true;
}

void setup() {
    pinMode(LED_BUILTIN, OUTPUT);
    Bridge.begin();
    Bridge.provide("set_led", set_led);
}
```

注册之后，主机侧就可以调用 `set_led` 这个 RPC 方法。

例如在 Python 侧：

```python
Bridge.call("set_led", True)
```

### 6.2 `Bridge.provide_safe(...)`

```cpp
String greet() {
    return String("Hello Friend");
}

void setup() {
    Bridge.begin();
    Bridge.provide_safe("greet", greet);
}
```

这个接口和 `provide(...)` 的区别，不在“功能”，而在**执行线程**。

---

## 7. `provide` 和 `provide_safe` 的区别

这是使用这个库时最需要搞清楚的点之一。

### 7.1 `provide(...)`

`provide(...)` 注册的回调，会在库内部更新线程处理。

优点：

- 响应直接
- 适合轻量逻辑

风险：

- 线程不安全
- 如果函数里访问了只能在主循环安全访问的资源，可能出问题

适合：

- 简单计算
- 简单状态读写
- 不依赖复杂 Arduino 主循环上下文的逻辑

### 7.2 `provide_safe(...)`

`provide_safe(...)` 注册的回调，会在主循环线程中执行。  
源码里通过内部 `update_safe()` 和 `__loopHook()` 机制把这些调用放回主循环上下文处理。

优点：

- 更安全
- 更适合操作对上下文敏感的硬件逻辑

适合：

- GPIO
- 外设状态更新
- 需要放在主循环上下文的代码
- 不想承担多线程访问风险的接口

### 7.3 实际建议

如果你不确定某个导出函数该不该用 `provide_safe(...)`，**优先用 `provide_safe(...)`**。  
尤其是涉及：

- `digitalWrite / analogWrite`
- LED 矩阵
- 传感器读写
- 共享全局状态
- 和别的循环逻辑并发访问同一资源

---

## 8. `Monitor` 的用途

这个库还提供了一个 `Monitor` 对象，接口风格接近 Arduino 的 `Serial`。

### 8.1 初始化

```cpp
void setup() {
    Bridge.begin();
    Monitor.begin();
}
```

### 8.2 输出日志

```cpp
Monitor.println("Bridge started");
Monitor.print("Value: ");
Monitor.println(value);
```

`Monitor` 的作用可以理解为：

- 通过 Router 通道把 MCU 日志送到主机侧
- 在 UNO Q 这种双端架构下充当调试输出

对于调试 RPC 是否注册成功、调用是否失败，非常有用。

---

## 9. 一个最小双向示例

### 9.1 方案 A：主机侧控制 MCU LED

MCU 代码：

```cpp
#include "Arduino_RouterBridge.h"

void set_led_state(bool state) {
    digitalWrite(LED_BUILTIN, state ? LOW : HIGH);
}

void setup() {
    pinMode(LED_BUILTIN, OUTPUT);
    Bridge.begin();
    Bridge.provide_safe("set_led_state", set_led_state);
}

void loop() {
}
```

Python 侧：

```python
from arduino.app_utils import *
import time

state = False

def loop():
    global state
    state = not state
    Bridge.call("set_led_state", state)
    time.sleep(1)

App.run(user_loop=loop)
```

### 9.2 方案 B：MCU 请求 Python 获取数据

MCU 代码：

```cpp
#include "Arduino_RouterBridge.h"

void setup() {
    Bridge.begin();
}

void loop() {
    String weather;
    if (Bridge.call("get_weather", "Guangzhou").result(weather)) {
        // 使用 weather
    }
}
```

Python 侧：

```python
from arduino.app_utils import *

def get_weather(city: str) -> str:
    return "sunny"

Bridge.provide("get_weather", get_weather)

App.run()
```

这两种模式，基本覆盖了 UNO Q 上最常见的 Bridge 开发。

---

## 10. 这个库的几个重要行为细节

### 10.1 `Bridge.call(...)` 返回的是异步调用对象

也就是说：

```cpp
RpcCall rpc = Bridge.call("method", arg1, arg2);
```

这一步本身不是“马上拿到结果”，而是创建一个待执行/待取结果的调用对象。

### 10.2 `RpcCall` 析构时会兜底执行 `result()`

源码里析构函数会调用无参 `result()`。  
这意味着如果你写了：

```cpp
Bridge.call("method", 123);
```

而没有接收结果对象，也没有显式 `.result(...)`，它可能会按“无返回值调用”路径被处理。

因此：

- **有返回值需求**：一定显式 `.result(var)`
- **无返回值需求**：直接用 `notify(...)`

### 10.3 `if (Bridge.call(...))` 这种写法要谨慎

README 明确提醒这类隐式 `bool` 转换要谨慎。

```cpp
if (Bridge.call("send_greeting", "Hello")) {
}
```

这种写法本质上会走“期望 nil/void 返回”的逻辑。  
如果对方实际返回了别的类型，语义就不清晰。

工程上建议：

- 想拿结果，就 `.result(...)`
- 不想拿结果，就 `notify(...)`

不要过度依赖隐式布尔转换。

---

## 11. 在 UNO Q / App Lab 项目里的推荐写法

### 11.1 初始化顺序

推荐：

```cpp
void setup() {
    pinMode(...);
    Bridge.begin();
    Monitor.begin();
    Bridge.provide_safe(...);
}
```

### 11.2 导出给 Python 的硬件接口

推荐优先 `provide_safe(...)`，尤其是硬件控制接口：

```cpp
Bridge.provide_safe("set_pwm", set_pwm);
Bridge.provide_safe("set_matrix_frame", set_matrix_frame);
```

### 11.3 MCU 调 Python

有返回值：

```cpp
String text;
if (Bridge.call("get_text").result(text)) {
}
```

无返回值：

```cpp
Bridge.notify("event_happened", 123);
```

### 11.4 RPC 方法命名

推荐用清晰、稳定、动作导向的名字：

- `set_led_state`
- `read_sensor`
- `get_weather_forecast`
- `display_frame`
- `start_capture`

避免：

- `doit`
- `test1`
- `abc`

---

## 12. 常见问题和踩坑点

### 12.1 忘记 `Bridge.begin()`

这会导致：

- `call` 失败
- `provide` 无法注册
- `Monitor` 也不能正常工作

### 12.2 返回值类型不匹配

例如远端返回 `bool`，本地却用 `String` 接，会导致 `result(...)` 失败。

### 12.3 重复读取同一个 `RpcCall` 的结果

同一个调用对象不要重复 `.result(...)`。

### 12.4 本该 `notify` 却用了 `call`

如果根本不需要返回值，直接 `notify(...)` 更合理。

### 12.5 在 `provide(...)` 里直接做高风险硬件操作

如果遇到莫名其妙的并发问题，优先改成 `provide_safe(...)`。

### 12.6 长耗时逻辑阻塞

无论是 `provide` 还是 `provide_safe`，都不建议在回调里塞很长时间的阻塞逻辑。  
更合理的方式通常是：

- 回调只修改状态
- 真正耗时工作放到 `loop()` 中逐步执行

---

## 13. 一句话总结

`Arduino_RouterBridge` 就是 **UNO Q 上 MCU 与主机侧 App/Python 之间的 RPC 桥**。  
实际开发时记住下面这套就够用了：

- `Bridge.begin()` 初始化
- `Bridge.call(...).result(...)` 做“有返回值”的远程调用
- `Bridge.notify(...)` 做“无返回值”的事件通知
- `Bridge.provide(...)` 导出普通 RPC
- `Bridge.provide_safe(...)` 导出更安全的主循环上下文 RPC
- `Monitor.begin()` + `Monitor.println(...)` 做调试

---

## 14. 参考资料

- Arduino_RouterBridge 仓库  
  https://github.com/arduino-libraries/Arduino_RouterBridge

- README  
  https://raw.githubusercontent.com/arduino-libraries/Arduino_RouterBridge/main/README.md

- 主头文件 `Arduino_RouterBridge.h`  
  https://raw.githubusercontent.com/arduino-libraries/Arduino_RouterBridge/main/src/Arduino_RouterBridge.h

- 核心实现 `bridge.h`  
  https://raw.githubusercontent.com/arduino-libraries/Arduino_RouterBridge/main/src/bridge.h

- 调试输出实现 `monitor.h`  
  https://raw.githubusercontent.com/arduino-libraries/Arduino_RouterBridge/main/src/monitor.h

- 官方测试示例 `examples/test/test.ino`  
  https://raw.githubusercontent.com/arduino-libraries/Arduino_RouterBridge/main/examples/test/test.ino

- 官方 TCP client 示例 `examples/client/client.ino`  
  https://raw.githubusercontent.com/arduino-libraries/Arduino_RouterBridge/main/examples/client/client.ino
