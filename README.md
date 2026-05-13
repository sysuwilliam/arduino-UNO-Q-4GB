# Arduino UNO Q 4GB

Arduino UNO Q 4GB 开发板的学习与开发记录，为相关开发者提供参考。

## 技术领域

- **混合架构开发**：MPU 与 MCU 跨核通信
- **机器视觉**：实时视觉分析
- **边缘 AI**：神经网络模型本地推理
- **物联网集成**：IoT 远程控制与数据交互

## 目录结构

```
arduino-UNO-Q-4GB/
│
├── Apps/                               # 应用程序目录
│   └── LED_showtext/                   # LED文本显示应用
│       └── led_showtext/
│           ├── python/                 # Python后端代码
│           ├── sketch/                 # Arduino草图代码
│           ├── app.yaml                # 应用配置文件
│           └── 开发说明.md              # 开发详细说明
│
├── 例程分析/                            # 官方例程分析目录
│   ├── Blink_LED/                      # LED闪烁例程
│   │   ├── blink-led/                  # 原始例程
│   │   └── blink-led-分析版/            # 深度分析版本
│   │
│   ├── Detect_Objects_on_Smartphone_Camera/  # 手机摄像头物体检测
│   │   ├── detect-objects-on-smartphone-camera/
│   │   └── detect-objects-on-smartphone-camera-分析版/
│   │
│   ├── detect-objects-on-camera/       # 摄像头物体检测
│   │
│   └── Weather_forcast_of_LED_matrix/  # LED矩阵天气预报
│       ├── weather-forecast-on-led-matrix/
│       └── weather-forecast-on-led-matrix-分析版/
│
├── 开发报告/                            # 开发过程文档
│   ├── pictures/                       # 报告配图目录
│   ├── 1.开发板介绍.md
│   └── 2.使用Ubuntu系统运行开发版.md
│
├── 数据手册/                            # 官方硬件文档
│   ├── ABX00162-ABX00173-datasheet.pdf # 官方数据手册
│   ├── ABX00162-schematics.pdf         # 电路原理图
│   ├── ABX00162-full-pinout.pdf        # 完整引脚定义图
│   ├── ABX00162-cad-files.zip          # CAD设计文件
│   ├── ABX00162-step/                  # 3D模型
│   └── stm32u585ai.pdf                 # STM32U5微控制器手册
│
├── 演示视频/                            # 演示资源目录
│   └── Arduino UNO Q例程演示.mp4
│
├── 运行指南/                            # 软硬件使用指南
│   ├── Hardware/                       # 硬件相关
│   │   ├── 1.用户手册.md
│   │   ├── 2.电源规格详解.md
│   │   ├── 3.引脚图分析.md
│   │   ├── 4.Ubuntu快速运行指南.md
│   │   ├── 5.远程访问选项.md
│   │   ├── 6.SSH连接.md
│   │   ├── 7.单板计算机模式.md
│   │   ├── 8.系统镜像更新.md
│   │   └── 9.Debian_Linux基础.md
│   │
│   └── Software/                       # 软件相关
│       ├── 1.入门指南.md
│       ├── 2.Bricks构建块指南.md
│       ├── 3.CLI_命令行工具指南.md
│       ├── 4.示例应用概览.md
│       ├── 5.自定义AI模型指南.md
│       ├── 6.发布说明.md
│       └── 7.IoT_Remote集成指南.md
│
└── libraries/                          # 库文档目录
    ├── Arduino_LED_Matrix.md           # LED矩阵库
    ├── Arduino_RouterBridge.md         # 路由桥接库
    └── ArduinoGraphics.md              # 图形库
```

## 主要内容说明

### Apps - 应用程序
自主开发的应用程序，包含完整的 Python 后端、Arduino 草图代码和配置文件。

### 例程分析 - 官方例程深度分析
包含 4 个官方例程的学习与分析：
- **Blink LED**：基础 LED 闪烁，包含详细代码注释和知识点总结
- **Detect Objects**：物体检测例程，展示边缘 AI 能力
- **Weather Forecast**：LED 矩阵天气预报，演示网络数据获取
- 每个例程均包含原始代码和分析文档

### 开发报告 - 开发过程记录
记录开发板的上手过程和开发经验，配有操作截图。

### 数据手册 - 完整硬件文档
包含官方数据手册、电路原理图、引脚定义、CAD 文件和 3D 模型。

### 运行指南 - 完整使用指南
- **Hardware**：硬件使用、系统配置、远程访问等 9 个指南
- **Software**：软件开发、CLI 工具、AI 模型自定义等 7 个指南

### libraries - 核心库文档
三个核心库的详细文档：LED 矩阵控制、MPU/MCU 通信、图形绘制。

## 快速开始

1. **了解硬件**：查看 `开发报告/1.开发板介绍.md`
2. **系统初始化**：参考 `开发报告/2.使用Ubuntu系统运行开发版.md`
3. **运行例程**：观看 `演示视频/Arduino UNO Q例程演示.mp4`
4. **深入学习**：
   - `运行指南/Hardware/` - 硬件相关指南
   - `运行指南/Software/` - 软件开发指南
   - `例程分析/` - 官方例程深度解析

## 参考资源

- [Arduino UNO Q 官方文档](https://docs.arduino.cc/hardware/uno-q/)
- [Arduino App Lab 官方文档](https://docs.arduino.cc/software/app-lab/)
- [本项目 GitHub 仓库](https://github.com/sysuwilliam/arduino-UNO-Q-4GB)

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。
