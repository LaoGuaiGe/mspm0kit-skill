---
name: mspm0kit
description: One-sentence CCS project generator for the Tianqiaoxing MSPM0G3519 custom board. Create full CCS projects from SDK examples with automatic pin/package adaptation, then build and flash. Use when the user wants to start a new MSPM0 firmware project on this specific board, or needs pin availability information for the Tianqiaoxing G3519.
---

# mspm0kit — 天巧星 MSPM0G3519 Skill

**Board**: Tianqiaoxing MSPM0G3519 custom development board (LQFP-64)
**Toolchain**: CCS Theia + TI Arm Clang + SysConfig + DriverLib
**SDK**: MSPM0 SDK 2.05.01.00

## Workflow

When the user requests a new project, follow these four steps:

### Step 1 — Think

1. Identify the peripheral(s) the user wants (UART, GPIO, PWM, SPI, I2C, ADC, Timer).
2. Check the pin table below to confirm target pins are available.
3. Read the corresponding `peripherals/<peripheral>.md` for the SDK example name and pin mapping.
4. Confirm clock needs (default: 80 MHz CPUCLK with 40 MHz HFXT).

### Step 2 — Plan

Tell the user what you're going to create:

- Project name and target directory
- Which SDK example will be used as the template
- Which pins will be configured
- Clock configuration (default 80 MHz)

Wait for confirmation before creating files, OR proceed if the user has indicated they want automatic execution.

### Step 3 — Code

1. Ask: "是否允许我读取 SDK 目录（`<sdk_root>`）来复制例程模板？"
2. On approval, run:
   ```
   python scripts/scaffold.py <project_name> <sdk_example_name> -o <cwd>
   ```
3. If the user needs custom behavior beyond the SDK example, edit the generated `.syscfg` and `.c` file.
4. All pin changes go through `.syscfg` — never hand-edit generated `ti_msp_dl_config.*` files.
5. **After scaffold completes, ask the user:** "工程已生成，是否要我帮你编译测试？"
   - If yes → proceed to Step 4 (build + report errors)
   - If no → just print the project path and usage instructions

### Step 4 — Verify

1. Run build:
   ```
   python scripts/build.py <project_dir>
   ```
   This asks for confirmation before each tool invocation (SysConfig CLI, gmake).
2. If build fails: read the error, fix the issue, retry (max 3 times).
3. If build succeeds: report the `.out` file path and provide the flash command.
4. On first build failure, read `ti_msp_dl_config.h` to confirm generated macro names — never guess them.

## Core Rules

- `.syscfg` is the sole source of truth for pins, peripherals, clocks, interrupts, and DMA.
- Prefer SysConfig + DriverLib over register-level code.
- Never edit generated files: `ti_msp_dl_config.c`, `ti_msp_dl_config.h`, `device_linker.cmd`.
- Don't guess generated macro names. Read the generated header after SysConfig runs.
- If SysConfig emits warnings, report them — don't call it "clean".
- If hardware behavior is unverified, say "verification stopped at compile level".
- Every access to external paths (CCS, SDK) requires a permission prompt.

## Project Layering

Generated projects must follow the embedded code layering conventions from the OLED_UI reference project. If unsure about layer placement, ask the user.

### Layer Structure

```
<project>/
├── main.c                     # Entry point: init + main loop
├── <project>.syscfg            # SysConfig: pins, clocks, peripherals
├── app/                        # Application layer
│   └── app_<feature>.c/h       # User-facing app tasks, game logic, UI pages
├── hardware/                   # Hardware abstraction layer (HAL)
│   └── hw_<peripheral>.c/h     # Peripheral drivers (I2C, SPI, PWM, sensors)
├── middle/                     # Middleware layer
│   └── mid_<service>.c/h       # Reusable system services (timer, button, protocol)
└── ticlang/                    # Build output (generated)
```

### Layer Rules

| Layer | Prefix | Responsibility | Depends on |
|-------|--------|---------------|------------|
| `hardware/` | `hw_` | Peripheral drivers, sensor drivers, bit-bang protocols | DriverLib, `ti_msp_dl_config.h` |
| `middle/` | `mid_` | System services, protocol parsers, reusable components | `hardware/` or DriverLib |
| `app/` | `app_` | Application tasks, UI pages, game logic | `hardware/` + `middle/` |

### Key Conventions

- **File naming**: `hw_<peripheral>.c`, `mid_<service>.c`, `app_<feature>.c` — prefix indicates layer
- **No cross-layer back-references**: `hardware/` must not include `middle/` or `app/` headers. `middle/` must not include `app/` headers.
- **SysConfig ownership**: only `main.c` calls `SYSCFG_DL_init()`. Peripheral drivers receive config via generated macros from `ti_msp_dl_config.h`.
- **Single responsibility**: each `.c/.h` pair handles one peripheral or one service
- **Simple projects**: if the project has less than 3 source files, keep everything in root — don't over-layer

### Reference

Full example: `E:\github\OLED_UI\OLED_UI_Examples\MSPM0G3519\ccs\oeldui` (hardware → middle → oledUI → app, 4-layer embedded architecture)

## Pin Table — Tianqiaoxing MSPM0G3519

### Completely Unusable (never assign)

| Pin | Reason |
|-----|--------|
| PA2 | Frequency accuracy control, not routed |
| PA5 | HFXT crystal input (40 MHz) |
| PA6 | HFXT crystal output (40 MHz) |
| PA19 | SWDIO debug interface |
| PA20 | SWCLK debug interface |

### Conditional

| Pin | Condition |
|-----|-----------|
| PA18 | BSL entry pin — must be LOW at reset. Board BACK button (PULL_DOWN) |

### Board Peripheral Pins (occupied, do not reassign)

| Pin(s) | Occupied by |
|--------|-------------|
| PA0, PA1 | Software I2C — OLED (2.2kΩ pull-up on board) |
| PA10, PA11 | UART0 to CH340 USB-C (排针 can share TX/RX) |
| PA27, PA28 | Software I2C — LSM6DS3 IMU |
| PB6, PB7, PB8, PB9 | SPI1 — W25Q128 Flash (CS/MISO/MOSI/SCLK) |
| PB17, PB18 | UART7 — wireless UART module |
| PB21 | ENTER button (PULL_UP, active-low) |
| PB22 | Onboard LED (PULL_DOWN, active-low) |
| PB23 | Wireless link status input |
| PB26 | TIMA1 CCP0 — WS2812 RGB LED |
| PB27 | TIMG6 CCP1 — Buzzer PWM |

### Optional (can release if unused)

| Pin(s) | Function |
|--------|----------|
| PA29, PA30 | QEI encoder (TIMG8 CCP0/CCP1) |
| PA31 | Encoder button (PULL_UP) |

### Free Pins (available for user assignment)

All other pins not listed above. The board uses LQFP-64(PM) package.

## Path Configuration

The skill stores toolchain paths in `config.json`. When the skill needs to access external paths:

1. **CCS directory**: Ask "是否允许我读取 CCS 配置（`<ccs_root>`）？"
2. **SDK directory**: Ask "是否允许我读取 SDK 内容（`<sdk_root>`）？"

If the user declines, use the built-in peripheral reference docs in `peripherals/` as fallback knowledge.

If `config.json` does not exist, run `python scripts/setup.py` first.

## Tools

| Script | Purpose |
|--------|---------|
| `python scripts/setup.py` | First-time path configuration |
| `python scripts/scaffold.py <name> <example> -o <dir>` | Generate CCS project from SDK example |
| `python scripts/build.py <project_dir>` | SysConfig CLI + gmake compile |
| `python scripts/flash.py <project_dir>` | DSLite flash |
| `python scripts/serial_console.py <port> -b <baud>` | Serial monitor |
| `python scripts/scaffold_oled.py <name>` | Generate OLED UI framework project (from local OLED_UI repo) |

## SDK Example Index

### Standard Peripherals (from MSPM0 SDK)

Key SDK examples (under `examples/nortos/LP_MSPM0G3519/driverlib/`):

| Peripheral | SDK Example | Default Pins |
|-----------|-------------|--------------|
| GPIO Output | `gpio_toggle_output` | PB22, PB26, PB27, PB14 |
| UART TX/RX | `uart_rw_multibyte_fifo_poll` | PA10(TX), PA11(RX) |
| UART Console | `uart_tx_console_multibyte_repeated_fifo_dma` | PA10(TX), PA11(RX) |
| UART Echo | `uart_echo_interrupts_standby` | PA10/PA11 |
| SPI Controller | `spi_controller_multibyte_fifo_poll` | PB7, PB8, PB31, PB6 |
| SPI Controller DMA | `spi_controller_fifo_dma_interrupts` | PB7, PB8, PB31, PB6 |
| I2C Controller | `i2c_controller_rw_multibyte_fifo_poll` | PC2(SCL), PC3(SDA) |
| ADC Single | `adc12_single_conversion` | PA14 (ADC0 ch12) |
| ADC Internal Temp | `adc12_internal_temp_sensor_mathacl` | — |
| PWM Timer | `timg_32bit_timer_mode_pwm_edge_sleep` | PB6, PB7 (TIMG12) |
| Timer Periodic | `tima_timer_mode_periodic_repeat_count` | — |
| QEI | `timg_qei_mode` | — |

### OLED UI Framework (from local repo)

When the user asks to "移植屏幕UI" or "add OLED display":

1. Run `python scripts/scaffold_oled.py <project_name>` (not the standard scaffold.py)
2. This copies the minimal OLED UI framework from the local `OLED_UI` repo
3. Optional modules: `--with-imu`, `--with-ws2812`, `--with-wireless` (can be combined)
4. Does NOT include: games, external Flash fonts
5. Reference: `peripherals/oled_ui.md` for API, `peripherals/imu.md` / `ws2812.md` / `wireless_uart.md` for modules

## External Modules

When asked to drive an external sensor, motor, display, or radio:

- Ask for: datasheet, schematic, pin map, supply voltage, logic level, protocol, key timing.
- Before blaming code: check power, ground, pull-ups, level shifting, reset/enable pins, TX/RX crossover, I2C address, SPI mode, PWM polarity, shared pins.
- After repeated failures with correct SysConfig + build + flash: suggest checking wiring, power, module mode, datasheet mismatch.
- Separate "firmware looks correct" from "hardware proved correct".

## Reference

For detailed SysConfig/DriverLib usage and debugging, also refer to the `mspm0-ccs` skill's reference docs.
