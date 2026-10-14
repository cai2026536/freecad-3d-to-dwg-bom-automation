#!/usr/bin/env python3
"""
FreeCAD headless pipeline for processing STEP files.

This script is intended to be executed via FreeCADCmd. It will:
- import a STEP file
- split multi-body solids into individual part features
- create a simple TechDraw page
- export DXF drawing (or SVG fallback)
- export BOM CSV and Excel

Usage:
    FreeCADCmd -c "import sys; sys.path.insert(0, 'scripts'); import freecad_step_pipeline; freecad_step_pipeline.process_step('input/model.step', 'output/model')"
"""

from __future__ import annotations

import csv
import os
import sys
from typing import List, Optional

import FreeCAD
import Import
import Part
import TechDraw


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def get_shape_solids(obj) -> List:
    shape = getattr(obj, "Shape", None)
    if shape is None:
        return []
    try:
        return list(shape.Solids)
    except Exception:
        return []


def split_multibody_objects(doc) -> List:
    """Split multi-solid objects into individual Part::Feature records."""
    created = []
    for obj in list(doc.Objects):
        if not hasattr(obj, "Shape"):
            continue
        solids = get_shape_solids(obj)
        if len(solids) <= 1:
            continue

        base_name = obj.Name
        for index, solid in enumerate(solids, start=1):
            feature = doc.addObject("Part::Feature", f"{base_name}_solid{index}")
            feature.Label = f"{obj.Label} - Solid {index}"
            feature.Shape = solid
            created.append(feature)

    return created


def create_techdraw_page(doc, parts, page_name: str = "AssemblySheet"):
    """Create a simple TechDraw sheet with one view per part."""
    page = doc.addObject("TechDraw::DrawPage", page_name)
    page.Label = "Assembly Drawing"

    candidates = []
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    candidates.append(os.path.join(project_root, "templates", "techdraw_template.svg"))
    candidates.append(
        os.path.join(
            FreeCAD.getResourceDir(),
            "Mod",
            "TechDraw",
            "Templates",
            "A4_Landscape_ISO7200.svg",
        )
    )

    template_path = None
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            template_path = candidate
            break

    if template_path:
        try:
            template = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
            template.Template = template_path
            page.Template = template
        except Exception:
            pass

    if getattr(page, "Template", None) is None:
        raise RuntimeError("Template not set for Page")

    row = 0
    col = 0
    for idx, part in enumerate(parts):
        view = doc.addObject("TechDraw::DrawViewPart", f"View_{idx + 1}")
        view.Source = [part]
        view.X = 20 + col * 120
        view.Y = 20 + row * 100
        page.addView(view)

        col += 1
        if col >= 3:
            col = 0
            row += 1

    doc.recompute()
    return page


def export_bom_csv(doc, output_csv: str):
    rows = []
    for obj in doc.Objects:
        if not hasattr(obj, "Shape"):
            continue
        if not obj.isDerivedFrom("Part::Feature"):
            continue

        shape = obj.Shape
        rows.append(
            {
                "PartName": getattr(obj, "Label", obj.Name),
                "ObjectName": obj.Name,
                "Type": obj.TypeId,
                "Volume_mm3": round(float(shape.Volume), 3) if hasattr(shape, "Volume") else "",
                "Area_mm2": round(float(shape.Area), 3) if hasattr(shape, "Area") else "",
            }
        )

    with open(output_csv, "w", newline="") as csvfile:
        fieldnames = ["PartName", "ObjectName", "Type", "Volume_mm3", "Area_mm2"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return output_csv


def export_excel_bom(csv_path: str, excel_path: str) -> str:
    """Optional Excel export using pandas/openpyxl."""
    try:
        import pandas as pd
    except Exception as exc:
        raise RuntimeError("pandas is required for Excel BOM export. Install requirements.txt") from exc

    df = pd.read_csv(csv_path)
    df.to_excel(excel_path, index=False)
    return excel_path


def export_techdraw_page(page, output_dir: str, base_name: str) -> Optional[str]:
    """Export a TechDraw page to DXF if possible, otherwise SVG; return the exported path."""
    dxf_path = os.path.join(output_dir, f"{base_name}.dxf")
    svg_path = os.path.join(output_dir, f"{base_name}.svg")

    # Preferred API
    if hasattr(TechDraw, "exportPageAsDXF"):
        try:
            TechDraw.exportPageAsDXF(page, dxf_path)
            return dxf_path
        except Exception:
            pass

    # Fallback: some FreeCAD builds expose exportPageAsSvg or exportPageAsSVG
    for name in ("exportPageAsSvg", "exportPageAsSVG", "exportPageAsSVG2"):
        if hasattr(TechDraw, name):
            try:
                getattr(TechDraw, name)(page, svg_path)
                return svg_path
            except Exception:
                pass

    # As a final attempt, try to use the DrawPage object's export (older/newer variants)
    try:
        if hasattr(page, "exportToDXF"):
            page.exportToDXF(dxf_path)
            return dxf_path
    except Exception:
        pass

    raise RuntimeError("This FreeCAD installation does not support TechDraw page DXF/SVG export")


def process_step(input_step: str, output_dir: str) -> dict:
    """Main processing function for a single STEP input file."""
    ensure_dir(output_dir)
    input_step = os.path.abspath(input_step)
    output_dir = os.path.abspath(output_dir)

    if not os.path.exists(input_step):
        raise FileNotFoundError(f"STEP input not found: {input_step}")

    base_name = os.path.splitext(os.path.basename(input_step))[0]
    doc = FreeCAD.newDocument(base_name)
    doc.Label = base_name

    Import.insert(input_step, doc.Name)
    doc.recompute()

    split_multibody_objects(doc)

    parts = [
        obj for obj in doc.Objects
        if hasattr(obj, "Shape") and obj.isDerivedFrom("Part::Feature")
    ]

    if not parts:
        raise RuntimeError(f"No Part::Feature objects found in imported STEP file: {input_step}")

    page = create_techdraw_page(doc, parts, page_name=f"{base_name}_Page")

    exported_path = export_techdraw_page(page, output_dir, base_name)

    fcstd_path = os.path.join(output_dir, f"{base_name}.FCStd")
    doc.saveAs(fcstd_path)

    bom_csv = os.path.join(output_dir, f"{base_name}_bom.csv")
    export_bom_csv(doc, bom_csv)

    bom_xlsx = os.path.join(output_dir, f"{base_name}_bom.xlsx")
    try:
        export_excel_bom(bom_csv, bom_xlsx)
    except Exception:
        bom_xlsx = None

    return {
        "document": fcstd_path,
        "drawing": exported_path,
        "bom_csv": bom_csv,
        "bom_xlsx": bom_xlsx,
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: FreeCADCmd -c \"import sys; sys.path.insert(0, 'scripts'); import freecad_step_pipeline; freecad_step_pipeline.process_step('input/part.step', 'output')\"")
        sys.exit(1)

    input_step = sys.argv[1]
    output_dir = sys.argv[2]
    result = process_step(input_step, output_dir)
    print(result)
