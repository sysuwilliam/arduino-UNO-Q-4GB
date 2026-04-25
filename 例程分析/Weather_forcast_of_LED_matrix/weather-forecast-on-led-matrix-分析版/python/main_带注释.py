# SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
#
# SPDX-License-Identifier: MPL-2.0

# 导入天气预报 Brick。
# 这个 Brick 封装了与天气服务的通信细节，
# 让我们不需要自己手写 HTTP 请求、JSON 解析和天气代码映射。
from arduino.app_bricks.weather_forecast import WeatherForecast

# 导入 Arduino App Lab 运行时工具。
# 其中最关键的是：
# 1. Bridge：用于把 Python 函数暴露给 Arduino 调用；
# 2. App.run()：用于启动应用运行时。
#
# 官方文档说明，Bricks 在 UNO Q 上会与 App 并行启动，
# 有些 Brick 甚至可能以独立进程或容器方式运行。
# 因此这里导入并实例化的 WeatherForecast，不应简单理解为“普通本地函数库”。
from arduino.app_utils import *

# 创建天气预报对象。
# 这个对象会负责根据城市名称去查询天气，
# 并返回一个包含描述和分类的结果对象。
forecaster = WeatherForecast()


def get_weather_forecast(city: str) -> str:
    # 根据传入的城市名称查询天气。
    # city 这个参数来自 Arduino 端的 Bridge.call(...) 调用。
    forecast = forecaster.get_forecast_by_city(city)

    # 打印人类可读的天气描述，方便调试和观察程序运行结果。
    # 例如输出可能类似：
    # Weather forecast for Guangzhou: Partly cloudy
    print(f"Weather forecast for {city}: {forecast.description}")

    # 返回一个简化后的天气类别字符串。
    # Arduino 端不需要完整天气数据，只需要简单类别来选择动画。
    # 常见类别包括：
    # sunny / cloudy / rainy / snowy / foggy
    return forecast.category


# 向 Router Bridge 注册一个供 Arduino 调用的远程函数。
# 左边的字符串 "get_weather_forecast" 是对外暴露的接口名，
# 右边是当前 Python 文件中真正要执行的函数。
Bridge.provide("get_weather_forecast", get_weather_forecast)

# 启动 App Lab 运行时。
# 由于本项目不需要像上一个例程那样反复执行 Python loop，
# 所以这里只启动运行时并等待 Arduino 通过 Bridge 发起调用。
#
# 官方文档特别强调：App.run() 应该放在 main.py 末尾，
# 因为它会启动 App 本身、Bridge 和所有已导入的 Bricks。
App.run()
