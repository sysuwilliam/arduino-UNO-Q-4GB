# `sketch.yaml` 解析

## 原文件作用

`sketch.yaml` 是 Arduino 草图的构建配置文件，用于指定：

- 编译平台；
- 依赖库；
- 默认构建配置。

虽然它不包含业务逻辑，但它决定了 LED 点阵控制和 Router Bridge 能否正确参与编译。

## 原始内容解析

### `profiles:`

表示项目定义了一组可选构建配置。

本项目只有一个配置：`default`。

### `default:`

表示下面的配置内容属于默认构建方案。

### `platforms:`

原文件指定的平台是：

`arduino:zephyr`

这说明项目构建目标并不是传统单一的经典 Arduino AVR 环境，而是面向支持当前应用运行模型的平台配置。

结合项目内容看，这个平台需要支持：

- LED Matrix 驱动能力；
- Router Bridge 调用机制；
- Python 与 Arduino 协同运行。

### `libraries:`

这里声明了项目构建所需的依赖库。

#### `Arduino_RouterBridge (0.3.0)`

这是最关键的桥接库，负责：

- `Bridge.begin()`
- `Bridge.call(...)`
- Python 与 Arduino 之间的函数调用机制

没有它，Arduino 就无法去调用 Python 的天气查询函数。

#### `Arduino_RPClite (0.2.1)`

这是 Router Bridge 的底层依赖之一。

从命名可以推断，它负责轻量级远程调用机制的底层支撑。

#### `ArxContainer (0.7.0)`

这是容器类相关依赖，通常用于底层数据结构支持。

#### `ArxTypeTraits (0.3.2)`

这是类型特征支持库，更多用于模板与类型系统的底层实现。

#### `DebugLog (0.8.4)`

这是调试日志相关依赖，便于底层库在开发和排查问题时输出调试信息。

#### `MsgPack (0.4.2)`

这是消息打包与序列化相关依赖。

桥接调用往往需要对参数和结果进行编码传输，因此这类库在通信框架中很常见。

### `default_profile: default`

表示当系统没有明确指定其它 profile 时，就使用 `default` 配置进行编译。

## 小结

`sketch.yaml` 的主要职责是：

- 指定目标平台；
- 声明 Router Bridge 相关依赖；
- 确保草图具备桥接通信能力的编译环境。

对这个项目而言，它是“能否成功构建天气点阵程序”的基础配置文件。
