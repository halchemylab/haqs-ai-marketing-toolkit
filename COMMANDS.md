# HAQS Command Map

Use this as the starting point when deciding what to run.

## Main Commands

| Need | Run |
| --- | --- |
| Create a complete packet or selected assets | `haqs-create` |
| Create selected event assets from an existing brief | `haqs-create --scope selected --job-type event --brief events/<event-slug>/brief.json --assets tracked_url,qr_code,social` |
| Create a complete campaign packet from an existing brief | `haqs-create --scope complete --job-type campaign --brief campaigns/<campaign-slug>/brief.json` |
| Open the older individual-generator menu | `haqs-toolkit` |

Install the commands first when needed:

```powershell
pip install -e .
```

## Creation Model

Use `haqs-create` first. It asks:

```text
What are you creating?
1. Complete packet
2. Selected assets

What is this for?
1. Event
2. Campaign / offer
```

Each creation run saves one folder:

```text
runs/<job-slug>-<job-type>-<scope>-YYYY-MM-DD-HHMM/
  brief.json
  outputs/
  packet-index.md
  quality-check.md
```

Quality checks run automatically after assets are generated.

## Selected Assets

For selected asset work, choose one or more assets from the same brief.

| Asset | Key |
| --- | --- |
| Tracked URL | `tracked_url` |
| QR code | `qr_code` |
| Email sequence/drafts | `email` |
| Social posts | `social` |
| Landing page copy | `landing_page` |
| Campaign project plan | `project_plan` |

## Direct Automation

Use direct module commands when you only need a specific low-level generator:

```powershell
python -m haqs_toolkit.generators.campaign_url_builder --landing-page-url https://example.com `
  --source linkedin --medium social --campaign-name fall_launch

python -m haqs_toolkit.generators.qr_code_generator --link https://example.com

python -m haqs_toolkit.generators.project_plan_builder --campaign-name "Fall Launch" `
  --campaign-type email_campaign --launch-date 2026-09-15 `
  --channels email,linkedin --team Sam=Copy

python -m haqs_toolkit.generators.roi_report --log-path output/roi/automation_roi.csv
```

## Legacy Wrappers

Most old root-level wrappers live in `scripts/legacy/` and are kept only for
older habits and automation. The event marketing asset builder is available at
the repo root as `marketing_event_ai_builder.py`; prefer the commands above for
new work.
