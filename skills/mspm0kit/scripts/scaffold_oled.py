#!/usr/bin/env python3
"""Thin wrapper: scaffold OLED projects from bundled skill examples (no external repo needed)."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SCAFFOLD = SKILL_DIR / "scripts" / "scaffold.py"

# Module-file lists (filenames only — all in root)
IMU_C_FILES = ["hw_lsm6ds3.c", "FusionAhrs.c", "FusionOffset.c"]
WS2812_C_FILES = ["hw_ws2812.c", "hw_ws2812_effects.c"]
WIRELESS_C_FILES = ["mid_wireless_uart.c"]
TIMER_C_FILES = ["mid_timer.c"]

# SysConfig addons
SYSCFG_HW_I2C = """
const I2C  = scripting.addModule("/ti/driverlib/I2C", {}, false);
const I2C1 = I2C.addInstance();
I2C1.$name = "I2C_0"; I2C1.peripheral.$assign = "I2C0";
I2C1.peripheral.sdaPin.$assign = "PA0"; I2C1.peripheral.sclPin.$assign = "PA1";
"""

SYSCFG_TIMER = """
const TIMER  = scripting.addModule("/ti/driverlib/TIMER", {}, false);
const TIMER1 = TIMER.addInstance();
TIMER1.timerClkDiv = 8; TIMER1.timerClkPrescale = 10;
TIMER1.timerStartTimer = true; TIMER1.timerMode = "PERIODIC";
TIMER1.interrupts = ["ZERO"]; TIMER1.interruptPriority = "3";
TIMER1.$name = "TIMER_TICK"; TIMER1.timerPeriod = "5 ms";
TIMER1.peripheral.$assign = "TIMA0";
"""

SYSCFG_WS2812 = """
const PWM_WS = scripting.addModule("/ti/driverlib/PWM", {}, false);
const PWM_WS1 = PWM_WS.addInstance();
PWM_WS1.$name = "WS2812"; PWM_WS1.pwmMode = "EDGE_ALIGN_UP";
PWM_WS1.ccIndex = [0]; PWM_WS1.timerCount = 100; PWM_WS1.timerStartTimer = true;
PWM_WS1.peripheral.$assign = "TIMA1"; PWM_WS1.peripheral.ccp0Pin.$assign = "PB26";
PWM_WS1.ccp0PinConfig.direction = scripting.forceWrite("OUTPUT");
PWM_WS1.ccp0PinConfig.hideOutputInversion = scripting.forceWrite(false);
PWM_WS1.ccp0PinConfig.onlyInternalResistor = scripting.forceWrite(false);
PWM_WS1.ccp0PinConfig.passedPeripheralType = scripting.forceWrite("Digital");
PWM_WS1.PWM_CHANNEL_0.initVal = "HIGH";
PWM_WS1.PWM_CHANNEL_0.shadowUpdateMode = "ZERO_EVT";
"""

SYSCFG_WIRELESS = """
const UART_WL = scripting.addModule("/ti/driverlib/UART", {}, false);
const UART_WL1 = UART_WL.addInstance();
UART_WL1.$name = "UART_WIRELESS"; UART_WL1.enabledInterrupts = ["RX"];
UART_WL1.peripheral.$assign = "UART7";
UART_WL1.peripheral.rxPin.$assign = "PB18"; UART_WL1.peripheral.txPin.$assign = "PB17";
UART_WL1.txPinConfig.direction = scripting.forceWrite("OUTPUT");
UART_WL1.txPinConfig.hideOutputInversion = scripting.forceWrite(false);
UART_WL1.txPinConfig.onlyInternalResistor = scripting.forceWrite(false);
UART_WL1.txPinConfig.passedPeripheralType = scripting.forceWrite("Digital");
UART_WL1.rxPinConfig.hideOutputInversion = scripting.forceWrite(false);
UART_WL1.rxPinConfig.onlyInternalResistor = scripting.forceWrite(false);
UART_WL1.rxPinConfig.passedPeripheralType = scripting.forceWrite("Digital");
"""


def _load_config() -> dict:
    cfg = SKILL_DIR / "config.json"
    if cfg.exists():
        return json.loads(cfg.read_text(encoding="utf-8"))
    return {}


def _copy_bundled_driver(out: Path, files: list[str], dst: Path) -> list[str]:
    """Copy .c files from bundled examples, searching all example dirs."""
    entries = []
    examples_root = SKILL_DIR / "examples"
    for name in files:
        found = None
        # Search all bundled example directories for the file
        for ex_dir in examples_root.iterdir():
            if ex_dir.is_dir() and (ex_dir / name).is_file():
                found = ex_dir / name
                break
        if found:
            shutil.copy2(found, dst / name)
            entries.append(f'        <file path="{name}" openOnCreation="false" excludeFromBuild="false" action="copy"/>')
    return entries


def main(
    project_name: str,
    output_dir: str | None = None,
    mode: str = "draw",
    use_hw_i2c: bool = False,
    with_imu: bool = False,
    with_ws2812: bool = False,
    with_wireless: bool = False,
) -> Path:
    example_name = "oled_menu" if mode == "menu" else "oled_draw"

    # 1. Run scaffold.py for the base OLED example
    cmd = [sys.executable, str(SCAFFOLD), project_name, example_name]
    if output_dir:
        cmd.extend(["-o", output_dir])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr)
        sys.exit(1)
    print(result.stdout.strip())

    out = (Path(output_dir) if output_dir else Path.cwd()) / project_name
    if not out.is_dir():
        print(f"ERROR: scaffold did not create {out}")
        sys.exit(1)

    syscfg_addon = ""
    extra_entries = []
    src_examples = SKILL_DIR / "examples" / example_name
    need_timer = with_imu or with_ws2812

    # 2. Optional modules (search all bundled examples for .c files)
    if with_imu:
        extra_entries += _copy_bundled_driver(out, IMU_C_FILES, out)
    if with_ws2812:
        extra_entries += _copy_bundled_driver(out, WS2812_C_FILES, out)
        syscfg_addon += SYSCFG_WS2812
    if with_wireless:
        extra_entries += _copy_bundled_driver(out, WIRELESS_C_FILES, out)
        syscfg_addon += SYSCFG_WIRELESS
    if need_timer:
        extra_entries += _copy_bundled_driver(out, TIMER_C_FILES, out)
        syscfg_addon += SYSCFG_TIMER
    if use_hw_i2c:
        syscfg_addon += SYSCFG_HW_I2C

    # 3. Append syscfg addons
    if syscfg_addon:
        syscfg_file = out / f"{project_name}.syscfg"
        syscfg_file.write_text(
            syscfg_file.read_text(encoding="utf-8") + syscfg_addon, encoding="utf-8"
        )

    # 4. Append projectspec entries
    if extra_entries:
        pspec_file = out / f"{project_name}.projectspec"
        content = pspec_file.read_text(encoding="utf-8")
        content = content.replace("</project>", "\n".join(extra_entries) + "\n    </project>")
        pspec_file.write_text(content, encoding="utf-8")

    return out


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Scaffold OLED UI project (uses bundled examples, no external repo)")
    p.add_argument("project_name", help="Project name")
    p.add_argument("-o", "--output", default=None)
    p.add_argument("--mode", default="draw", choices=["draw", "menu"])
    p.add_argument("--i2c", default="sw", choices=["sw", "hw"])
    p.add_argument("--with-imu", action="store_true")
    p.add_argument("--with-ws2812", action="store_true")
    p.add_argument("--with-wireless", action="store_true")
    args = p.parse_args()

    result = main(
        project_name=args.project_name,
        output_dir=args.output,
        mode=args.mode,
        use_hw_i2c=(args.i2c == "hw"),
        with_imu=args.with_imu,
        with_ws2812=args.with_ws2812,
        with_wireless=args.with_wireless,
    )

    modules = []
    if args.with_imu: modules.append("IMU")
    if args.with_ws2812: modules.append("WS2812")
    if args.with_wireless: modules.append("Wireless")
    i2c_note = " (hardware I2C)" if args.i2c == "hw" else ""

    print(f"OLED UI project ({args.mode}{i2c_note}): {result}")
    if modules:
        print(f"  Modules: {', '.join(modules)}")
    print(f"  Import: CCS -> Import -> CCS Projects from .projectspec -> {result}/{args.project_name}.projectspec")
