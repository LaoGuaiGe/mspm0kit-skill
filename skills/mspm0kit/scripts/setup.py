#!/usr/bin/env python3
"""First-time setup: ask for toolchain paths and write config.json."""
from __future__ import annotations

import json
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parents[1]

DEFAULTS = {
    "ccs_root": r"D:\TI\CCS\ccs",
    "sdk_root": r"D:\TI\CCS\mspm0_sdk_2_05_01_00",
    "sysconfig_cli": r"D:\TI\CCS\ccs\utils\sysconfig_1.24.0\sysconfig_cli.bat",
    "dslite": r"D:\TI\CCS\ccs\ccs_base\DebugServer\bin\DSLite.exe",
    "gmake": r"D:\TI\CCS\ccs\utils\bin\gmake.exe",
    "compiler": r"D:\TI\CCS\ccs\tools\compiler\ti-cgt-armllvm_4.0.3.LTS",
    "sdk_examples": r"D:\TI\CCS\mspm0_sdk_2_05_01_00\examples\nortos\LP_MSPM0G3519\driverlib",
    "probe": "XDS110",
    "oled_ui_source": "",
}


def _prompt(label: str, default: str) -> str:
    value = input(f"{label} [{default}]: ").strip()
    return value if value else default


def main() -> None:
    config_path = CONFIG_DIR / "config.json"
    print("天巧星 MSPM0G3519 Skill — 首次配置")
    print("-" * 40)

    ccs_root = _prompt("CCS 安装目录", DEFAULTS["ccs_root"])
    sdk_root = _prompt("MSPM0 SDK 目录", DEFAULTS["sdk_root"])
    probe = _prompt("调试探针 (XDS110/JLink)", DEFAULTS["probe"])
    oled_ui = _prompt(
        "OLED_UI 仓库路径 (留空跳过，需要时可通过 --source 指定)",
        DEFAULTS["oled_ui_source"],
    )

    config = {
        "ccs_root": ccs_root,
        "sdk_root": sdk_root,
        "sysconfig_cli": DEFAULTS["sysconfig_cli"],
        "dslite": DEFAULTS["dslite"],
        "gmake": DEFAULTS["gmake"],
        "compiler": DEFAULTS["compiler"],
        "sdk_examples": str(
            Path(sdk_root) / "examples/nortos/LP_MSPM0G3519/driverlib"
        ),
        "probe": probe,
        "oled_ui_source": oled_ui,
    }

    config_path.write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\n配置已保存到: {config_path}")


if __name__ == "__main__":
    main()
