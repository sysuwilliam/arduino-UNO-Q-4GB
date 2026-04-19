# Arduino UNO Q SSH 连接指南

> **原文链接:** https://docs.arduino.cc/tutorials/uno-q/ssh/  
> **作者:** Karl Söderby  
> **最后修订:** 2025年10月29日  
> **翻译日期:** 2026年4月19日

---

## 目录

- [概述](#概述)
- [要求](#要求)
- [安装 SSH（本地计算机）](#安装-ssh本地计算机)
- [通过 SSH 连接](#通过-ssh-连接)
- [Arduino App CLI](#arduino-app-cli)
- [文件传输](#文件传输)
- [故障排除](#故障排除)

---

## 概述

[Arduino® UNO Q](https://store.arduino.cc/products/uno-q) 可以通过 [Arduino App Lab](https://docs.arduino.cc/software/app-lab/) 进行编程，这是一个桌面应用程序，支持代码编辑和在开发板上运行 [Apps](https://docs.arduino.cc/software/app-lab/tutorials/getting-started/#create--run-apps)，无需任何外部工具。

开发板的微处理器（运行 Debian OS）也可以使用 Secure Shell（SSH）访问，这是一种允许通过局域网远程连接到开发板的方法。这使您能够：

- 访问开发板的 shell 并远程在开发板上执行操作
- 从本地计算机远程传输文件到开发板（使用 SCP）

UNO Q 开发板预装了 Arduino App Lab，它基于 `arduino-app-cli` 工具*。这使您能够**通过命令行启动 Apps**，而不是使用桌面应用程序。

\* 在 [Arduino App CLI 指南](https://docs.arduino.cc/software/app-lab/tutorials/cli)中阅读更多关于 `arduino-app-cli` 的信息。

---

## 要求

### 硬件要求

- [Arduino® UNO Q](https://store.arduino.cc/products/uno-q)
- 5 VDC 3 A 电源适配器（例如手机充电器或电脑的 USB 端口）

### 软件要求

- 已完成开发板的[首次设置](https://docs.arduino.cc/software/app-lab/tutorials/getting-started/#install--set-up-arduino-app-lab)*
- 计算机上已安装 SSH 客户端工具（macOS、Windows 10+、Ubuntu 都有内置 SSH 客户端工具）
- 可访问本地 Wi-Fi® 网络（计算机和开发板需要在同一网络）

> ⚠️ **注意：** 在首次设置期间，会输入 Wi-Fi® 凭据，开发板将自动启用 SSH。如果未完成首次设置，则无法通过 SSH 访问开发板，除非手动激活。这也可以通过使用 `adb` 访问开发板，并在开发板的 shell 中运行 `arduino-app-cli system network-mode enable` 来激活。详见 [Arduino App CLI 文档](https://docs.arduino.cc/software/app-lab/tutorials/cli/)。

---

## 安装 SSH（本地计算机）

SSH 是一种网络协议，而不是工具本身。有许多不同的 SSH 工具可供选择，大多数操作系统都有内置工具。在本节中，我们将介绍如何在一些常见操作系统（macOS、Windows、Ubuntu）上设置它。

### macOS

macOS 具有基于 [OpenSSH](https://www.openssh.com/) 的内置 `ssh` 工具，**应该开箱即用**。通过在终端中运行以下命令检查工具是否存在：

```bash
ssh -V
```

您应该看到类似以下内容：

```
OpenSSH_9.9p2, LibreSSL 3.3.6
```

这表示它正常工作。✅

> 💡 **提示：** 如果您运行的是过时/自定义系统，由于某种原因没有 SSH，您可以通过例如 Brew 手动安装 [OpenSSH](https://formulae.brew.sh/formula/openssh) 和 [LibreSSL](https://formulae.brew.sh/formula/libressl)。

### Windows

较新版本的 Windows（10+）也包含 SSH 客户端，无需安装额外工具。要验证工具是否已安装，在 Windows 机器上打开终端，输入：

```bash
ssh -V
```

应该返回类似以下内容：

```
OpenSSH_for_Windows_x.x, LibreSSL 3.x.x
```

这表示它正常工作。✅

> 💡 **提示：** 对于较旧的 Windows 机器，使用包管理器如 [Chocolatey](https://chocolatey.org/) 来安装 OpenSSH / LibreSSL。

### Linux (Ubuntu)

许多 Linux 操作系统都包含 SSH 客户端，无需安装额外工具。要验证工具是否已安装，在 Ubuntu 机器上打开终端，输入：

```bash
ssh -V
```

应该返回类似以下内容：

```
OpenSSH_x.x Ubuntu-3ubuntu.x, OpenSSL x.x.x
```

这表示它正常工作。✅

> 💡 **提示：** 如果您运行的是过时/自定义系统，由于某种原因没有 SSH，您可以通过运行 `sudo apt install openssh-client openssh-server libressl-dev` 手动安装 [OpenSSH](https://formulae.brew.sh/formula/openssh) 和 [LibreSSL](https://formulae.brew.sh/formula/libressl)。

---

## 通过 SSH 连接

要通过 SSH 连接到 UNO Q 开发板，我们只需要知道**开发板名称和密码**。这在首次设置期间设置。

1. 打开终端。
2. 运行以下命令：
   ```bash
   ssh arduino@<boardname>.local # 将 <boardname> 替换为您的开发板名称
   ```

3. 当询问是否连接时，输入 `yes`。

4. 输入开发板的密码。

输入密码后，您应该进入开发板的 shell，现在可以执行操作了！

请参阅下面成功访问开发板 shell 后的样子。

### macOS 确认

![macOS SSH 访问](https://docs.arduino.cc/static/66329408af0db4d2890646f3734a961e/a6d36/ssh-macos.png)

#### macOS MDNS 问题

如果连接失败并出现以下错误：

- `ssh: connect to host <boardname>.local port 22: Connection refused`

这可能是您本地网络的 mDNS 问题。要解决此问题，可以尝试以下替代方案：

**直接通过 IP 地址连接：** 开发板的 IP 地址可以通过以下方式找到：

- Arduino IDE 2（需要安装 Zephyr core）
- Arduino CLI，运行 `arduino-cli board list`
- 在开发板的 shell 中运行 `hostname -I`。您可以通过 `adb shell` 访问开发板（[说明](https://docs.arduino.cc/software/app-lab/tutorials/cli/#connect-via-adb)），或[以 SBC 模式使用开发板](https://docs.arduino.cc/tutorials/uno-q/single-board-computer/)。

获取 IP 地址后，您应该能够使用 `ssh arduino@10.0.20.138` 通过 SSH 连接。

> ⚠️ **注意：** 如果您之前曾连接到具有相同 IP 地址的开发板，但已重新刷写开发板，您可能需要从 `~/.ssh/known_hosts` 中删除旧密钥。这可以通过编辑 `known_hosts` 文件或运行 `ssh-keygen -R <board ip address>` 来完成。

### Windows 确认

![Windows SSH 访问](https://docs.arduino.cc/static/26f281d857eed3120f12b33c4a9b2b24/a6d36/ssh-windows.png)

### Linux (Ubuntu) 确认

![Linux (Ubuntu) SSH 访问](https://docs.arduino.cc/static/0088891f2b386647445f922ad31195fe/a6d36/ssh-linux.png)

---

## Arduino App CLI

`arduino-app-cli` 可用于从终端在开发板上启动和停止 Apps。通过 SSH 访问开发板时，您可以运行诸如 `arduino-app-cli app start <app>` 的命令。

有关 `arduino-app-cli` 工具的更多详细信息，请参阅 [Arduino App CLI 指南](https://docs.arduino.cc/software/app-lab/tutorials/cli/)。

---

## 文件传输

要从计算机传输文件到开发板，请**从计算机的终端**使用 `scp` 工具（不是在开发板上的 SSH 会话中）。该工具可用于向开发板**推送**或从开发板**拉取**文件和文件夹。

这是通过指定计算机上的本地路径（例如 `/User/documents/file.xx`）和开发板上的路径（例如 `/home/arduino/`）来完成的。

### 推送文件

要**推送**文件，使用以下命令：

```bash
scp test-transfer.txt arduino@<boardname>.local:/home/arduino/
```

这将把您运行命令的同一目录中的 `test-transfer.txt` 文件传输到开发板。

### 拉取文件

要**拉取**文件，使用以下命令：

```bash
scp arduino@<boardname>.local:/home/arduino/test-transfer.txt ./
```

这将把文件拉取到您运行命令的目录。`./` 可以替换为指定路径（例如 `/User/documents/`）。

### 推送/拉取文件夹

要**推送**文件夹，使用 `-rp` 递归复制目录并保留时间/权限：

```bash
scp -rp "my-folder" arduino@<board-name>.local:/home/arduino/ArduinoApps/
```

要从开发板**拉取**文件夹到当前目录：

```bash
scp -rp arduino@<board-name>.local:/home/arduino/ArduinoApps/my-folder ./
```

---

## 故障排除

如果 SSH 连接失败，有一些常见事项需要检查：

- 是否已完成首次设置？如果没有，请按照[此处](https://docs.arduino.cc/software/app-lab/tutorials/getting-started/#install--set-up-arduino-app-lab)的说明操作。首次设置将在开发板上启用 SSH，这是连接所必需的。

- 如果即使已完成首次设置，SSH 连接仍然卡住，可能是本地网络问题。检查开发板是否与您的计算机连接到同一网络。

### MDNS 问题

某些网络可能会阻止使用 mDNS，这使我们能够使用"友好"名称（`arduino@<boardname>.local`），而不是使用开发板的实际 IP 地址。有两种解决方法：

1. 不使用 `arduino@<boardname>.local`，而是直接使用开发板的 IP 地址。可以通过以 SBC 模式启动开发板并在终端中输入 `hostname -I` 来获取 IP 地址。这将显示您开发板的 IP 地址。

2. （高级）通过运行 `sudo nano /etc/hosts` 编辑本地计算机上的 `/etc/hosts`。在文件底部添加 `<boardipaddress> <boardname>.local`。这将允许您使用 `ssh arduino@<boardname>.local` 连接。

---

> 📝 **文档版本：** 1.0（翻译）  
> 📅 **翻译日期：** 2026年4月19日  
> 📖 **基于：** Connect to UNO Q via Secure Shell (SSH)（最后修订：2025年10月29日）
