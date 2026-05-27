#!/usr/bin/env python3
"""Build a CCS project: SysConfig CLI -> gmake."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _load_config(config_path: str) -> dict:
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def main(
    project_dir: str,
    config_path: str | None = None,
    _interactive: bool = True,
) -> tuple[bool, str]:
    config = _load_config(
        config_path or str(Path(__file__).resolve().parents[1] / "config.json")
    )

    proj = Path(project_dir).resolve()
    syscfg_files = list(proj.glob("*.syscfg"))
    if not syscfg_files:
        return False, f"No .syscfg file found in {proj}"
    syscfg = syscfg_files[0]

    sysconfig_cli = config.get("sysconfig_cli", "sysconfig_cli.bat")
    gmake = config.get("gmake", "gmake")
    sdk_root = config.get("sdk_root", "")

    product_json = str(Path(sdk_root) / ".metadata" / "product.json")

    # Step 1: SysConfig
    if _interactive:
        response = input(
            f"\n是否允许调用 SysConfig CLI? (y/n)\n"
            f"  路径: {sysconfig_cli}\n"
            f"  目标: {syscfg}\n"
        )
        if response.lower() not in ("y", "yes", ""):
            return False, "User declined SysConfig step"

    sysconfig_cmd = [
        sysconfig_cli,
        "--compiler", "ticlang",
        "--product", product_json,
        "--output", str(proj),
        str(syscfg),
    ]

    print(f"[SysConfig] Running: {' '.join(sysconfig_cmd)}")
    result = subprocess.run(
        sysconfig_cmd, capture_output=True, text=True, cwd=str(proj),
    )
    if result.returncode != 0:
        return False, f"SysConfig failed:\n{result.stderr}\n{result.stdout}"

    # Step 2: gmake
    ticlang_dir = proj / "ticlang"
    if not ticlang_dir.is_dir():
        return False, f"ticlang/ directory not found in {proj}"

    if _interactive:
        response = input(
            f"\n是否允许运行 gmake 编译? (y/n)\n"
            f"  目录: {ticlang_dir}\n"
        )
        if response.lower() not in ("y", "yes", ""):
            return False, "User declined gmake step"

    gmake_cmd = [gmake, "-C", str(ticlang_dir)]
    print(f"[gmake] Running: {' '.join(gmake_cmd)}")
    result = subprocess.run(
        gmake_cmd, capture_output=True, text=True, cwd=str(ticlang_dir),
    )

    if result.returncode != 0:
        return False, f"gmake failed:\n{result.stderr}\n{result.stdout}"

    out_files = list(proj.glob("ticlang/*.out"))
    out_path = out_files[0] if out_files else f"{proj}/ticlang/{proj.name}.out"
    return True, str(out_path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build CCS project")
    parser.add_argument("project_dir", help="Path to project directory")
    args = parser.parse_args()

    ok, msg = main(args.project_dir)
    if ok:
        print(f"\nBuild successful\n  Output: {msg}")
    else:
        print(f"\nBuild failed\n{msg}")
        raise SystemExit(1)
