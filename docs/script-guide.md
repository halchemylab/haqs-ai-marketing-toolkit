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

For a short "which command should I run?" reference, start with `COMMANDS.md`.

Launch the interactive toolkit:

```powershell
haqs-toolkit
```

For local development, install the package in editable mode first:

```powershell
pip install -e .
```

Use the main CLI for one-off assets. Use `haqs-campaign` when a reusable brief
should produce a complete campaign packet. Use `haqs-event` when an event has a
structured `events/<event-slug>/brief.json` packet. Use `haqs-check` before
publishing generated packet files.

## Repository Layout

```text
brand_voice.txt             Global AI copy voice.
haqs_toolkit/               Packaged commands, workflows, generators, helpers.
haqs_toolkit/data/          Data templates loaded by packaged generators.
events/                     Event packet briefs, inputs, and outputs.
docs/                       Usage notes.
marketing_event_ai_builder.py
                            Root-level event marketing asset builder.
scripts/                    Legacy wrappers.
tests/                      Unit tests.
output/                     Ignored generated files and ROI logs.
```

## Individual Generators

Most generator modules are interactive and ask for input in the terminal.
Generated files are written under `output/<date>/<category>/` unless
`HAQS_OUTPUT_DIR` is set. Start with `haqs-toolkit` for individual tools.

Legacy `python <script>.py` wrappers live in `scripts/legacy/`. Keep them
working for older habits and automation, but prefer console commands and package
modules for new workflows.

| Legacy wrapper | Purpose | Requires `OPENAI_API_KEY` |
| --- | --- | --- |
| `scripts/legacy/content_repurposer.py` | Repurpose source content into social, email, hook, quote, and newsletter assets. | Yes |
| `scripts/legacy/email_generator.py` | Generate three email drafts from source content and a purpose. | Yes |
| `scripts/legacy/landing_page_copy_generator.py` | Generate landing page copy from a guided brief. | Yes |
| `scripts/legacy/testimonial_formatter.py` | Turn feedback into reusable social proof. | Yes |
| `scripts/legacy/campaign_url_builder.py` | Build UTM campaign URLs. | No |
| `scripts/legacy/project_plan_builder.py` | Build campaign project plan CSV and Markdown files. | No |
| `scripts/legacy/qr_code_generator.py` | Generate a QR code PNG from a URL. | No |
| `scripts/legacy/roi_report.py` | Summarize tracked automation ROI. | No |

Several operational tools also support non-interactive flags:

```powershell
python -m haqs_toolkit.generators.campaign_url_builder --landing-page-url https://example.com `
  --source linkedin --medium social --campaign-name fall_launch

python -m haqs_toolkit.generators.qr_code_generator --link https://example.com

python -m haqs_toolkit.generators.project_plan_builder --campaign-name "Fall Launch" `
  --campaign-type email_campaign --launch-date 2026-09-15 `
  --channels email,linkedin --team Sam=Copy

python -m haqs_toolkit.generators.roi_report --log-path output/roi/automation_roi.csv
```

Check generated packet files before publishing:

```powershell
haqs-check campaigns/fall-workshop
haqs-check events/demo-event/outputs
```

The checker scans generated Markdown and text files for unresolved placeholders,
sample URLs, missing CTA links, empty sections, and generation fallback notes.

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
python marketing_event_ai_builder.py events/demo-event
```

Or, after installing the package:

```powershell
haqs-event events/demo-event
```
