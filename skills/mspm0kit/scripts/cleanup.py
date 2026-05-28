#!/usr/bin/env python3
"""Clean up a CCS project before building — fix common AI-generated mistakes."""
from __future__ import annotations

import sys
from pathlib import Path


def main(project_dir: str) -> int:
    proj = Path(project_dir).resolve()
    if not proj.is_dir():
        print(f"ERROR: {proj} not found")
        return 1

    fixed = 0

    # 1. Move .c files from subdirectories to root, remove duplicates
    c_in_subdirs = []
    for d in proj.iterdir():
        if not d.is_dir() or d.name in ("Debug", "ticlang", "targetConfigs"):
            continue
        for cf in d.glob("*.c"):
            c_in_subdirs.append(cf)

    for cf in c_in_subdirs:
        root_file = proj / cf.name
        if root_file.exists():
            # Compare: if same content, delete subdir copy; if different, keep root
            if cf.read_text() == root_file.read_text():
                cf.unlink()
                print(f"[dup] removed: {cf.relative_to(proj)} (same as root)")
                fixed += 1
            else:
                print(f"[warn] {cf.relative_to(proj)} differs from root — keeping both, review manually")
        else:
            # Move to root
            cf.rename(root_file)
            print(f"[move] {cf.relative_to(proj)} -> {root_file.name}")
            fixed += 1

    # 2. Remove generated files that belong in Debug/
    for name in ["device_linker.cmd", "device.cmd.genlibs", "device.opt",
                  "ti_msp_dl_config.c", "ti_msp_dl_config.h"]:
        gen_file = proj / name
        if gen_file.exists():
            gen_file.unlink()
            print(f"[gen] removed root/{name} (CCS generates in Debug/)")
            fixed += 1

    # 3. Remove ticlang/ directory (CCS uses Debug/)
    ticlang = proj / "ticlang"
    if ticlang.is_dir():
        import shutil
        shutil.rmtree(ticlang)
        print("[dir] removed ticlang/ (conflicts with CCS Debug/)")
        fixed += 1

    # 4. Verify final state
    remaining = []
    for d in proj.iterdir():
        if not d.is_dir() or d.name in ("Debug", "ticlang", "targetConfigs", ".settings", ".git"):
            continue
        for cf in d.glob("*.c"):
            remaining.append(str(cf.relative_to(proj)))
    if remaining:
        print(f"[FAIL] .c files still in subdirectories: {remaining}")
        return 1

    print(f"Cleanup complete: {fixed} issue(s) fixed, 0 remaining")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cleanup.py <project_dir>")
        print("Fixes: duplicate .c, generated files in root, ticlang/ conflicts")
        sys.exit(1)
    sys.exit(main(sys.argv[1]))
