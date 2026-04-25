# Weather forecast on LED matrix 中文版说明

## 项目名称

Weather forecast on LED matrix

## 项目概述

这个“天气预报显示系统”会从 `open-meteo.com` 服务获取实时天气信息，并将天气状态显示在 Arduino UNO Q 的 LED 点阵上。

它可以展示如下天气类别：

- 晴天 `sunny`
- 多云 `cloudy`
- 下雨 `rainy`
- 下雪 `snowy`
- 有雾 `foggy`

这些天气不会只显示静态图案，而是通过 LED 点阵上的动画效果表现出来，并且系统会自动周期性更新天气信息。

结合官方示例说明，这个项目常被描述为“约每 10 秒更新一次”。但从当前源码实现看，这个“10 秒”并不是通过显式 `delay(10000)` 或固定定时器写出来的，而是由不同动画序列的单帧时长和重复播放次数共同近似形成的刷新节奏。

## 功能说明

这个示例完成了下面几件事：

- 根据指定城市请求天气数据；
- 将天气服务返回的天气代码转换成更简单的天气类别；
- 按天气类别选择对应的 LED 点阵动画；
- 在开发板的 8 x 13 LED Matrix 上播放动画效果。

项目的职责划分如下：

- Python 端负责访问天气 API 并处理天气数据；
- Arduino 端负责轮询天气结果并驱动 LED 点阵显示；
- Router Bridge 负责在 Python 与 Arduino 之间传递参数和结果。

## 使用的 Bricks

这个例程使用了如下 Brick：

- `weather_forecast`

它的作用是：

- 从 `open-meteo.com` API 获取天气信息；
- 把技术性较强的天气代码转换成较简单的天气分类结果。

根据官方 Bricks 文档，还可以补充一点：

- Brick 不只是普通 Python 库的别名；
- 在 App Lab 中，Brick 会随 App 一起部署，并在 Linux 侧作为独立组件并行运行；
- 应用代码通过 Brick 暴露的 API 与其交互。

## 硬件与软件要求

### 硬件

- Arduino UNO Q 1 块
- USB-C 数据线 1 根（用于供电和程序运行）

### 软件

- Arduino App Lab

补充说明：

你也可以把 Arduino UNO Q 当作单板计算机（SBC）来使用。此时通常需要借助 USB-C 扩展坞，并外接鼠标、键盘和显示器。

## 如何使用该示例

1. 打开 `sketch.ino` 文件。
2. 修改城市变量，例如：

```cpp
String city = "Turin";
```

3. 运行应用。
4. 观察 LED 点阵。
5. 点阵会根据当前天气显示对应的动画效果，并按固定周期更新天气状态。

## 工作原理

项目运行后，会按如下流程执行：

### 1. Python 端调用天气服务

Python 中使用 `weather_forecast` Brick 获取天气：

```python
from arduino.app_bricks.weather_forecast import WeatherForecast

forecaster = WeatherForecast()
forecast = forecaster.get_forecast_by_city(city)
```

这部分的作用是：

- 根据城市名称查询天气；
- 与天气服务接口通信；
- 把复杂天气代码整理成更容易使用的结果对象。

## 2. Python 端处理城市参数并返回天气类别

Python 定义了一个供 Arduino 调用的函数：

```python
def get_weather_forecast(city: str) -> str:
    forecast = forecaster.get_forecast_by_city(city)
    print(f"Weather forecast for {city}: {forecast.description}")
    return forecast.category
```

这个函数做了三件事：

- 接收 Arduino 传来的城市名称；
- 获取该城市当前天气；
- 返回一个简化后的天气分类字符串。

返回值可能是：

- `sunny`
- `cloudy`
- `rainy`
- `snowy`
- `foggy`

## 3. 通过 Router Bridge 将 Python 函数暴露给 Arduino

Python 中通过下面这句注册桥接函数：

```python
Bridge.provide("get_weather_forecast", get_weather_forecast)
```

这表示 Arduino 以后可以通过 `get_weather_forecast` 这个名字远程调用 Python 函数。

## 4. Arduino 端携带城市参数发起请求

Arduino 端调用方式如下：

```cpp
String weather_forecast;
bool ok = Bridge.call("get_weather_forecast", city).result(weather_forecast);
```

这段代码表示：

- 把 `city` 作为参数传给 Python；
- 等待 Python 返回结果；
- 如果调用成功，就把天气分类结果保存到 `weather_forecast` 字符串中。

## 5. Arduino 端根据天气类别播放 LED 点阵动画

Arduino 会根据天气分类，选择不同动画序列：

```cpp
if (weather_forecast == "sunny") {
  matrix.loadSequence(sunny);
  playRepeat(10);
} else if (weather_forecast == "cloudy") {
  matrix.loadSequence(cloudy);
  playRepeat(10);
} else if (weather_forecast == "rainy") {
  matrix.loadSequence(rainy);
  playRepeat(20);
} else if (weather_forecast == "snowy") {
  matrix.loadSequence(snowy);
  playRepeat(10);
} else if (weather_forecast == "foggy") {
  matrix.loadSequence(foggy);
  playRepeat(5);
}
```

不同天气使用不同动画帧和不同重复次数，从而让视觉效果更符合天气特征：

- 雨天动画更快；
- 雪天动画更慢；
- 雾天动画较柔和；
- 晴天和多云动画较平稳。

## 高层数据流

整个项目的数据流可以概括为：

```text
Arduino 城市名 -> Python Bridge 函数 -> 天气 API -> 返回天气类别 -> Arduino 选择动画 -> LED 点阵播放
```

## 代码理解

### Python 后端 `main.py`

Python 部分负责天气数据获取：

- 创建 `WeatherForecast()` 实例；
- 接收 Arduino 传来的城市名称；
- 调用天气服务；
- 打印可读描述用于调试；
- 返回简化后的天气类别；
- 通过 `Bridge.provide(...)` 暴露给 Arduino 调用。

### Arduino 硬件端 `sketch.ino`

Arduino 部分负责显示控制：

- 初始化 LED 点阵；
- 初始化 Router Bridge；
- 在循环中请求指定城市的天气结果；
- 根据天气类别加载不同动画序列；
- 调用 `playRepeat()` 重复播放动画。

### 动画帧文件 `weather_frames.h`

这个文件保存了天气动画对应的帧数据。

它本质上是多个数组，每个数组代表一类天气的动画序列，例如：

- `sunny`
- `cloudy`
- `rainy`
- `snowy`
- `foggy`

数组中每一项都表示一帧画面及其显示时间，因此 Arduino 只需要加载对应序列并播放，就能在 LED 点阵上呈现动画。

从这一点也能解释为什么 README 中常说“每 10 秒更新一次”：一次天气查询后的显示阶段，本质上就是把某个动画序列按设定节奏播放若干轮，然后才进入下一轮天气请求。

## 结论

这个例程展示了一个比较完整的“云端数据 + 本地显示”的应用模式：

- Python 负责联网和数据处理；
- Arduino 负责本地硬件输出；
- LED 点阵负责结果可视化；
- Router Bridge 负责连接两个运行环境。

它比简单闪灯例程更接近真实应用，因为它同时涉及：

- 网络数据获取；
- 参数传递；
- 结果分类；
- 动画显示；
- 软硬件协同。
