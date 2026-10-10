#!/usr/bin/env python3
"""Optional helper for DXF -> DWG conversion.

This is not required for the core workflow, because native DWG export is limited in FreeCAD open-source usage.
Use this when an external DXF-to-DWG converter is installed.

Example:
    python scripts/dxf_to_dwg_optional.py --input ./output/model.dxf --output ./output/model.dwg --converter "C:/path/to/ODAFileConverter.exe"
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys


def convert_dxf_to_dwg(input_dxf: str, output_dwg: str, converter_exe: str):
    if not os.path.exists(converter_exe):
        raise FileNotFoundError(f"Converter executable not found: {converter_exe}")

    cmd = [converter_exe, input_dxf, output_dwg]
    print(f"Running: {' '.join(cmd)}")
    completed = subprocess.run(cmd, capture_output=True, text=True)
    if completed.returncode != 0:
        print(completed.stdout)
        print(completed.stderr)
        raise RuntimeError(f"DXF to DWG conversion failed for {input_dxf}")

    return output_dwg


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert DXF files to DWG using an external converter.")
    parser.add_argument("--input", required=True, help="Input DXF path")
    parser.add_argument("--output", required=True, help="Output DWG path")
    parser.add_argument("--converter", required=True, help="Path to the converter executable")
    args = parser.parse_args()

    try:
        result = convert_dxf_to_dwg(args.input, args.output, args.converter)
        print(f"Converted: {result}")
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
