# SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
#
# SPDX-License-Identifier: MPL-2.0

# 从 Arduino App Lab 提供的工具模块中导入运行时能力。
# 这里最关键的是：
# 1. App.run(...)：用于启动应用循环；
# 2. Bridge：用于从 Python 端调用 Arduino 端注册的函数。
from arduino.app_utils import *

# Python 标准库中的 time 模块用于实现定时等待。
# 这里通过 time.sleep(1) 让 LED 每隔 1 秒切换一次。
import time

# 用布尔变量记录当前“希望设置成什么状态”。
# False 可以理解为“当前目标状态为关闭”，
# 后续会在循环中不断取反，实现亮灭交替。
led_state = False


def loop():
    # 函数内部要修改模块级变量 led_state，
    # 因此必须声明它是全局变量。
    global led_state

    # 暂停 1 秒。
    # 这一步决定了 LED 闪烁的节奏。
    # 如果改成 0.5，LED 就会更快闪烁；
    # 如果改成 2，则会每 2 秒切换一次。
    time.sleep(1)

    # 将布尔值取反：
    # False -> True
    # True  -> False
    # 这样每执行一次 loop()，LED 目标状态都会翻转一次。
    led_state = not led_state

    # 通过 Router Bridge 调用 Arduino 端暴露出来的函数 set_led_state。
    # 第一个参数是远程函数名，必须与 Arduino 端 Bridge.provide(...) 注册的名字一致。
    # 第二个参数是传给 Arduino 的状态值。
    #
    # 这里并不是在 Python 里直接操作 GPIO，
    # 而是把“我要设置成什么状态”的意图发送给 Arduino，
    # 再由 Arduino 去执行真正的硬件控制。
    Bridge.call("set_led_state", led_state)


# 启动 App Lab 应用。
# user_loop=loop 表示运行时会反复调用上面定义的 loop() 函数，
# 从而形成一个持续执行的应用逻辑。
#
# 官方文档特别强调：App.run(...) 应放在 main.py 的末尾。
# 因为它会启动 App 运行时、Bridge 以及任何已导入的 Bricks。
# 如果把其他关键逻辑写在它后面，通常不会按预期执行。
App.run(user_loop=loop)
