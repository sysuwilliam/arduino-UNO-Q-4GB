# Arduino UNO Q 完整引脚图详细分析

> **文档来源:** https://docs.arduino.cc/resources/pinouts/ABX00162-full-pinout.pdf  
> **分析日期:** 2026年4月19日

---

## 目录

- [一、引脚图图例说明](#一引脚图图例说明)
- [二、双处理器架构引脚分布](#二双处理器架构引脚分布)
- [三、UNO 标准引脚（顶部连接器）](#三uno-标准引脚顶部连接器)
- [四、模拟引脚（JANALOG 连接器）](#四模拟引脚janalog-连接器)
- [五、高速连接器（底部接口）](#五高速连接器底部接口)
- [六、LED 矩阵引脚](#六led-矩阵引脚)
- [七、重要警告与注意事项](#七重要警告与注意事项)
- [八、电源引脚详解](#八电源引脚详解)
- [九、通信接口引脚](#九通信接口引脚)
- [十、高级功能引脚](#十高级功能引脚)

---

## 一、引脚图图例说明

### 颜色编码含义

| 颜色标识 | 含义 |
|----------|------|
| **Power GPIO Digital** | 电源、GPIO 数字引脚 |
| **External IN** | 外部输入 |
| **Power Input** | 电源输入 |
| **Ground** | 地线 |
| **Power Output** | 电源输出 |
| **Analog External** | 模拟外部接口 |
| **I2C Default** | I2C 默认接口 |
| **LED** | LED 相关 |
| **SPI Default** | SPI 默认接口 |
| **RGB LED** | RGB LED |
| **UART/USART Default** | UART/USART 默认接口 |
| **Other SERIAL** | 其他串行接口 |
| **Analog Default** | 模拟默认接口 |
| **PWM/Timer** | PWM/定时器 |
| **Analog Audio** | 模拟音频 |
| **Main Part** | 主要部分（标准功能） |
| **Secondary Part** | 次要部分（扩展功能） |
| **Internal Component** | 内部组件 |
| **Other Pins** | 其他引脚（复位、系统控制、调试） |

### 术语说明

> **注意:** CIPO/COPI 之前被称为 MISO/MOSI
> - **CIPO** = Controller In Peripheral Out（原 MISO）
> - **COPI** = Controller Out Peripheral In（原 MOSI）

---

## 二、双处理器架构引脚分布

Arduino UNO Q 采用**双处理器架构**，引脚由两个处理器分别控制：

### 处理器分工

| 处理器 | 型号 | 控制的引脚 |
|--------|------|------------|
| **MPU (微处理器)** | Qualcomm QRB2210 | 底部高速连接器、摄像头接口、显示器接口等 |
| **MCU (微控制器)** | STM32U585 | 顶部 UNO 标准引脚、模拟引脚、LED 矩阵等 |

### 逻辑电平区分

| 逻辑电平 | 适用引脚 | 标识 |
|----------|----------|------|
| **3.3V** | 大部分 MCU 引脚 | `3.3V Logic` |
| **1.8V** | JCTL 调试接口、部分高速接口 | `1.8V Logic` |

---

## 三、UNO 标准引脚（顶部连接器）

UNO Q 保持经典 UNO 外形，顶部引脚与标准 Arduino UNO 完全兼容。

### 数字引脚映射表

| MCU 引脚 | Arduino 引脚 | 主要功能 | 次要功能 |
|----------|-------------|----------|----------|
| PB7 | **D0 / RX** | GPIO | UART RX |
| PB6 | **D1 / TX** | GPIO | UART TX |
| PB3 | **D2** | GPIO | - |
| PB0 | **D3** | GPIO | OPAMP OUT / PWM |
| PA12 | **D4** | GPIO | FDCAN1_TX (CAN 总线 TX) |
| PA11 | **D5** | GPIO | FDCAN1_RX (CAN 总线 RX) / PWM |
| PB1 | **D6** | GPIO | PWM |
| PB2 | **D7** | GPIO | - |
| PB4 | **D8** | GPIO | - |
| PB8 | **D9** | GPIO | PWM |
| PB9 | **D10 / SS** | GPIO | SPI SS / PWM |
| PB15 | **D11 / MOSI** | GPIO | SPI MOSI / PWM |
| PB14 | **D12 / MISO** | GPIO | SPI MISO |
| PB13 | **D13 / SCK** | GPIO | SPI SCK |

### 数字引脚功能详解

#### PWM 引脚（6 个）

| 引脚 | MCU 引脚 | 特性 |
|------|----------|------|
| D3 | PB0 | OPAMP OUT / PWM |
| D5 | PA11 | CAN RX / PWM |
| D6 | PB1 | PWM |
| D9 | PB8 | PWM |
| D10 | PB9 | SPI SS / PWM |
| D11 | PB15 | SPI MOSI / PWM |

> **PWM 频率：** 固定 500 Hz

#### CAN 总线引脚（2 个）

| 引脚 | MCU 引脚 | 功能 |
|------|----------|------|
| D4 | PA12 | FDCAN1_TX |
| D5 | PA11 | FDCAN1_RX |

#### SPI 引脚（4 个）

| 引脚 | MCU 引脚 | 功能 | 方向 |
|------|----------|------|------|
| D10 | PB9 | SS (片选) | 输出 |
| D11 | PB15 | MOSI (主出从入) | 输出 |
| D12 | PB14 | MISO (主入从出) | 输入 |
| D13 | PB13 | SCK (时钟) | 输出 |

---

## 四、模拟引脚（JANALOG 连接器）

### ADC 引脚映射表

| MCU 引脚 | Arduino 引脚 | 主要功能 | 次要功能 |
|----------|-------------|----------|----------|
| PA4 | **A0 / DAC0** | GPIO / ADC / DAC | - |
| PA5 | **A1 / DAC1** | GPIO / ADC / DAC | - |
| PA6 | **A2** | GPIO / ADC | OPAMP IN + |
| PA7 | **A3** | GPIO / ADC | OPAMP IN - |
| PC1 | **A4** | GPIO / ADC | I2C SDA |
| PC0 | **A5** | GPIO / ADC | I2C SCL |

### ADC 特性

| 参数 | 规格 |
|------|------|
| 分辨率 | 14-bit（可配置 14/12/10/8 位） |
| 输入范围 | 0 ~ VREF+ (默认 3.3V) |
| 引脚数量 | 6 个 |

### ADC 电压参考选项

| 参考电压 | 代码参数 | 来源 |
|----------|----------|------|
| 1.5V | `AR_INTERNAL1V5` | 内部 |
| 1.8V | `AR_INTERNAL1V8` | 内部 |
| 2.048V | `AR_INTERNAL2V05` | 内部 |
| 2.5V | `AR_INTERNAL2V5` | 内部 |
| 2V ~ VDD | `AR_EXTERNAL` | 外部（AREF 引脚） |

### DAC 引脚

| 引脚 | MCU 引脚 | 分辨率 |
|------|----------|--------|
| A0 / DAC0 | PA4 | 8~12 位可调 |
| A1 / DAC1 | PA5 | 8~12 位可调 |

---

## 五、高速连接器（底部接口）

底部高速连接器用于与 UNO Q 载板集成，包含 JMISC 和 JMEDIA 两个连接器。

### JMISC 连接器

提供额外的 MCU 和 MPU 引脚访问。

#### MCU 引脚（JMISC - MCU 部分）

| 引脚号 | MCU 引脚 | 功能 |
|--------|----------|------|
| 1 | PA8 | MCU_MCO (主时钟输出) |
| 2 | PB9 | - |
| 3 | PA18 | MCU_CRS_SYNC |
| 13 | PE8 | MCU_PE8 |
| 14 | PE7 | MCU_PE7 |
| 15 | PF14 | MCU_I2C4_SCL |
| 16 | PF15 | MCU_I2C4_SDA |
| 17 | PD9 | MCU_PSSI_DOCK |
| 18 | PD8 | MCU_PSSI_RDY |
| 19 | PI5 | MCU_PSSI_RDY |
| 21 | PA3 | MCU_OPAMP1_VOUT |
| 22 | PA8 | MCU_MCO |
| 23 | PB8 | MCU_OPAMP1_VINP |
| 24 | PA1 | MCU_OPAMP1_VINN |

#### MPU 引脚（JMISC - MPU 部分）

| 引脚号 | MPU 引脚 | 功能 |
|--------|----------|------|
| 44 | - | HS_DET (耳机检测) |
| 46 | - | HPH_REF (耳机参考) |
| 48 | - | HPH_R (耳机右声道) |
| 50 | - | HPH_L (耳机左声道) |
| 52 | - | LINEOUT_M (线路输出 M) |
| 54 | - | LINEOUT_P (线路输出 P) |
| 56 | - | EARMIC (耳麦麦克风) |
| 58 | - | EAR_P_R |
| 60 | - | MIC2_IN_P (麦克风 2 输入 +) |
| 62 | - | MIC2_IN_M (麦克风 2 输入 -) |

### JMEDIA 连接器

主要用于摄像头和显示器接口。

#### 摄像头接口（CSI）

| 引脚组 | 功能 |
|--------|------|
| CSI0_* | 摄像头接口 0 |
| CSI1_* | 摄像头接口 1 |
| CCI_I2C_* | 摄像头控制 I2C |

#### 显示器接口（DSI）

| 引脚组 | 功能 |
|--------|------|
| MIPI_DSI0_* | MIPI DSI 显示接口 0 |
| MIPI_DSI1_* | MIPI DSI 显示接口 1 |

---

## 六、LED 矩阵引脚

### LED 矩阵规格

| 参数 | 值 |
|------|-----|
| 尺寸 | 8 行 × 13 列 |
| LED 数量 | 104 个 |
| 颜色 | 蓝色 |
| 灰度级别 | 8 级（3-bit） |
| 控制方式 | 由 MCU (STM32) 控制 |

### LED 矩阵布局

```
列:  1   2   3   4   5   6   7   8   9   10  11  12  13
行1:  ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●
行2:  ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●
行3:  ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●
行4:  ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●
行5:  ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●
行6:  ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●
行7:  ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●
行8:  ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●
```

### LED 矩阵索引映射

| 行 | 列 1-13 的索引范围 |
|----|-------------------|
| 1 | 1-13 |
| 2 | 14-26 |
| 3 | 27-39 |
| 4 | 40-52 |
| 5 | 53-65 |
| 6 | 66-78 |
| 7 | 79-91 |
| 8 | 92-104 |

### 编程接口

```cpp
#include <Arduino_LED_Matrix.h>

Arduino_LED_Matrix matrix;

void setup() {
    matrix.begin();
    matrix.setGrayscaleBits(3);  // 设置灰度级别 (1-8)
    matrix.draw(frameArray);      // 绘制帧
}
```

---

## 七、重要警告与注意事项

### ⚠️ 电压电平警告

| 警告内容 | 说明 |
|----------|------|
| **AO 和 AI 不支持 5V** | 模拟输出和模拟输入引脚**不能**承受 5V 电压 |
| **JCTL 引脚为 1.8V** | 调试接口引脚工作在 1.8V 逻辑电平，必须使用 1.8V 兼容的 USB-TTL 转换器 |

### ⚠️ 特殊引脚限制

| 限制类型 | 说明 |
|----------|------|
| **不可作为常规 GPIO** | 某些引脚有特殊用途，不能作为普通 GPIO 使用（引脚图上有特殊标注） |
| **电源优先级** | 同时使用多种供电方式时，遵循特定优先级规则 |

### ⚠️ 高级区域说明

> **警告:** 以下信息仅供高级使用，可能不受 Arduino 官方软件支持：
> - 底部高速连接器的直接访问
> - 原始 MPU 引脚操作
> - 自定义固件刷写

---

## 八、电源引脚详解

### 电源输入引脚

| 引脚 | 电压范围 | 电流 | 说明 |
|------|----------|------|------|
| **USB-C** | 5V DC | 3A (15W) | 主要供电方式 |
| **VIN** | 7-24V DC | - | 外部电源输入 |
| **5V** | 5V DC | - | 外部 5V 输入 |

### 电源输出引脚

| 引脚 | 电压 | 最大电流 | 说明 |
|------|------|----------|------|
| **3.3V** | 3.3V | - | 3.3V 输出（供外设使用） |
| **5V** | 5V | - | 5V 输出（USB 供电时可用） |
| **1.8V** | 1.8V | - | 1.8V 输出（高级应用） |
| **VBAT** | - | - | 电池备份电源 |

### 地线引脚

| 引脚 | 说明 |
|------|------|
| **GND** | 多个 GND 引脚分布在板边 |

---

## 九、通信接口引脚

### I2C 接口

#### 默认 I2C（Wire）

| 引脚 | Arduino 名称 | MCU 引脚 | 功能 |
|------|-------------|----------|------|
| D20 | SDA | PB11 | I2C 数据线 |
| D21 | SCL | PB10 | I2C 时钟线 |

#### 第二路 I2C

| 引脚 | Arduino 名称 | MCU 引脚 | 功能 |
|------|-------------|----------|------|
| D18 | SDA2 | PC1 | I2C2 数据线 |
| D19 | SCL2 | PC0 | I2C2 时钟线 |

### UART 接口

#### 默认串口（Serial）

| 引脚 | Arduino 名称 | MCU 引脚 | 功能 |
|------|-------------|----------|------|
| D0 | RX | PB7 | UART 接收 |
| D1 | TX | PB6 | UART 发送 |

### SPI 接口

| 引脚 | Arduino 名称 | MCU 引脚 | 功能 |
|------|-------------|----------|------|
| D10 | SS | PB9 | 片选 |
| D11 | MOSI/COPI | PB15 | 主出从入 |
| D12 | MISO/CIPO | PB14 | 主入从出 |
| D13 | SCK | PB13 | 时钟 |

---

## 十、高级功能引脚

### OPAMP 引脚（运算放大器）

| 引脚 | MCU 引脚 | 功能 |
|------|----------|------|
| A2 | PA6 | OPAMP IN + |
| A3 | PA7 | OPAMP IN - |
| D3 | PB0 | OPAMP OUT |

### PSSI 引脚（并行同步从机接口）

| JMISC 引脚 | MCU 引脚 | 功能 |
|------------|----------|------|
| 7 | PE4 | PSSI_D4 |
| 8 | PE5 | PSSI_D3 |
| 9 | PE3 | PSSI_D2 |
| 10 | PC9 | PSSI_D1 |
| 11 | PC8 | PSSI_D0 |
| 15 | PD9 | PSSI_DOCK |
| 17 | PI7 | PSSI_D7 |
| 19 | PI6 | PSSI_D6 |
| 21 | PI4 | PSSI_D5 |

### 调试接口（JCTL）

> ⚠️ **警告：** JCTL 引脚工作在 **1.8V 逻辑电平**

| 引脚 | 功能 | 说明 |
|------|------|------|
| JCTL_TX | UART TX | 调试串口发送 |
| JCTL_RX | UART RX | 调试串口接收 |
| - | TCK/SWCLK | JTAG/SWD 时钟 |
| - | TMS/SWDIO | JTAG/SWD 数据 |
| - | TDO/SWO | JTAG/SWD 输出 |

### 硬件调试 UART 接口

| 参数 | 值 |
|------|-----|
| 波特率 | 115200 bps |
| 逻辑电平 | **1.8V** |
| 用途 | 引导日志、内核日志、底层调试 |

---

## 附录：完整引脚分类速查表

### 按功能分类

| 功能类别 | 引脚数量 | 引脚列表 |
|----------|----------|----------|
| **数字 I/O** | 22 | D0-D21 |
| **模拟输入** | 6 | A0-A5 |
| **PWM 输出** | 6 | D3, D5, D6, D9, D10, D11 |
| **DAC 输出** | 2 | A0/DAC0, A1/DAC1 |
| **SPI** | 4 | D10-D13 |
| **I2C** | 4 | D18-D21 (含第二路) |
| **UART** | 2 | D0, D1 |
| **CAN** | 2 | D4, D5 |
| **电源** | 多个 | VIN, 5V, 3.3V, GND |

### 按处理器分类

| 处理器 | 控制的引脚 |
|--------|------------|
| **MCU (STM32U585)** | 顶部 UNO 引脚、JANALOG、LED 矩阵、部分 JMISC |
| **MPU (QRB2210)** | 摄像头接口、显示器接口、音频接口、部分 JMISC |

---

## 参考资源

| 资源 | 链接 |
|------|------|
| 完整引脚图 PDF | https://docs.arduino.cc/resources/pinouts/ABX00162-full-pinout.pdf |
| 数据手册 | https://docs.arduino.cc/resources/datasheets/ABX00162-datasheet.pdf |
| 原理图 | https://docs.arduino.cc/resources/schematics/ABX00162-schematics.pdf |
| 用户手册 | https://docs.arduino.cc/tutorials/uno-q/user-manual/ |

---

> 📝 **文档版本：** 1.0  
> 📅 **分析日期：** 2026年4月19日  
> 📖 **基于：** Arduino UNO Q Full Pinout (ABX00162)
