# Python Script Guide

This guide describes the Python entry points Codex can use in this repository.

## Setup

Install dependencies:

```powershell
pip install -r requirements.txt
```

Optional editable install:

```powershell
pip install -e .
```

## Main CLI

Launch the interactive toolkit:

```powershell
python main.py
```

After installing the package, the console command is also available:

```powershell
haqs-toolkit
```

## Individual Generators

Most existing generator scripts are interactive and ask for input in the terminal.
Generated files are written under `output/<date>/<category>/` unless
`HAQS_OUTPUT_DIR` is set.

| Script | Purpose | Requires `OPENAI_API_KEY` |
| --- | --- | --- |
| `content_repurposer.py` | Repurpose source content into social, email, hook, quote, and newsletter assets. | Yes |
| `email_generator.py` | Generate three email drafts from source content and a purpose. | Yes |
| `landing_page_copy_generator.py` | Generate landing page copy from a guided brief. | Yes |
| `testimonial_formatter.py` | Turn feedback into reusable social proof. | Yes |
| `campaign_url_builder.py` | Build UTM campaign URLs. | No |
| `project_plan_builder.py` | Build campaign project plan CSV and Markdown files. | No |
| `qr_code_generator.py` | Generate a QR code PNG from a URL. | No |
| `roi_report.py` | Summarize tracked automation ROI. | No |

## Expected Outputs

AI copy generators save text or Markdown files. Operational tools save CSV, PNG,
or text files. Every completed generator logs estimated time savings to
`output/roi/automation_roi.csv`.

## Event Workflow

For repeatable event work, use an event packet:

```text
events/<event-slug>/
  brief.json
  inputs/
  outputs/
```

The event runner reads `brief.json`, validates required fields, and writes a
predictable set of review-ready marketing files to `outputs/`.

Run it directly:

```powershell
python scripts/run_event_pipeline.py events/demo-event
```

Or, after installing the package:

```powershell
haqs-event events/demo-event
```
