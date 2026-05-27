# mspm0kit-skill

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Skills](https://img.shields.io/badge/Skills-tianqiaoxing__g3519%20%7C%20mspm0__ccs-blue)]()

天巧星 MSPM0G3519 开发板的 AI 编程助手 skill。一句话创建完整 CCS 工程，自动适配引脚、时钟树、外设配置。通过 SysConfig CLI + gmake 一键编译验证，DSLite 一键烧录。

[English](README.md) | **中文**

---

## 包含的 Skill

| Skill | 用途 |
|-------|------|
| `tianqiaoxing-g3519` | 一句话建工程：scaffold → build → flash。含完整引脚表 + 10 个外设参考文档。 |
| `mspm0-ccs` | 通用 MSPM0 SysConfig/DriverLib 辅助。工程检查、例程管理、串口控制台。 |

---

## 安装

### Claude Code

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills" | Out-Null
Copy-Item -Recurse -Force .\skills\tianqiaoxing-g3519 "$env:USERPROFILE\.claude\skills\tianqiaoxing-g3519"
Copy-Item -Recurse -Force .\skills\mspm0-ccs "$env:USERPROFILE\.claude\skills\mspm0-ccs"
```

### Codex / OpenCode / OpenClaw

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.agents\skills" | Out-Null
Copy-Item -Recurse -Force .\skills\tianqiaoxing-g3519 "$env:USERPROFILE\.agents\skills\tianqiaoxing-g3519"
```

---

## 快速开始

### 1. 首次配置工具链路径

```powershell
python ~/.claude/skills/tianqiaoxing-g3519/scripts/setup.py
```

直接回车使用默认值（CCS `D:\TI\CCS\ccs`、SDK `D:\TI\CCS\mspm0_sdk_2_05_01_00`、XDS110）。如果路径不同，输入实际路径后回车。配置保存在 `config.json`。

### 2. 在 Kiro / Claude Code 中说

```
帮我实现 UART0 调试串口的工程
```

Skill 会自动：
1. **思考** — 识别外设、查引脚表、确认时钟
2. **规划** — 列出将要创建的工程内容
3. **编码** — 运行 `scaffold.py` 生成完整 CCS 工程
4. **询问** — "工程已生成，是否要我帮你编译测试？"
5. **验证** — 确认后自动运行 SysConfig CLI + gmake，报告结果

### 3. 在 CCS 中导入

File → Import → C/C++ → CCS Projects from `.projectspec` → 选择 `<工程名>.projectspec`

---

## 支持的功能

### 标准外设（基于 MSPM0 SDK 官方例程）

| 外设 | SDK 例程 | 默认引脚 | 操作流程 |
|------|----------|----------|----------|
| GPIO 输出 | `gpio_toggle_output` | PB22 | `scaffold.py` → `build.py` → `flash.py` |
| UART 收发 | `uart_rw_multibyte_fifo_poll` | PA10/PA11 | 同上 |
| UART 控制台 | `uart_tx_console_multibyte_repeated_fifo_dma` | PA10/PA11 (115200) | 同上 |
| SPI 控制器 | `spi_controller_multibyte_fifo_poll` | SPI0 空闲引脚 | 同上 |
| I2C 控制器 | `i2c_controller_rw_multibyte_fifo_poll` | I2C0 空闲引脚 | 同上 |
| ADC 单通道 | `adc12_single_conversion` | 空闲 ADC 引脚 | 同上 |
| PWM 定时器 | `timg_32bit_timer_mode_pwm_edge_sleep` | TIMG0 空闲引脚 | 同上 |
| 周期定时器 | `tima_timer_mode_periodic_repeat_count` | — | 同上 |
| 编码器 | `timg_qei_mode` | PA29/PA30 | 同上 |

### 板载外设（基于 OLED_UI 框架）

```bash
# 纯 OLED UI 框架
python scripts/scaffold_oled.py my_project

# 带可选模块
python scripts/scaffold_oled.py my_project --with-imu --with-ws2812 --with-wireless
```

| 模块 | 驱动 | 引脚 | 开关 |
|------|------|------|------|
| OLED 屏幕 (SSD1312 128x64) | `oledUI/` 框架 | PA0(SDA)/PA1(SCL) | 默认包含 |
| IMU (LSM6DS3 六轴) | `hw_lsm6ds3.c` + AHRS 融合 | PA28(SDA)/PA27(SCL) | `--with-imu` |
| WS2812 RGB 灯 (x4) | `hw_ws2812.c` + 特效 | PB26 (TIMA1 CCP0) | `--with-ws2812` |
| 2.4G 无线串口 | `mid_wireless_uart.c` | PB17(TX)/PB18(RX) | `--with-wireless` |

---

## 引脚速查表

### 完全不可用

| 引脚 | 原因 |
|------|------|
| PA2 | 频率精度控制，未引出 |
| PA5, PA6 | 40 MHz 外部晶振 |
| PA19, PA20 | SWD 调试接口 |

### 板载外设占用

| 引脚 | 外设 |
|------|------|
| PA0, PA1 | OLED 软件 I2C（板载 2.2kΩ 上拉） |
| PA10, PA11 | UART0 转 CH340 USB-C（排针可共用） |
| PA27, PA28 | IMU 软件 I2C |
| PB6-PB9 | W25Q128 SPI Flash |
| PB17, PB18 | 2.4G 无线串口 |
| PB21 | ENTER 按键（上拉，低有效） |
| PB22 | 板载 LED（下拉，低有效） |
| PB23 | 无线连接状态 |
| PB26 | WS2812 RGB 灯 |
| PB27 | 无源蜂鸣器 |

完整引脚表见 `skills/tianqiaoxing-g3519/SKILL.md`。

---

## 目录结构

```
skills/tianqiaoxing-g3519/
├── SKILL.md                    # Agent 入口：四步工作流 + 引脚表 + 例程索引
├── config.json                 # 路径配置（setup.py 生成）
├── peripherals/                # 10 个外设参考文档
├── scripts/
│   ├── setup.py                # 首次路径配置
│   ├── scaffold.py             # SDK 例程 -> CCS 工程
│   ├── scaffold_oled.py        # OLED UI 框架 + 可选模块工程
│   ├── build.py                # SysConfig CLI + gmake 编译
│   ├── flash.py                # DSLite 烧录（支持 XDS110 / J-Link）
│   └── serial_console.py       # 串口监视
└── tests/                      # 7 个测试
```

`skills/mspm0-ccs/` 是通用 MSPM0 辅助 skill，包含 SysConfig 静态检查、示例管理、CCS-DSS 调试等工具。

---

## 环境要求

- **IDE**：CCS Theia + TI Arm Clang 4.0.3 LTS
- **SDK**：MSPM0 SDK 2.05.01.00
- **SysConfig**：1.24.0
- **调试器**：XDS110 或 J-Link
- **Python**：3.8+（串口监视需 `pyserial`）

---

## 相关链接

- OLED_UI 框架：[github.com/LaoGuaiGe/OLED_UI](https://github.com/LaoGuaiGe/OLED_UI)
- TI MSPM0 SDK：[ti.com/tool/MSPM0-SDK](https://www.ti.com/tool/MSPM0-SDK)
- 立创天巧星文档：[wiki.lckfb.com](https://wiki.lckfb.com/zh-hans/tmx-mspm0g3507/)

## 开源协议

MIT
