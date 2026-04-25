// SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
//
// SPDX-License-Identifier: MPL-2.0

// LED 点阵控制库。
// 它负责向开发板上的 LED Matrix 写入图案和播放动画序列。
#include <Arduino_LED_Matrix.h>

// Router Bridge 库。
// 它负责让 Arduino 调用 Python 端已经注册好的函数。
#include <Arduino_RouterBridge.h>

// 自定义天气动画帧数据头文件。
// 里面定义了 sunny、cloudy、rainy、snowy、foggy 等动画序列。
#include "weather_frames.h"

// 当前查询天气所使用的城市名。
// 这个变量保存在 Arduino 端，因此设备烧录好后会按这个城市持续轮询天气。
String city = "Guangzhou";

// 创建 LED 点阵对象。
Arduino_LED_Matrix matrix;

void setup() {
  // 初始化 LED 点阵硬件。
  matrix.begin();

  // 清空点阵显示，避免上电后残留未知内容。
  matrix.clear();

  // 初始化 Router Bridge。
  // 没有这一步，Arduino 无法向 Python 发起远程调用。
  Bridge.begin();
}

void loop() {
  // 用于接收 Python 返回的天气分类结果。
  String weather_forecast;

  // 调用 Python 端提供的 get_weather_forecast 函数，并把 city 作为参数传过去。
  // result(weather_forecast) 会尝试把返回结果写入 weather_forecast。
  // ok 表示这次桥接调用是否成功。
  bool ok = Bridge.call("get_weather_forecast", city).result(weather_forecast);

  // 只有在调用成功时，才根据返回结果播放动画。
  if (ok) {
    // 晴天：加载 sunny 动画序列，并重复播放 10 次。
    if (weather_forecast == "sunny") {
      matrix.loadSequence(sunny);
      playRepeat(10);

    // 多云：加载 cloudy 动画序列，并重复播放 10 次。
    } else if (weather_forecast == "cloudy") {
      matrix.loadSequence(cloudy);
      playRepeat(10);

    // 雨天：动画重复次数更多，通常是为了让雨滴运动看起来更连续。
    } else if (weather_forecast == "rainy") {
      matrix.loadSequence(rainy);
      playRepeat(20);

    // 雪天：重复播放 10 次。
    } else if (weather_forecast == "snowy") {
      matrix.loadSequence(snowy);
      playRepeat(10);

    // 雾天：重复播放 5 次。
    } else if (weather_forecast == "foggy") {
      matrix.loadSequence(foggy);
      playRepeat(5);
    }
  }
}

// 为了避免每种天气都重复写同样的播放循环，
// 这里抽出一个通用函数来重复播放当前已经加载好的动画序列。
void playRepeat(int repeat_count) {
  for (int i = 0; i < repeat_count; i++) {
    matrix.playSequence();
  }
}
