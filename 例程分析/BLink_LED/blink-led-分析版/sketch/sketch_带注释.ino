// SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
//
// SPDX-License-Identifier: MPL-2.0

// 引入 Router Bridge 库。
// 这个库负责建立 Arduino 与 Python 运行环境之间的桥接通信能力，
// 使得 Python 可以调用 Arduino 中注册的函数。
#include "Arduino_RouterBridge.h"

// 这是 Arduino 的初始化函数，设备上电或复位后只执行一次。
void setup() {
    // 将板载 LED 所在的引脚设置为输出模式。
    // LED_BUILTIN 是 Arduino 提供的板级常量，
    // 它会映射到该开发板上板载 LED 对应的实际引脚号。
    pinMode(LED_BUILTIN, OUTPUT);

    // 初始化 Router Bridge。
    // 没有这一步，Python 与 Arduino 之间的桥接调用无法建立。
    Bridge.begin();

    // 向桥接系统注册一个可远程调用的函数。
    //
    // 第一个参数 "set_led_state" 是对外暴露的函数名，
    // Python 端会通过这个字符串来发起调用。
    //
    // 第二个参数 set_led_state 是本地真正执行的 C++ 函数名。
    // 一旦 Python 调用 Bridge.call("set_led_state", ...)，
    // Router Bridge 就会把请求转发到这里定义的函数。
    Bridge.provide("set_led_state", set_led_state);
}

// Arduino 主循环函数。
// 在这个例程中它保持为空，
// 因为 LED 的节奏控制逻辑全部放在 Python 端完成。
// Arduino 这里只扮演“硬件执行端”的角色：
// 收到 Python 的调用后，执行对应的引脚输出动作即可。
void loop() {
}

// 这是提供给 Python 远程调用的函数。
// 参数 state 表示 Python 希望 LED 处于什么逻辑状态。
void set_led_state(bool state) {
    // 这里特别关键：板载 LED 采用的是反相控制逻辑。
    //
    // 常见直觉是：
    // HIGH -> 亮
    // LOW  -> 灭
    //
    // 但本例不是这样，而是：
    // LOW  -> 亮
    // HIGH -> 灭
    //
    // 因此这里写成：
    // state 为 true  时输出 LOW，点亮 LED；
    // state 为 false 时输出 HIGH，熄灭 LED。
    //
    // 这通常和板载 LED 的硬件接法有关，不是程序写错了。
    digitalWrite(LED_BUILTIN, state ? LOW : HIGH);
}
