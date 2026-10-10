# FreeCAD STEP to DWG/BOM Automation

This repository contains an open-source automation workflow for processing STEP files with FreeCAD and generating:

- split multi-body / multi-part solids
- part drawings and assembly drawings
- 2D dimensioned views
- DXF exports and optional DWG conversion
- BOM export in CSV and Excel

The project is intended to be used as a practical starting point for headless CAD automation.

## Project goals

- Import STEP/STP files in batch
- Split multi-body solids into individual part features
- Create simple TechDraw sheets for each model or assembly
- Export 2D drawings to DXF
- Optionally convert DXF to DWG using external software
- Generate BOM data as CSV and Excel

## Typical workflow

STEP file -> FreeCAD import -> split bodies -> create TechDraw pages -> export DXF -> convert to DWG (optional) -> BOM CSV/XLSX

## Repository layout

- `scripts/freecad_step_pipeline.py` : FreeCAD script that imports STEP files and creates drawings/BOM
- `scripts/step_to_drawing_batch.py` : batch runner for folders of STEP files
- `scripts/dxf_to_dwg_optional.py` : optional DXF -> DWG conversion helper
- `requirements.txt` : Python dependencies
- `README.md` : usage instructions

## Requirements

- FreeCAD installed with `FreeCADCmd` on PATH
- Python 3.10+
- Optional: ODA File Converter or another DXF-to-DWG converter for DWG export

## Quick start

1. Install FreeCAD and confirm `FreeCADCmd` is available.
2. Clone this repository.
3. Put STEP files in a folder like `input/`.
4. Run:

```bash
python scripts/step_to_drawing_batch.py --input-dir ./input --output-dir ./output
```

This will scan all `.step`, `.stp`, `.STEP`, `.STP` files in the input folder and process them one by one.

## Generated outputs

For each STEP file, the batch runner creates a subfolder under the output directory with files such as:

- `model.FCStd`
- `model.dxf`
- `model_bom.csv`
- `model_bom.xlsx`
- optional `model.dwg` if DXF-to-DWG conversion is configured

## DWG note

FreeCAD does not provide a native DWG writer in the standard open-source workflow. The usual practical path is:

- export DXF from FreeCAD
- convert DXF to DWG using external tools such as ODA File Converter or LibreDWG-compatible tooling

This repository includes `scripts/dxf_to_dwg_optional.py` for that workflow.

## FreeCAD headless mode

The pipeline is intentionally designed for `FreeCADCmd` headless automation and batch operation.

Example direct run:

```bash
FreeCADCmd -c "import sys; sys.path.insert(0, 'scripts'); import freecad_step_pipeline; freecad_step_pipeline.process_step('input/model.step', 'output/model')"
```

## Caveats

- Exact TechDraw behavior can vary slightly by FreeCAD version.
- Automatic dimension placement and drawing layout are simplified and meant as a practical baseline workflow.
- For production drawing standards, you may need to tune view placement, templates, and dimensioning style.

## License

MIT
