# Arduino UNO Q 4GB

Arduino UNO Q 4GB 开发板的学习与开发记录，为后续开发者提供参考。

## 技术领域

- **混合架构开发**：MPU 与 MCU 跨核通信
- **机器视觉**：实时视觉分析
- **ROS 2 机器人**：搭载 ROS 2 Humble 构建分布式机器人系统
- **边缘 AI**：神经网络模型本地推理

## 目录结构

```
├── 数据手册/               # 官方数据手册与原理图
│   ├── ABX00162-ABX00173-datasheet.pdf   # 官方数据手册
│   ├── ABX00162-schematics.pdf           # 原理图
│   ├── ABX00162-full-pinout.pdf          # 引脚定义图
│   ├── ABX00162-cad-files.zip           # CAD 文件
│   ├── ABX00162-step/                    # 3D 模型
│   └── stm32u585ai.pdf                  # STM32U5 微控制器手册
│
└── 运行指南/               # 软硬件使用指南
    ├── Hardware/           # 硬件相关
    │   ├── 1.用户手册.md
    │   ├── 2.电源规格详解.md
    │   ├── 3.引脚图分析.md
    │   ├── 4.Ubuntu快速运行指南.md
    │   ├── 5.远程访问选项.md
    │   ├── 6.SSH连接.md
    │   ├── 7.单板计算机模式.md
    │   ├── 8.系统镜像更新.md
    │   └── 9.Debian_Linux基础.md
    │
    └── Software/            # 软件相关
        ├── 1.入门指南.md
        ├── 2.Bricks构建块指南.md
        ├── 3.CLI命令行工具指南.md
        ├── 4.示例应用概览.md
        ├── 5.自定义AI模型指南.md
        ├── 6.发布说明.md
        └── 7.IoT_Remote集成指南.md
```

## 快速开始

1. 查看 `运行指南/Hardware/1.用户手册.md` 了解硬件基本信息
2. 参考 `运行指南/Hardware/4.Ubuntu快速运行指南.md` 完成系统初始化
3. 阅读 `运行指南/Software/1.入门指南.md` 开始软件开发

## 参考资源

- [Arduino UNO Q 官方文档](https://docs.arduino.cc/hardware/uno-r4-wifi)
- [STM32U5 微控制器文档](https://www.st.com/en/microcontrollers-microprocessors/stm32u5-series.html)

## 许可证

Apache-2.0