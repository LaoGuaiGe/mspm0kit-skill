#!/usr/bin/env python3
"""Generate a Tianqiaoxing-adapted CCS project from an SDK example."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


def _load_config(config_path: str) -> dict:
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def _copy_and_rename(src: Path, dst: Path, old_name: str, new_name: str) -> None:
    """Copy file, replacing the old project name stem in filename and content."""
    new_stem = src.stem.replace(old_name, new_name)
    dst_file = dst / f"{new_stem}{src.suffix}"
    dst.mkdir(parents=True, exist_ok=True)
    content = src.read_text(encoding="utf-8", errors="replace")
    content = content.replace(old_name, new_name)
    dst_file.write_text(content, encoding="utf-8")


def main(
    project_name: str,
    sdk_example: str,
    output_dir: str | None = None,
    config_path: str | None = None,
    _interactive: bool = True,
) -> Path:
    config = _load_config(
        config_path or str(Path(__file__).resolve().parents[1] / "config.json")
    )
    sdk_examples_dir = Path(config["sdk_examples"])
    source_dir = sdk_examples_dir / sdk_example

    if not source_dir.is_dir():
        raise FileNotFoundError(
            f"SDK example not found: {source_dir}\n"
            f"Available examples under: {sdk_examples_dir}"
        )

    out = Path(output_dir or Path.cwd())
    out.mkdir(parents=True, exist_ok=True)

    # 1. Copy .c source file, rename with project name
    c_files = list(source_dir.glob("*.c"))
    for cf in c_files:
        _copy_and_rename(cf, out, sdk_example, project_name)

    # 2. Copy .syscfg, fix package from LQFP-100(PZ) to LQFP-64(PM)
    syscfg_files = list(source_dir.glob("*.syscfg"))
    for sf in syscfg_files:
        content = sf.read_text(encoding="utf-8", errors="replace")
        content = re.sub(
            r'--package\s+"LQFP-100\(PZ\)"',
            '--package "LQFP-64(PM)"',
            content,
        )
        out_name = sf.name.replace(sdk_example, project_name)
        (out / out_name).write_text(content, encoding="utf-8")

    # 3. Copy ticlang/device_linker.cmd
    ticlang_src = source_dir / "ticlang"
    ticlang_dst = out / "ticlang"
    ticlang_dst.mkdir(exist_ok=True)
    linker_cmd = ticlang_src / "device_linker.cmd"
    if linker_cmd.exists():
        shutil.copy2(linker_cmd, ticlang_dst / "device_linker.cmd")

    # 4. Copy .projectspec from ticlang/, rename and adapt paths
    pspec_files = list(ticlang_src.glob("*.projectspec"))
    for ps in pspec_files:
        content = ps.read_text(encoding="utf-8", errors="replace")
        content = content.replace(
            f"{sdk_example}_LP_MSPM0G3519_nortos_ticlang", project_name
        )
        content = content.replace(sdk_example, project_name)
        content = re.sub(
            r'path="\.\./.*?\.c"', f'path="{project_name}.c"', content
        )
        content = re.sub(
            r'path="\.\./.*?\.syscfg"',
            f'path="{project_name}.syscfg"',
            content,
        )
        content = re.sub(r'path="\.\./README\.md"', 'path="README.md"', content)
        content = re.sub(
            r'path="\.\./README\.html"', 'path="README.html"', content
        )
        content = re.sub(
            r'name=".*?_LP_MSPM0G3519_nortos_ticlang"',
            f'name="{project_name}"',
            content,
        )
        content = re.sub(
            r'title=".*?"', f'title="{project_name}"', content
        )
        (out / f"{project_name}.projectspec").write_text(content, encoding="utf-8")

    return out


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate Tianqiaoxing-adapted CCS project from SDK example"
    )
    parser.add_argument("project_name", help="Name for the new project")
    parser.add_argument("sdk_example", help="SDK example directory name")
    parser.add_argument(
        "--output", "-o", default=None,
        help="Parent output directory (default: current dir)",
    )
    args = parser.parse_args()

    result = main(
        project_name=args.project_name,
        sdk_example=args.sdk_example,
        output_dir=args.output,
    )
    print(f"Project created: {result}")
