#!/usr/bin/env python3
"""Generate a minimal OLED UI framework project for Tianqiaoxing G3519."""
from __future__ import annotations

import json
import shutil
from pathlib import Path


def _load_config(config_path: str) -> dict:
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)

def _find_source(source: str | None, config: dict) -> Path:
    """Find OLED_UI source: explicit --source arg, then config.json, then fail."""
    if source:
        p = Path(source)
        if p.is_dir() and (p / "oledUI" / "OLED.c").exists():
            return p

    cfg_path = config.get("oled_ui_source", "")
    if cfg_path:
        p = Path(cfg_path)
        if p.is_dir() and (p / "oledUI" / "OLED.c").exists():
            return p

    raise FileNotFoundError(
        "Cannot find OLED_UI repo.\n"
        "Options:\n"
        "  1. Run setup.py to configure the path\n"
        "  2. Pass --source <path> to this script\n"
        "  3. Clone from https://github.com/LaoGuaiGe/OLED_UI"
    )


# ── template files written directly (self-contained, no external template dir) ──

APP_TASK_STUB_H = """\
#ifndef APP_TASK_STUB_H
#define APP_TASK_STUB_H
#include "stdbool.h"
#include "stdint.h"
typedef enum {
    APP_STATE_IDLE,
    APP_STATE_FADE_IN,
    APP_STATE_RUNNING,
    APP_STATE_FADE_OUT,
} AppState;
typedef struct {
    void (*init)(void);
    void (*tick)(void);
    void (*sample)(void);
    bool (*should_exit)(void);
    void (*on_exit)(void);
    void (*fade_tick)(int8_t level);
    int8_t fade_steps;
    uint32_t frame_interval_ms;
} AppTaskDef;
void     app_task_start(const AppTaskDef *app);
void     app_task_stop(void);
void     app_task_tick(void);
bool     app_task_is_active(void);
AppState app_task_get_state(void);
#endif
"""

APP_TASK_STUB_C = """\
#include "app_task_stub.h"
static const AppTaskDef *current_app = NULL;
void app_task_start(const AppTaskDef *app)  { current_app = app; if (app && app->init) app->init(); }
void app_task_stop(void)                    { if (current_app && current_app->on_exit) current_app->on_exit(); current_app = NULL; }
void app_task_tick(void)                    { if (current_app && current_app->tick) current_app->tick(); }
bool app_task_is_active(void)               { return current_app != NULL; }
AppState app_task_get_state(void)           { return current_app ? APP_STATE_RUNNING : APP_STATE_IDLE; }
"""

HW_ENCODER_STUB_H = """\
#ifndef HW_ENCODER_STUB_H
#define HW_ENCODER_STUB_H
#include "stdint.h"
void     HW_Encoder_Init(void)    {}
void     HW_Encoder_Enable(void)  {}
void     HW_Encoder_Disable(void) {}
int16_t  HW_Encoder_GetDelta(void){ return 0; }
#endif
"""

MID_TIMER_STUB_H = """\
#ifndef __MID_TIMER_STUB_H__
#define __MID_TIMER_STUB_H__
#include "ti_msp_dl_config.h"
#include "stdint.h"
void     timer_init(void);
void     enable_task_interrupt(void);
void     disable_task_interrupt(void);
uint32_t get_sys_tick_ms(void);
#endif
"""

MID_TIMER_STUB_C = """\
#include "mid_timer_stub.h"
static volatile uint32_t sys_tick_ms = 0;
void timer_init(void) {
    NVIC_ClearPendingIRQ(TIMER_TICK_INST_INT_IRQN);
    NVIC_EnableIRQ(TIMER_TICK_INST_INT_IRQN);
}
void TIMER_TICK_INST_IRQHandler(void) {
    if (DL_TimerA_getPendingInterrupt(TIMER_TICK_INST) == DL_TIMER_IIDX_ZERO) {
        sys_tick_ms += 5;
    }
}
void enable_task_interrupt(void)  {}
void disable_task_interrupt(void) {}
uint32_t get_sys_tick_ms(void)    { return sys_tick_ms; }
"""

# ── Syscfg additions for each module ──

SYSCFG_IMU_ADDON = """
/* ---- IMU I2C: PA28=SDA, PA27=SCL ---- */
const GPIO2  = GPIO.addInstance();
GPIO2.$name                          = "IMU";
GPIO2.associatedPins.create(2);
GPIO2.associatedPins[0].$name        = "SDA";
GPIO2.associatedPins[0].initialValue = "SET";
GPIO2.associatedPins[0].assignedPort = "PORTA";
GPIO2.associatedPins[0].assignedPin  = "28";
GPIO2.associatedPins[0].pin.$assign  = "PA28";
GPIO2.associatedPins[1].$name        = "SCL";
GPIO2.associatedPins[1].initialValue = "SET";
GPIO2.associatedPins[1].assignedPort = "PORTA";
GPIO2.associatedPins[1].assignedPin  = "27";
GPIO2.associatedPins[1].pin.$assign  = "PA27";
"""

SYSCFG_WS2812_ADDON = """
/* ---- WS2812: TIMA1 CCP0 on PB26 ---- */
const PWM    = scripting.addModule("/ti/driverlib/PWM", {}, false);
const PWM1   = PWM.addInstance();
PWM1.$name                              = "WS2812";
PWM1.pwmMode                            = "EDGE_ALIGN_UP";
PWM1.ccIndex                            = [0];
PWM1.timerCount                         = 100;
PWM1.timerStartTimer                    = true;
PWM1.peripheral.$assign                 = "TIMA1";
PWM1.peripheral.ccp0Pin.$assign         = "PB26";
PWM1.ccp0PinConfig.direction            = scripting.forceWrite("OUTPUT");
PWM1.ccp0PinConfig.hideOutputInversion  = scripting.forceWrite(false);
PWM1.ccp0PinConfig.onlyInternalResistor = scripting.forceWrite(false);
PWM1.ccp0PinConfig.passedPeripheralType = scripting.forceWrite("Digital");
PWM1.PWM_CHANNEL_0.initVal              = "HIGH";
PWM1.PWM_CHANNEL_0.shadowUpdateMode     = "ZERO_EVT";
"""

SYSCFG_TIMER_ADDON = """
/* ---- System Tick: TIMA0 5ms periodic ---- */
const TIMER  = scripting.addModule("/ti/driverlib/TIMER", {}, false);
const TIMER1 = TIMER.addInstance();
TIMER1.timerClkDiv        = 8;
TIMER1.timerClkPrescale   = 10;
TIMER1.timerStartTimer    = true;
TIMER1.timerMode          = "PERIODIC";
TIMER1.interrupts         = ["ZERO"];
TIMER1.interruptPriority  = "3";
TIMER1.$name              = "TIMER_TICK";
TIMER1.timerPeriod        = "5 ms";
TIMER1.peripheral.$assign = "TIMA0";
"""

SYSCFG_WIRELESS_ADDON = """
/* ---- Wireless UART: UART7 on PB17(TX)/PB18(RX) ---- */
const UART   = scripting.addModule("/ti/driverlib/UART", {}, false);
const UART1  = UART.addInstance();
UART1.$name                            = "UART_WIRELESS";
UART1.enabledInterrupts                = ["RX"];
UART1.peripheral.$assign               = "UART7";
UART1.peripheral.rxPin.$assign         = "PB18";
UART1.peripheral.txPin.$assign         = "PB17";
UART1.txPinConfig.direction            = scripting.forceWrite("OUTPUT");
UART1.txPinConfig.hideOutputInversion  = scripting.forceWrite(false);
UART1.txPinConfig.onlyInternalResistor = scripting.forceWrite(false);
UART1.txPinConfig.passedPeripheralType = scripting.forceWrite("Digital");
UART1.rxPinConfig.hideOutputInversion  = scripting.forceWrite(false);
UART1.rxPinConfig.onlyInternalResistor = scripting.forceWrite(false);
UART1.rxPinConfig.passedPeripheralType = scripting.forceWrite("Digital");
"""

# Minimal MenuData — one "Hello World" root page, no app/hardware deps
MENU_DATA_C = """\
#include "OLED_UI_MenuData.h"
#include "OLED_UI.h"

/* ---- 单页面菜单项 ---- */
MenuItem MainMenuItems[] = {
    {.General_item_text = "Hello TianQiaoXing!", .General_callback = NULL,
     .General_SubMenuPage = NULL, .List_BoolRadioBox = NULL},
    {.General_item_text = "OLED_UI Framework", .General_callback = NULL,
     .General_SubMenuPage = NULL, .List_BoolRadioBox = NULL},
    {.General_item_text = "SSD1312 128x64", .General_callback = NULL,
     .General_SubMenuPage = NULL, .List_BoolRadioBox = NULL},
    {.General_item_text = NULL},  /* end marker */
};

#define SPEED 10

MenuPage MainMenuPage = {
    .General_MenuType         = MENU_TYPE_LIST,
    .General_CursorStyle      = REVERSE_ROUNDRECTANGLE,
    .General_FontSize         = OLED_UI_FONT_12,
    .General_ParentMenuPage   = NULL,
    .General_LineSpace        = 4,
    .General_MoveStyle        = UNLINEAR,
    .General_MovingSpeed      = SPEED,
    .General_ShowAuxiliaryFunction = NULL,
    .General_MenuItems        = MainMenuItems,
    .List_MenuArea            = {1, 1, 127, 63},
    .List_IfDrawFrame         = false,
    .List_IfDrawLinePerfix    = true,
    .List_StartPointX         = 4,
    .List_StartPointY         = 2,
};
"""

MAIN_C_TEMPLATE = """\
#include "ti_msp_dl_config.h"
#include "OLED_UI.h"

extern MenuPage MainMenuPage;

int main(void)
{
    SYSCFG_DL_init();

    OLED_Init();
    OLED_Clear();
    OLED_ShowString(0, 0, "OLED UI Framework", 12);
    OLED_ShowString(0, 16, "TianQiaoXing G3519", 12);
    OLED_Update();
    delay_cycles(16000000);  /* ~200ms at 80MHz */

    OLED_UI_Init(&MainMenuPage);

    while (1) {
        OLED_UI_MainLoop();
    }
}
"""

SYSCFG_TEMPLATE = """\
/**
 * @cliArgs --device "MSPM0G351X" --part "Default" --package "LQFP-64(PM)" --product "mspm0_sdk@2.05.01.01"
 * @v2CliArgs --device "MSPM0G3519" --package "LQFP-64(PM)" --product "mspm0_sdk@2.05.01.01"
 * @versions {"tool":"1.24.0+4110"}
 */

const GPIO   = scripting.addModule("/ti/driverlib/GPIO", {}, false);
const GPIO1  = GPIO.addInstance();
const SYSCTL = scripting.addModule("/ti/driverlib/SYSCTL");

/* ---- 80 MHz clock tree: 40 MHz HFXT - SYSPLL - 80 MHz CPUCLK ---- */
SYSCTL.forceDefaultClkConfig = true;
SYSCTL.clockTreeEn           = true;
scripting.suppress("For best practices when the CPUCLK is running at 32MHz and above, clear the flash status bit using DL_FlashCTL_executeClearStatus\\\\(\\\\) before executing any flash operation\\\\. Otherwise there may be false positives\\\\.", SYSCTL);

const divider9       = system.clockTree["UDIV"];
divider9.divideValue = 2;

const multiplier2         = system.clockTree["PLL_QDIV"];
multiplier2.multiplyValue = 4;

const mux4       = system.clockTree["EXHFMUX"];
mux4.inputSelect = "EXHFMUX_XTAL";

const mux8       = system.clockTree["HSCLKMUX"];
mux8.inputSelect = "HSCLKMUX_SYSPLL0";

const mux12       = system.clockTree["SYSPLLMUX"];
mux12.inputSelect = "zSYSPLLMUX_HFCLK";

const pinFunction4                        = system.clockTree["HFXT"];
pinFunction4.inputFreq                    = 40;
pinFunction4.enable                       = true;
pinFunction4.HFXTStartup                  = 10;
pinFunction4.HFCLKMonitor                 = true;
pinFunction4.peripheral.$assign           = "SYSCTL";
pinFunction4.peripheral.hfxInPin.$assign  = "PA5";
pinFunction4.peripheral.hfxOutPin.$assign = "PA6";

/* ---- Board: SWD debug ---- */
const Board                       = scripting.addModule("/ti/driverlib/Board", {}, false);
Board.peripheral.$assign          = "DEBUGSS";
Board.peripheral.swclkPin.$assign = "PA20";
Board.peripheral.swdioPin.$assign = "PA19";

/* ---- OLED I2C: PA0=SDA, PA1=SCL ---- */
GPIO1.$name                              = "OLED";
GPIO1.associatedPins.create(2);
GPIO1.associatedPins[0].$name            = "SDA";
GPIO1.associatedPins[0].initialValue     = "SET";
GPIO1.associatedPins[0].assignedPort     = "PORTA";
GPIO1.associatedPins[0].assignedPin      = "0";
GPIO1.associatedPins[0].ioStructure      = "OD";
GPIO1.associatedPins[0].pin.$assign      = "PA0";
GPIO1.associatedPins[1].$name            = "SCL";
GPIO1.associatedPins[1].initialValue     = "SET";
GPIO1.associatedPins[1].assignedPort     = "PORTA";
GPIO1.associatedPins[1].assignedPin      = "1";
GPIO1.associatedPins[1].ioStructure      = "OD";
GPIO1.associatedPins[1].pin.$assign      = "PA1";

const ProjectConfig              = scripting.addModule("/ti/project_config/ProjectConfig", {}, false);
ProjectConfig.migrationCondition = true;
"""

PROJECTSPEC_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<projectSpec>
    <applicability>
        <when>
            <context deviceFamily="ARM" deviceId="MSPM0G3519"/>
        </when>
    </applicability>
    <project
        title="{project_name}"
        name="{project_name}"
        configurations="Debug"
        toolChain="TICLANG"
        connection="TIXDS110_Connection.xml"
        device="MSPM0G3519"
        ignoreDefaultDeviceSettings="true"
        ignoreDefaultCCSSettings="true"
        products="MSPM0-SDK;sysconfig"
        compilerBuildOptions="
            -I${{PROJECT_ROOT}}
            -I${{PROJECT_ROOT}}/${{ConfigName}}
            -I${{PROJECT_ROOT}}/oledUI
            -I${{PROJECT_ROOT}}/hardware
            -I${{PROJECT_ROOT}}/app
            -I${{PROJECT_ROOT}}/middle
            -O2
            @device.opt
            -I${{COM_TI_MSPM0_SDK_INSTALL_DIR}}/source/third_party/CMSIS/Core/Include
            -I${{COM_TI_MSPM0_SDK_INSTALL_DIR}}/source
            -gdwarf-3
            -mcpu=cortex-m0plus
            -march=thumbv6m
            -mfloat-abi=soft
            -mthumb
        "
        linkerBuildOptions="
            -ldevice.cmd.genlibs
            -L${{COM_TI_MSPM0_SDK_INSTALL_DIR}}/source
            -L${{PROJECT_ROOT}}
            -L${{PROJECT_BUILD_DIR}}/syscfg
            -Wl,--rom_model
            -Wl,--warn_sections
            -L${{CG_TOOL_ROOT}}/lib
            -llibc.a
        "
        sysConfigBuildOptions="
            --output .
            --product ${{COM_TI_MSPM0_SDK_INSTALL_DIR}}/.metadata/product.json
            --compiler ticlang
        "
        sourceLookupPath="${{COM_TI_MSPM0_SDK_INSTALL_DIR}}/source/ti/driverlib"
        description="OLED UI Framework for Tianqiaoxing MSPM0G3519">
        <property name="buildProfile" value="release"/>
        <property name="isHybrid" value="true"/>
        <file path="main.c" openOnCreation="true" excludeFromBuild="false" action="copy"/>
        <file path="{project_name}.syscfg" openOnCreation="true" excludeFromBuild="false" action="copy"/>
        <file path="oledUI/OLED.c" openOnCreation="false" excludeFromBuild="false" action="copy"/>
        <file path="oledUI/OLED_driver.c" openOnCreation="false" excludeFromBuild="false" action="copy"/>
        <file path="oledUI/OLED_Fonts.c" openOnCreation="false" excludeFromBuild="false" action="copy"/>
        <file path="oledUI/OLED_UI.c" openOnCreation="false" excludeFromBuild="false" action="copy"/>
        <file path="oledUI/OLED_UI_Driver.c" openOnCreation="false" excludeFromBuild="false" action="copy"/>
        <file path="oledUI/OLED_UI_MenuData.c" openOnCreation="false" excludeFromBuild="false" action="copy"/>
        <file path="hardware/myiic.c" openOnCreation="false" excludeFromBuild="false" action="copy"/>
        <file path="hardware/hw_delay.c" openOnCreation="false" excludeFromBuild="false" action="copy"/>
        <file path="app/app_task_stub.c" openOnCreation="false" excludeFromBuild="false" action="copy"/>
{extra_file_entries}
    </project>
</projectSpec>
"""


def _trim_file(src: Path, dst: Path, remove_includes: list[str], remove_funcs: list[str] | None = None) -> None:
    """Copy a file, removing specified #include lines and optional function bodies."""
    lines = src.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    result = []
    for line in lines:
        stripped = line.strip()
        skip = False
        for pat in remove_includes:
            if pat in stripped:
                skip = True
                break
        if not skip:
            result.append(line)
    dst.write_text("".join(result), encoding="utf-8")


def main(
    project_name: str,
    output_dir: str | None = None,
    source: str | None = None,
    config_path: str | None = None,
    with_imu: bool = False,
    with_ws2812: bool = False,
    with_wireless: bool = False,
) -> Path:
    cfg_file = config_path or str(Path(__file__).resolve().parents[1] / "config.json")
    config = _load_config(cfg_file) if Path(cfg_file).exists() else {}
    src_root = _find_source(source, config)
    out = Path(output_dir or Path.cwd()) / project_name
    out.mkdir(parents=True, exist_ok=True)

    need_timer = with_imu or with_ws2812
    extra_files = ""
    syscfg_addon = ""

    # ── directories ──
    for d in ["oledUI", "hardware", "app", "middle", "ticlang"]:
        (out / d).mkdir(exist_ok=True)

    # ── 1. Copy as-is: core OLED files ──
    for stem in ["OLED.c", "OLED.h", "OLED_driver.c", "OLED_driver.h",
                  "OLED_Fonts.c", "OLED_Fonts.h", "OLED_UI.h", "OLED_UI_MenuData.h"]:
        shutil.copy2(src_root / "oledUI" / stem, out / "oledUI" / stem)

    # ── 2. Copy & trim: OLED_UI.c ──
    _trim_file(
        src_root / "oledUI" / "OLED_UI.c",
        out / "oledUI" / "OLED_UI.c",
        remove_includes=['#include "app_task.h"'],
    )

    # ── 3. Copy & trim: OLED_UI_Driver.c ──
    _trim_file(
        src_root / "oledUI" / "OLED_UI_Driver.c",
        out / "oledUI" / "OLED_UI_Driver.c",
        remove_includes=['#include "hw_encoder.h"'],
    )

    # ── 4. Minimal MenuData ──
    (out / "oledUI" / "OLED_UI_MenuData.c").write_text(MENU_DATA_C, encoding="utf-8")

    # ── 5. Hardware deps ──
    shutil.copy2(src_root / "hardware" / "myiic.c", out / "hardware" / "myiic.c")
    shutil.copy2(src_root / "hardware" / "myiic.h", out / "hardware" / "myiic.h")
    shutil.copy2(src_root / "hardware" / "hw_delay.c", out / "hardware" / "hw_delay.c")
    shutil.copy2(src_root / "hardware" / "hw_delay.h", out / "hardware" / "hw_delay.h")

    # ── 6. Stub files ──
    (out / "app" / "app_task_stub.h").write_text(APP_TASK_STUB_H, encoding="utf-8")
    (out / "app" / "app_task_stub.c").write_text(APP_TASK_STUB_C, encoding="utf-8")
    (out / "hardware" / "hw_encoder_stub.h").write_text(HW_ENCODER_STUB_H, encoding="utf-8")

    # ── 7. Add #include "app_task_stub.h" to OLED_UI.c ──
    ui_c = (out / "oledUI" / "OLED_UI.c").read_text(encoding="utf-8")
    ui_c = '#include "app_task_stub.h"\n' + ui_c
    (out / "oledUI" / "OLED_UI.c").write_text(ui_c, encoding="utf-8")

    # ── 7b. Optional modules ──

    if with_imu:
        shutil.copy2(src_root / "hardware" / "hw_lsm6ds3.c", out / "hardware" / "hw_lsm6ds3.c")
        shutil.copy2(src_root / "hardware" / "hw_lsm6ds3.h", out / "hardware" / "hw_lsm6ds3.h")
        for f in ["FusionAhrs.c", "FusionAhrs.h", "FusionOffset.c", "FusionOffset.h",
                   "FusionConvention.h", "FusionMath.h"]:
            shutil.copy2(src_root / "middle" / f, out / "middle" / f)
        syscfg_addon += SYSCFG_IMU_ADDON
        extra_files += '\n        <file path="hardware/hw_lsm6ds3.c" openOnCreation="false" excludeFromBuild="false" action="copy"/>'
        extra_files += '\n        <file path="middle/FusionAhrs.c" openOnCreation="false" excludeFromBuild="false" action="copy"/>'
        extra_files += '\n        <file path="middle/FusionOffset.c" openOnCreation="false" excludeFromBuild="false" action="copy"/>'

    if with_ws2812:
        shutil.copy2(src_root / "hardware" / "hw_ws2812.c", out / "hardware" / "hw_ws2812.c")
        shutil.copy2(src_root / "hardware" / "hw_ws2812.h", out / "hardware" / "hw_ws2812.h")
        shutil.copy2(src_root / "hardware" / "hw_ws2812_effects.c", out / "hardware" / "hw_ws2812_effects.c")
        shutil.copy2(src_root / "hardware" / "hw_ws2812_effects.h", out / "hardware" / "hw_ws2812_effects.h")
        syscfg_addon += SYSCFG_WS2812_ADDON
        extra_files += '\n        <file path="hardware/hw_ws2812.c" openOnCreation="false" excludeFromBuild="false" action="copy"/>'
        extra_files += '\n        <file path="hardware/hw_ws2812_effects.c" openOnCreation="false" excludeFromBuild="false" action="copy"/>'

    if with_wireless:
        shutil.copy2(src_root / "middle" / "mid_wireless_uart.c", out / "middle" / "mid_wireless_uart.c")
        shutil.copy2(src_root / "middle" / "mid_wireless_uart.h", out / "middle" / "mid_wireless_uart.h")
        syscfg_addon += SYSCFG_WIRELESS_ADDON
        extra_files += '\n        <file path="middle/mid_wireless_uart.c" openOnCreation="false" excludeFromBuild="false" action="copy"/>'

    if need_timer:
        (out / "middle" / "mid_timer_stub.h").write_text(MID_TIMER_STUB_H, encoding="utf-8")
        (out / "middle" / "mid_timer_stub.c").write_text(MID_TIMER_STUB_C, encoding="utf-8")
        syscfg_addon += SYSCFG_TIMER_ADDON
        extra_files += '\n        <file path="middle/mid_timer_stub.c" openOnCreation="false" excludeFromBuild="false" action="copy"/>'

    # ── 8. Generated files ──
    (out / "main.c").write_text(MAIN_C_TEMPLATE, encoding="utf-8")
    syscfg_content = SYSCFG_TEMPLATE + syscfg_addon
    (out / f"{project_name}.syscfg").write_text(syscfg_content, encoding="utf-8")

    # ── 9. device_linker.cmd ──
    linker_src = src_root / "ticlang" / "device_linker.cmd"
    if linker_src.exists():
        shutil.copy2(linker_src, out / "ticlang" / "device_linker.cmd")
    else:
        sdk_examples = config.get("sdk_examples", "")
        sdk_cmd = Path(sdk_examples) / "gpio_toggle_output" / "ticlang" / "device_linker.cmd" if sdk_examples else None
        if sdk_cmd and sdk_cmd.exists():
            shutil.copy2(sdk_cmd, out / "ticlang" / "device_linker.cmd")

    # ── 10. projectspec ──
    pspec = PROJECTSPEC_TEMPLATE.format(
        project_name=project_name,
        extra_file_entries=extra_files,
    )
    (out / f"{project_name}.projectspec").write_text(pspec, encoding="utf-8")

    return out


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Scaffold OLED UI framework project for Tianqiaoxing G3519")
    p.add_argument("project_name", help="Project name")
    p.add_argument("-o", "--output", default=None, help="Parent output dir (default: cwd)")
    p.add_argument("--source", default=None, help="Path to OLED_UI repo")
    p.add_argument("--with-imu", action="store_true", help="Add LSM6DS3 IMU driver + FusionAhrs")
    p.add_argument("--with-ws2812", action="store_true", help="Add WS2812 RGB LED driver + effects")
    p.add_argument("--with-wireless", action="store_true", help="Add wireless UART module (UART7)")
    args = p.parse_args()

    result = main(
        project_name=args.project_name,
        output_dir=args.output,
        source=args.source,
        with_imu=args.with_imu,
        with_ws2812=args.with_ws2812,
        with_wireless=args.with_wireless,
    )

    modules = []
    if args.with_imu: modules.append("IMU")
    if args.with_ws2812: modules.append("WS2812")
    if args.with_wireless: modules.append("Wireless UART")

    print(f"OLED UI project created: {result}")
    if modules:
        print(f"  Modules enabled: {', '.join(modules)}")
    print(f"  Import in CCS: File → Import → CCS Projects from .projectspec")
    print(f"  Select: {result}/{args.project_name}.projectspec")
