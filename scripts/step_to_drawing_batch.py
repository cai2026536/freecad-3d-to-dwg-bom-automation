#!/usr/bin/env python3
"""Batch runner for STEP files using FreeCADCmd.

Example:
    python scripts/step_to_drawing_batch.py --input-dir ./input --output-dir ./output
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def find_freecad_cmd() -> str:
    candidates = [
        os.environ.get("FREECAD_CMD"),
        "FreeCADCmd",
        "freecadcmd",
        "/usr/bin/FreeCADCmd",
        "/usr/local/bin/FreeCADCmd",
        "C:/Program Files/FreeCAD 0.21/bin/FreeCADCmd.exe",
    ]

    for candidate in candidates:
        if not candidate:
            continue
        if shutil.which(candidate):
            return candidate
        if os.path.exists(candidate):
            return candidate
    raise RuntimeError(
        "FreeCADCmd not found. Please install FreeCAD and ensure it is in PATH or set FREECAD_CMD."
    )


def discover_step_files(input_dir: str):
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    files = sorted(input_path.rglob("*.step")) + sorted(input_path.rglob("*.STEP"))
    files += sorted(input_path.rglob("*.stp")) + sorted(input_path.rglob("*.STP"))
    unique = []
    seen = set()
    for file in files:
        norm = str(file.resolve())
        if norm not in seen:
            seen.add(norm)
            unique.append(file)
    return unique


def run_freecad_for_file(freecad_cmd: str, step_file: str, output_dir: str):
    script_path = Path(__file__).resolve().parent / "freecad_step_pipeline.py"
    script_dir = str(script_path.parent)

    cmd = [
        freecad_cmd,
        "-c",
        (
            "import sys; "
            f"sys.path.insert(0, r'{script_dir}'); "
            "import freecad_step_pipeline; "
            f"freecad_step_pipeline.process_step(r'{step_file}', r'{output_dir}')"
        ),
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError(f"FreeCAD failed for {step_file}")

    return result.stdout


def main():
    parser = argparse.ArgumentParser(description="Batch process STEP files to DXF + BOM using FreeCAD headless mode.")
    parser.add_argument("--input-dir", required=True, help="Folder containing STEP files")
    parser.add_argument("--output-dir", required=True, help="Folder for generated files")
    args = parser.parse_args()

    freecad_cmd = find_freecad_cmd()
    step_files = discover_step_files(args.input_dir)

    if not step_files:
        raise FileNotFoundError(f"No STEP/STP files were found in: {args.input_dir}")

    os.makedirs(args.output_dir, exist_ok=True)

    for step_file in step_files:
        out_dir = os.path.join(args.output_dir, step_file.stem)
        os.makedirs(out_dir, exist_ok=True)
        print(f"Processing {step_file} -> {out_dir}")
        result_log = run_freecad_for_file(freecad_cmd, str(step_file), out_dir)
        print(result_log)

    print(f"Completed processing {len(step_files)} file(s).")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
