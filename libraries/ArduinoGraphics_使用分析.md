# ArduinoGraphics 使用分析

## 1. 这个库是干什么的

`ArduinoGraphics` 是 Arduino 官方的一个**通用图形绘制库**。  
官方 README 对它的定位很直接：它是 Arduino 的核心图形库，**基于 Processing 风格 API**。

它本身通常**不直接驱动具体硬件**，而是提供一套统一的高层绘图接口，比如：

- 设置背景色
- 设置描边色和填充色
- 画点、线、矩形、圆、椭圆
- 绘制文字
- 处理滚动文本

真正把这些图形显示到具体设备上，通常还需要一个“底层显示驱动类”来承接，比如：

- `Arduino_LED_Matrix`
- 某些显示屏驱动类
- 某些 RGB 矩阵驱动类

所以可以把它理解成：

- `ArduinoGraphics`：**怎么画**
- 具体显示驱动库：**画到哪里**

---

## 2. 在 UNO Q 项目里的定位

对你现在这个 UNO Q 项目来说，`ArduinoGraphics` 不是必须库，但它非常有用。

### 不用它时

你可以直接用 `Arduino_LED_Matrix`：

- `draw(frame)` 手动刷帧
- `loadSequence(...)` + `playSequence()` 播放动画

这更偏底层，适合：

- 自己控制每个像素
- 自己做帧缓冲
- 播放预定义动画

### 用它时

你可以在更高层写：

- `line(...)`
- `rect(...)`
- `circle(...)`
- `text(...)`
- `beginText() / endText()`

这更适合：

- 显示几何图形
- 写字符和短文本
- 做滚动文本
- 快速原型开发

所以在 UNO Q 上它和 `Arduino_LED_Matrix` 的关系通常是：

- `Arduino_LED_Matrix` 负责 LED 矩阵硬件显示
- `ArduinoGraphics` 提供图形和文字 API

---

## 3. 是否能单独使用

通常不建议把 `ArduinoGraphics` 理解为“单独就能工作”的库。  
它更像一个图形基类/抽象层，需要有具体设备类支持。

例如在 UNO Q 板载 LED 矩阵上，常见写法是：

```cpp
#include <ArduinoGraphics.h>
#include <Arduino_LED_Matrix.h>

Arduino_LED_Matrix matrix;
```

然后通过 `matrix.beginDraw()`、`matrix.text(...)`、`matrix.rect(...)` 这类方式绘图。  
也就是说，实际调用对象往往还是 `matrix`，只是这个对象提供了 `ArduinoGraphics` 风格接口。

---

## 4. 和 Arduino_LED_Matrix 的关系

这一点最重要。

### 4.1 包含顺序

如果你要在 LED 矩阵上使用 `ArduinoGraphics` 功能，建议按这个顺序包含：

```cpp
#include <ArduinoGraphics.h>
#include <Arduino_LED_Matrix.h>
```

这个顺序在官方 issue 和社区实际用法里都反复出现。  
工程上直接照这个顺序写最稳妥。

### 4.2 为什么你之前问“要不要装 ArduinoGraphics”

更准确的答案是：

- **只想显示像素帧或动画**：不一定要它
- **想画几何图形、文字、滚动文本**：通常要它

也就是说：

- `Arduino_LED_Matrix` 解决“矩阵怎么显示”
- `ArduinoGraphics` 解决“图怎么描述”

---

## 5. 最基本的使用流程

### 5.1 包含头文件

```cpp
#include <ArduinoGraphics.h>
#include <Arduino_LED_Matrix.h>
```

### 5.2 创建显示对象

在 UNO Q 场景里一般还是：

```cpp
Arduino_LED_Matrix matrix;
```

### 5.3 初始化

```cpp
void setup() {
    matrix.begin();
}
```

### 5.4 绘制的基本模式

这个库最常见的工作流是：

```cpp
matrix.beginDraw();
// 做各种绘图操作
matrix.endDraw();
```

可以把它理解成：

- `beginDraw()`：开始一次绘图事务
- 在中间做图形和文字绘制
- `endDraw()`：提交到显示设备

对 LED 矩阵和某些显示屏，这很像一个“缓冲区提交”模型。

---

## 6. 颜色相关接口

虽然 UNO Q 的板载 LED 矩阵本质上是单色蓝光矩阵，但 `ArduinoGraphics` 作为通用图形库，API 仍然是按 RGB 颜色模型设计的。

### 6.1 `background(...)`

用于设置背景色：

```cpp
matrix.background(255, 0, 0);
matrix.background(0xFF0000);
```

作用：

- 影响 `clear()`
- 影响文字绘制背景

### 6.2 `fill(...)`

设置填充色：

```cpp
matrix.fill(255, 255, 0);
matrix.fill(0xFFFF00);
```

用于：

- 矩形填充
- 圆形填充
- 椭圆填充

### 6.3 `stroke(...)`

设置描边色：

```cpp
matrix.stroke(255, 255, 255);
matrix.stroke(0xFFFFFF);
```

用于：

- 线条
- 点
- 图形边框
- 文本颜色

### 6.4 `noFill()` / `noStroke()`

```cpp
matrix.noFill();
matrix.noStroke();
```

它们会关闭填充或描边。

例如只画轮廓矩形：

```cpp
matrix.noFill();
matrix.stroke(255, 255, 255);
matrix.rect(0, 0, 10, 6);
```

---

## 7. 绘图接口

官方 `docs/api.md` 给出的核心接口如下。

### 7.1 点和像素

#### `set(x, y, color)`

设置一个像素颜色：

```cpp
matrix.set(2, 3, 0xFFFFFF);
```

或：

```cpp
matrix.set(2, 3, 255, 255, 255);
```

#### `point(x, y)`

按当前 `stroke()` 颜色绘制点：

```cpp
matrix.stroke(255, 255, 255);
matrix.point(2, 3);
```

### 7.2 直线

#### `line(x1, y1, x2, y2)`

```cpp
matrix.stroke(255, 255, 255);
matrix.line(0, 0, 12, 7);
```

### 7.3 矩形

#### `rect(x, y, width, height)`

```cpp
matrix.stroke(255, 255, 255);
matrix.noFill();
matrix.rect(1, 1, 11, 6);
```

如果有填充色，就会同时填充内部：

```cpp
matrix.stroke(255, 255, 255);
matrix.fill(255, 255, 255);
matrix.rect(2, 2, 5, 3);
```

### 7.4 圆和椭圆

#### `circle(x, y, diameter)`

```cpp
matrix.fill(255, 255, 255);
matrix.noStroke();
matrix.circle(6, 3, 4);
```

#### `ellipse(x, y, width, height)`

```cpp
matrix.fill(255, 255, 255);
matrix.ellipse(6, 3, 8, 4);
```

---

## 8. 文字相关接口

这部分是 `ArduinoGraphics` 在 UNO Q LED 矩阵上最有价值的地方。

### 8.1 `text(...)`

直接画文字：

```cpp
matrix.stroke(255, 255, 255);
matrix.text("abc", 0, 1);
```

### 8.2 `textFont(...)`

切换字体。

官方文档明确提到内置字体至少有：

- `Font_4x6`
- `Font_5x7`

例如：

```cpp
matrix.textFont(Font_5x7);
```

### 8.3 `textFontWidth()` / `textFontHeight()`

分别获取当前字体宽高：

```cpp
int w = matrix.textFontWidth();
int h = matrix.textFontHeight();
```

这对你后面做居中、布局、滚动范围计算很有帮助。

### 8.4 `textSize(...)`

设置文字缩放：

```cpp
matrix.textSize(2);
matrix.textSize(2, 3);
```

对超小矩阵来说，放大字经常会超出显示范围，所以在 UNO Q 的 8 x 13 矩阵上通常还是优先用默认大小。

---

## 9. 滚动文本接口

这是 `ArduinoGraphics` 很实用的一组接口。

### 9.1 `beginText(...)`

开始一次文本输出流程：

```cpp
matrix.beginText(0, 1, 0xFFFFFF);
```

之后它可以使用 `Print` 风格接口：

```cpp
matrix.print("Hello");
matrix.println("World");
```

### 9.2 `endText(...)`

结束文本流程，并可选设置滚动方式：

```cpp
matrix.endText();
```

或者：

```cpp
matrix.endText(SCROLL_LEFT);
```

官方支持的方向有：

- `NO_SCROLL`
- `SCROLL_LEFT`
- `SCROLL_RIGHT`
- `SCROLL_UP`
- `SCROLL_DOWN`

### 9.3 `textScrollSpeed(...)`

设置滚动速度。  
官方文档说明它控制的是“每滚动一个像素之间的延迟毫秒数”。

```cpp
matrix.textScrollSpeed(80);
```

值越小，滚动越快。

### 9.4 一个最小滚动文字示例

```cpp
#include <ArduinoGraphics.h>
#include <Arduino_LED_Matrix.h>

Arduino_LED_Matrix matrix;

void setup() {
    matrix.begin();

    matrix.beginDraw();
    matrix.stroke(0xFFFFFF);
    matrix.textFont(Font_5x7);
    matrix.textScrollSpeed(80);
    matrix.beginText(0, 1, 0xFFFFFF);
    matrix.println("HELLO");
    matrix.endText(SCROLL_LEFT);
    matrix.endDraw();
}

void loop() {
}
```

---

## 10. `beginDraw()` / `endDraw()` 的理解

这是这个库最核心的调用模式。

### 10.1 基本语义

官方文档定义：

- `beginDraw()`：开始绘图
- `endDraw()`：结束绘图，并把开始到结束之间的绘制内容显示到屏幕上

### 10.2 工程理解

你可以把它理解成：

- 在内存/缓冲区里修改图形
- 最后一次性提交

### 10.3 实践上的注意点

从 Arduino 社区和官方 issue 的实际讨论看，不同底层显示驱动对 `beginDraw()/endDraw()` 的具体行为可能有差异，例如：

- 是否清空当前帧
- 是否覆盖旧内容
- 是否双缓冲

所以工程上建议：

- 每次绘新画面时，不要假设旧画面一定会自动保留
- 必要时显式设置 `background(...)` 并 `clear()`
- 需要完整刷新时，把一帧所有内容在一次 `beginDraw() ... endDraw()` 里画完

一个稳妥模板：

```cpp
matrix.beginDraw();
matrix.background(0x000000);
matrix.clear();

matrix.stroke(0xFFFFFF);
matrix.textFont(Font_5x7);
matrix.text("OK", 0, 1);

matrix.endDraw();
```

---

## 11. 在 UNO Q LED 矩阵上的适用边界

这一点非常重要。

`ArduinoGraphics` 是通用图形 API，但 UNO Q 的板载矩阵只有：

- 8 行
- 13 列
- 单色蓝光

这意味着：

### 11.1 颜色 API 在这里主要是“抽象接口”

虽然你可以写：

```cpp
matrix.stroke(255, 0, 0);
```

但在单色 LED 矩阵上，最终不一定表现为真正 RGB 色彩，而更可能被映射为亮度或单色点亮效果。

### 11.2 文本空间非常有限

`Font_5x7` 在 8 x 13 矩阵上已经接近极限。  
所以：

- 一次显示很长的静态文本并不现实
- 更适合滚动文本
- 更适合 1~2 个字符缩写

### 11.3 几何图形比复杂文字更适合

例如这些非常适合：

- 箭头
- 电量图标
- 方框
- 圆点状态
- 简单图标

---

## 12. 和 `draw(frame)` 的关系

如果你已经会用 `Arduino_LED_Matrix.draw(frame)`，那么可以这样理解：

- `draw(frame)`：你自己管理底层像素数组
- `ArduinoGraphics`：库帮你把“线、圆、文字”翻译成像素

两种方式没有谁绝对更高级，只是适用场景不同。

### 更适合 `draw(frame)` 的情况

- 你已经有固定帧数据
- 你要精确控制每个像素亮度
- 你在做自定义动画系统

### 更适合 `ArduinoGraphics` 的情况

- 你想快速画图
- 你想显示文字
- 你要做滚动文本
- 你不想手写像素映射

---

## 13. 在 UNO Q / App Lab 项目里的推荐用法

### 13.1 Python 负责高层逻辑

例如：

- 网络状态
- AI 识别结果
- 菜单状态
- 用户输入

### 13.2 MCU 侧用 ArduinoGraphics 做最终显示

例如 Python 只返回一个状态：

- `"wifi_ok"`
- `"error"`
- `"detect_cat"`

然后 MCU 侧决定：

- 画一个图标
- 显示 2 个字母
- 滚动一段短文本

这种方式比让 Python 逐像素控制矩阵更清晰，也更符合 UNO Q 双端协作模式。

---

## 14. 一个推荐的最小模板

### 14.1 静态文字

```cpp
#include <ArduinoGraphics.h>
#include <Arduino_LED_Matrix.h>

Arduino_LED_Matrix matrix;

void setup() {
    matrix.begin();

    matrix.beginDraw();
    matrix.background(0x000000);
    matrix.clear();
    matrix.stroke(0xFFFFFF);
    matrix.textFont(Font_5x7);
    matrix.text("HI", 0, 1);
    matrix.endDraw();
}

void loop() {
}
```

### 14.2 线框矩形

```cpp
#include <ArduinoGraphics.h>
#include <Arduino_LED_Matrix.h>

Arduino_LED_Matrix matrix;

void setup() {
    matrix.begin();

    matrix.beginDraw();
    matrix.background(0x000000);
    matrix.clear();
    matrix.stroke(0xFFFFFF);
    matrix.noFill();
    matrix.rect(1, 1, 11, 6);
    matrix.endDraw();
}

void loop() {
}
```

### 14.3 滚动文本

```cpp
#include <ArduinoGraphics.h>
#include <Arduino_LED_Matrix.h>

Arduino_LED_Matrix matrix;

void setup() {
    matrix.begin();

    matrix.beginDraw();
    matrix.background(0x000000);
    matrix.clear();
    matrix.textFont(Font_5x7);
    matrix.textScrollSpeed(70);
    matrix.beginText(0, 1, 0xFFFFFF);
    matrix.print("ARDUINO UNO Q");
    matrix.endText(SCROLL_LEFT);
    matrix.endDraw();
}

void loop() {
}
```

---

## 15. 常见问题和踩坑点

### 15.1 以为 `ArduinoGraphics` 能单独驱动所有显示设备

通常不能。  
它一般要依附具体显示类。

### 15.2 忘记 `beginDraw()` / `endDraw()`

很多绘图类接口如果不放在这个流程里，显示行为可能不符合预期。

### 15.3 误以为旧内容会自动保留

不同底层实现不完全一样。  
稳妥做法是每次需要完整刷新时显式：

```cpp
background(...)
clear()
重新画完整帧
```

### 15.4 在 UNO Q 上画太长文本

8 x 13 空间非常小，长文本更适合滚动，而不是静态显示。

### 15.5 把颜色接口当作真正 RGB 输出

UNO Q 板载矩阵是单色蓝光矩阵，所以 RGB API 更多是统一接口，不是完整彩色显示。

### 15.6 在 App Lab 里找不到库

`ArduinoGraphics` 的 `library.properties` 元数据限制过架构可见性，App Lab GUI 里有时可能搜不到。  
这不代表它概念上不能用，而是工具链/库元数据层面的可见性问题。

---

## 16. 一句话总结

`ArduinoGraphics` 是 Arduino 的高层图形绘制 API。  
在 UNO Q 上，它最有价值的用途不是替代 `Arduino_LED_Matrix`，而是**叠加在它之上**，让你更方便地画：

- 点
- 线
- 矩形
- 圆
- 文本
- 滚动文本

如果你后面要在 UNO Q 上做界面感更强的 LED 矩阵显示，它会比纯手写 `frame[]` 省很多事。

---

## 17. 参考资料

- ArduinoGraphics 仓库  
  https://github.com/arduino-libraries/ArduinoGraphics

- README  
  https://github.com/arduino-libraries/ArduinoGraphics/blob/master/README.md

- API 文档  
  https://raw.githubusercontent.com/arduino-libraries/ArduinoGraphics/master/docs/api.md

- Arduino 库信息页  
  https://www.arduinolibraries.info/libraries/arduino-graphics

- Arduino Forum 关于 UNO Q / App Lab 中库可见性的讨论  
  https://forum.arduino.cc/t/why-cant-i-add-the-arduinographics-library-in-arduino-app-lab/1419897

- 你项目中的 LED Matrix 示例  
  [sketch.ino](/home/william/Desktop/Arduino%20UNO%20Q%204GB/例程分析/LED_Matrix_Rectangle/sketch/sketch.ino)

- 你项目中的天气矩阵示例  
  [sketch.ino](/home/william/Desktop/Arduino%20UNO%20Q%204GB/例程分析/Weather_forcast_of_LED_matrix/copy-of-weather-forecast-on-led-matrix/sketch/sketch.ino)
