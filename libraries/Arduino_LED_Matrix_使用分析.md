# Arduino_LED_Matrix 使用分析

## 1. 这个库是干什么的

`Arduino_LED_Matrix` 是 Arduino 官方生态中用于控制板载 LED 点阵的库。  
在你现在这个项目里，它主要用于驱动 **Arduino UNO Q** 的 **8 x 13 蓝色 LED 矩阵**。

从你仓库里的现有例程来看，这个库承担了三类核心工作：

- 初始化 LED 点阵硬件
- 直接把一帧像素数据刷到屏幕上
- 加载并播放多帧动画序列

如果只是想在 UNO Q 的板载 LED 阵列上显示图案、动画、亮度变化，通常先用这个库就够了。

---

## 2. 在 UNO Q 项目里的定位

你这个项目里已经有两种典型用法：

1. **动画序列播放**
   在天气预报示例里，通过 `loadSequence(...)` + `playSequence()` 播放天气动画。

2. **手工帧缓冲绘制**
   在 `LED_Matrix_Rectangle` 例程里，手动维护一个 `frame[]` 数组，再用 `draw(frame)` 把内容送到矩阵。

这说明 `Arduino_LED_Matrix` 本身偏底层显示控制，不负责：

- 网络请求
- 天气获取
- 业务逻辑
- Python/Bridge 通信

它只关心：**这个时刻 LED 阵列应该亮成什么样子。**

---

## 3. 最基本的使用流程

### 3.1 头文件

```cpp
#include <Arduino_LED_Matrix.h>
```

### 3.2 创建对象

你仓库现有示例使用的是：

```cpp
Arduino_LED_Matrix matrix;
```

有些别的官方资料或核心版本里，也可能看到类似：

```cpp
ArduinoLEDMatrix matrix;
```

这通常是不同核心版本或类名包装差异。  
对你当前 UNO Q 项目来说，**以你现有示例能编译通过的写法为准**，也就是：

```cpp
Arduino_LED_Matrix matrix;
```

### 3.3 初始化

```cpp
void setup() {
    matrix.begin();
}
```

这是必须的。没有 `begin()`，后续显示操作都不可靠。

如果你希望开机后先清空显示，可以接着写：

```cpp
matrix.clear();
```

---

## 4. 最常见的三种使用方式

## 4.1 方式一：直接显示单帧

这是最适合做“自己画像素”的方式。

你的 `LED_Matrix_Rectangle` 例程就是这种思路：

```cpp
constexpr uint8_t MATRIX_ROWS = 8;
constexpr uint8_t MATRIX_COLS = 13;
constexpr uint16_t FRAME_SIZE = MATRIX_ROWS * MATRIX_COLS;

uint8_t frame[FRAME_SIZE];

void showFrame() {
    matrix.draw(frame);
}
```

这里的核心点是：

- 点阵是 **8 行 x 13 列**
- `frame` 本质上是一个长度为 `104` 的数组
- 每个元素表示一个像素亮度
- 然后通过 `matrix.draw(frame)` 一次性显示出来

### 推荐的索引方式

```cpp
uint16_t pixelIndex(uint8_t row, uint8_t col) {
    return row * MATRIX_COLS + col;
}
```

这样 `(row, col)` 就能映射到一维数组：

```cpp
frame[pixelIndex(2, 5)] = 255;
```

### 一个最小示例

```cpp
#include <Arduino_LED_Matrix.h>

constexpr uint8_t MATRIX_ROWS = 8;
constexpr uint8_t MATRIX_COLS = 13;
constexpr uint16_t FRAME_SIZE = MATRIX_ROWS * MATRIX_COLS;

Arduino_LED_Matrix matrix;
uint8_t frame[FRAME_SIZE];

uint16_t idx(uint8_t row, uint8_t col) {
    return row * MATRIX_COLS + col;
}

void clearFrame() {
    for (uint16_t i = 0; i < FRAME_SIZE; ++i) {
        frame[i] = 0;
    }
}

void setup() {
    matrix.begin();
    matrix.setGrayscaleBits(8);

    clearFrame();
    frame[idx(3, 6)] = 255;
    matrix.draw(frame);
}

void loop() {
}
```

这个例子会点亮一个像素。

---

## 4.2 方式二：加载并播放动画序列

这是你仓库里天气示例使用的方式。

示例结构是：

```cpp
matrix.loadSequence(sunny);
matrix.playSequence();
```

如果希望多播几次：

```cpp
void playRepeat(int repeat_count) {
    for (int i = 0; i < repeat_count; i++) {
        matrix.playSequence();
    }
}
```

### 这种方式适合什么

- 已经提前定义好动画帧
- 不想每次手动改像素数组
- 想表达“图标/动作/天气动画/状态动画”

### 你的项目中的实际例子

天气预报示例里根据 Python 返回的字符串切换动画：

```cpp
if (weather_forecast == "sunny") {
    matrix.loadSequence(sunny);
    playRepeat(10);
} else if (weather_forecast == "cloudy") {
    matrix.loadSequence(cloudy);
    playRepeat(10);
}
```

也就是说：

- `loadSequence(...)` 负责装载一组帧
- `playSequence()` 负责把装进去的内容实际播放出来

---

## 4.3 方式三：配合 ArduinoGraphics 做文字和图形

如果你想做更高层的绘图，比如：

- 画线
- 画矩形
- 输出文字
- 滚动文字

就经常会和 `ArduinoGraphics` 配合使用。

关键点是：  
**如果要使用 ArduinoGraphics 的 API，要先包含 `ArduinoGraphics.h`，再包含 `Arduino_LED_Matrix.h`。**

官方 issue 中的示例明确写了这一点：

```cpp
#include "ArduinoGraphics.h"
#include "Arduino_LED_Matrix.h"
```

然后可以这样写：

```cpp
matrix.beginDraw();
matrix.stroke(0xFFFFFFFF);
matrix.line(0, 0, 11, 0);
matrix.endDraw();
```

滚动文本示例：

```cpp
matrix.beginDraw();
matrix.textScrollSpeed(80);
matrix.textFont(Font_5x7);
matrix.beginText(0, 1, 0xFFFFFF);
matrix.println("Hello");
matrix.endText(SCROLL_LEFT);
matrix.endDraw();
```

### 结论

所以你的上一个问题可以更准确地回答为：

- **只做像素帧和动画：不一定需要 `ArduinoGraphics`**
- **要做文字/几何图形/滚动文本：通常要配合 `ArduinoGraphics`**

---

## 5. `draw(frame)` 的数据模型

这是这个库最值得搞清楚的地方。

### 5.1 矩阵尺寸

在你项目里的 UNO Q 示例中，尺寸是：

- 行数：`8`
- 列数：`13`

所以一帧大小就是：

```cpp
8 * 13 = 104
```

### 5.2 帧缓冲类型

你现在的例程使用：

```cpp
uint8_t frame[104];
```

这说明每个像素至少可以用一个字节表示亮度。

### 5.3 亮度范围

从 `LED_Matrix_Rectangle` 示例看，亮度值直接写 `255`，并且设置了：

```cpp
matrix.setGrayscaleBits(8);
```

这表示当前示例按 **8 位灰度** 使用，也就是常见的：

- `0` = 熄灭
- `255` = 最亮

中间值则表示更低亮度。

### 5.4 坐标映射

你手动绘图时，推荐始终显式写一个坐标映射函数：

```cpp
uint16_t pixelIndex(uint8_t row, uint8_t col) {
    return row * 13 + col;
}
```

这样不容易把行列关系搞乱。

---

## 6. `setGrayscaleBits(...)` 的作用

在你的矩形例程里有这一句：

```cpp
matrix.setGrayscaleBits(8);
```

这说明该库支持灰度控制，而不仅仅是“亮/灭”。

工程上可以这样理解：

- 灰度位数越高，亮度层次越细
- 代价通常是刷新和底层调制更复杂

对 UNO Q 上的简单图标、动画项目，`8` 位灰度已经很够用了。  
如果你后面只是做状态指示，也可以一直用满亮 `255`，先不折腾更细的亮度层次。

---

## 7. `clear()` 的理解

`matrix.clear()` 的语义是“清除当前显示内容”。  
但要注意一个实践细节：

- 它更像是在清理当前显示/缓冲状态
- 如果你后面又把旧帧重新 `draw()` 或重新开始某个文本/动画流程，旧内容可能又会出现

Arduino 官方核心仓库里曾经有过 `clear()` 相关问题，后来在核心版本更新中修复过清除缓冲区的问题。  
因此如果你遇到“明明 clear 了但残影又回来”的情况，需要同时检查：

- 当前 Arduino core 版本
- 你是否又重新显示了旧缓冲区
- 是否在 `beginDraw()/endDraw()` 或文本滚动状态机里残留旧内容

工程建议：

- 纯帧绘制时，自己先清空 `frame[]`，再 `draw(frame)`
- 文本/图形绘制时，必要时显式重新开始一次绘制流程

---

## 8. 在 UNO Q 上的推荐使用方式

### 8.1 做固定图案或简单 UI

优先用 `draw(frame)`。

适合：

- 电量图标
- 连接状态
- 方向箭头
- 简单几何图形

### 8.2 做重复动画

优先用 `loadSequence(...)` + `playSequence()`。

适合：

- 天气动画
- 表情动画
- 启动动画
- 等待动画

### 8.3 做文字或滚动提示

优先考虑 `ArduinoGraphics + Arduino_LED_Matrix` 组合。

适合：

- 显示短文本
- 滚动提示
- 调试信息

---

## 9. 和 RouterBridge 结合时的典型模式

在 UNO Q + App Lab 架构里，常见做法不是让 Python 直接控制每个像素，而是：

1. Python 负责高层逻辑
   例如天气、AI 识别、网络状态、用户输入

2. MCU 负责最终显示
   例如根据 Python 返回的状态切换动画或绘制图案

比如你仓库里的天气示例：

- Python 返回 `"sunny"`、`"rainy"` 这类业务结果
- MCU 收到结果后调用 `matrix.loadSequence(...)`

这是很好的分层方式，因为：

- Python 不必知道矩阵帧细节
- MCU 不必承担网络逻辑
- 显示逻辑更集中

---

## 10. 一个推荐的最小模板

### 10.1 纯帧绘制模板

```cpp
#include <Arduino_LED_Matrix.h>

constexpr uint8_t ROWS = 8;
constexpr uint8_t COLS = 13;
constexpr uint16_t FRAME_SIZE = ROWS * COLS;

Arduino_LED_Matrix matrix;
uint8_t frame[FRAME_SIZE];

uint16_t idx(uint8_t row, uint8_t col) {
    return row * COLS + col;
}

void clearFrame() {
    for (uint16_t i = 0; i < FRAME_SIZE; ++i) {
        frame[i] = 0;
    }
}

void setup() {
    matrix.begin();
    matrix.setGrayscaleBits(8);
}

void loop() {
    clearFrame();
    frame[idx(3, 6)] = 255;
    matrix.draw(frame);
    delay(500);

    clearFrame();
    matrix.draw(frame);
    delay(500);
}
```

### 10.2 动画序列模板

```cpp
#include <Arduino_LED_Matrix.h>
#include "my_frames.h"

Arduino_LED_Matrix matrix;

void setup() {
    matrix.begin();
    matrix.clear();
    matrix.loadSequence(my_animation);
}

void loop() {
    matrix.playSequence();
}
```

### 10.3 ArduinoGraphics 文本模板

```cpp
#include <ArduinoGraphics.h>
#include <Arduino_LED_Matrix.h>

Arduino_LED_Matrix matrix;

void setup() {
    matrix.begin();

    matrix.beginDraw();
    matrix.textScrollSpeed(80);
    matrix.textFont(Font_5x7);
    matrix.beginText(0, 1, 0xFFFFFF);
    matrix.println("HELLO");
    matrix.endText(SCROLL_LEFT);
    matrix.endDraw();
}

void loop() {
}
```

---

## 11. 常见问题和踩坑点

### 11.1 忘记 `matrix.begin()`

这是第一类问题。没初始化，显示往往就不对。

### 11.2 行列顺序写反

UNO Q 的矩阵是 `8 x 13`，建议始终用：

```cpp
row * COLS + col
```

不要手写魔法数字。

### 11.3 忘记清空旧帧

如果你使用 `draw(frame)`，一定要管理好自己的 `frame[]`。  
最稳妥的方式就是每次先清空，再重画。

### 11.4 把 `ArduinoGraphics` 和基础库混为一谈

`Arduino_LED_Matrix` 负责矩阵显示本身。  
`ArduinoGraphics` 是更高层的绘图 API，不是必需依赖。

### 11.5 `ArduinoGraphics` 包含顺序错误

如果要用图形 API，请先：

```cpp
#include <ArduinoGraphics.h>
```

再：

```cpp
#include <Arduino_LED_Matrix.h>
```

### 11.6 以为 Python 侧能直接驱动矩阵细节

在 UNO Q 架构里，更推荐 Python 传“状态”，MCU 负责真正显示。  
除非你后面专门定义了一套逐像素协议，否则不要把矩阵底层控制放到 Python。

---

## 12. 一句话总结

`Arduino_LED_Matrix` 是 UNO Q 板载 LED 阵列的显示驱动库。  
你可以把它理解成三件事：

- `draw(frame)`：显示一帧像素
- `loadSequence()/playSequence()`：播放动画
- 配合 `ArduinoGraphics`：画图形和文字

如果你后面要做 UNO Q 的 LED 阵列功能，我建议默认按这个顺序选型：

1. 简单图案：`draw(frame)`
2. 图标动画：`loadSequence()/playSequence()`
3. 文字滚动：`ArduinoGraphics + Arduino_LED_Matrix`

---

## 13. 参考资料

- Arduino UNO Q 硬件页  
  https://docs.arduino.cc/hardware/uno-q

- UNO Q 数据手册  
  https://docs.arduino.cc/resources/datasheets/ABX00162-ABX00173-datasheet.pdf

- Arduino UNO R4 LED Matrix 官方教程  
  https://docs.arduino.cc/tutorials/uno-r4-wifi/led-matrix

- ArduinoCore-renesas 发布说明  
  https://github.com/arduino/ArduinoCore-renesas/releases

- `clear()` 相关 issue  
  https://github.com/arduino/ArduinoCore-renesas/issues/352

- 你项目中的天气示例  
  [/home/william/Desktop/Arduino UNO Q 4GB/例程分析/Weather_forcast_of_LED_matrix/copy-of-weather-forecast-on-led-matrix/sketch/sketch.ino](/home/william/Desktop/Arduino%20UNO%20Q%204GB/例程分析/Weather_forcast_of_LED_matrix/copy-of-weather-forecast-on-led-matrix/sketch/sketch.ino)

- 你项目中的手工绘帧示例  
  [/home/william/Desktop/Arduino UNO Q 4GB/例程分析/LED_Matrix_Rectangle/sketch/sketch.ino](/home/william/Desktop/Arduino%20UNO%20Q%204GB/例程分析/LED_Matrix_Rectangle/sketch/sketch.ino)
