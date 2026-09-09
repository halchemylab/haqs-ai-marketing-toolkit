# Python Script Guide

This guide describes the current Python entry points Codex can use in this
repository.

## Setup

Install dependencies:

```powershell
pip install -r requirements.txt
```

Optional editable install:

```powershell
pip install -e .
```

## Main Creation Flow

Use `haqs-create` for normal marketing asset creation.

```powershell
haqs-create
```

It supports two scopes:

- Complete packet: generate the recommended asset set.
- Selected assets: generate only the assets needed from the same brief.

It supports two job types:

- Event
- Campaign / offer

Each run creates one folder:

```text
runs/<job-slug>-<job-type>-<scope>-YYYY-MM-DD-HHMM>/
  brief.json
  outputs/
  packet-index.md
  quality-check.md
```

Quality checks run automatically after assets are generated.

## Non-Interactive Examples

Create selected event assets from an existing brief:

```powershell
haqs-create --scope selected --job-type event --brief path/to/event-brief.json `
  --assets tracked_url,qr_code,social
```

Create a complete campaign packet from an existing brief:

```powershell
haqs-create --scope complete --job-type campaign --brief path/to/campaign-brief.json
```

Selected asset keys:

```text
tracked_url
qr_code
email
social
landing_page
project_plan
```

`project_plan` is available for campaign runs.

## Lower-Level Generators

The packaged generator modules are still available for focused automation.
They write to `output/<date>/<category>/` unless `HAQS_OUTPUT_DIR` is set.

```powershell
python -m haqs_toolkit.generators.campaign_url_builder --landing-page-url https://example.com `
  --source linkedin --medium social --campaign-name fall_launch

python -m haqs_toolkit.generators.qr_code_generator --link https://example.com

python -m haqs_toolkit.generators.project_plan_builder --campaign-name "Fall Launch" `
  --campaign-type email_campaign --launch-date 2026-09-15 `
  --channels email,linkedin --team Sam=Copy

python -m haqs_toolkit.generators.roi_report --log-path output/roi/automation_roi.csv
```

## Expected Outputs

`haqs-create` outputs one self-contained run folder. Lower-level generators save
individual files under `output/`. Every completed generator logs estimated time
savings to `output/roi/automation_roi.csv`.
