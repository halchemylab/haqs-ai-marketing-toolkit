# HAQS Command Map

Use this as the starting point when deciding what to run.

## Main Commands

| Need | Run |
| --- | --- |
| Choose from a menu of one-off tools | `haqs-toolkit` |
| Create a new campaign packet brief | `haqs-campaign --new campaigns/<campaign-slug>` |
| Generate a full campaign packet | `haqs-campaign campaigns/<campaign-slug>` |
| Generate an event packet | `haqs-event events/<event-slug>` |
| Check generated packet files before publishing | `haqs-check <packet-or-output-dir>` |

Install the commands first when needed:

```powershell
pip install -e .
```

## One-Off Tool Routing

For one-off work, run `haqs-toolkit` and choose from the menu.

| Need | Menu Tool |
| --- | --- |
| Add UTM tracking to a URL | Campaign URL Builder |
| Turn source material into social posts, hooks, quotes, and blurbs | Content Repurposer |
| Generate three email drafts | Email Generator |
| Generate landing page copy | Landing Page Copy Generator |
| Build a campaign project plan | Project Plan Builder |
| Generate a QR code PNG | QR Code Generator |
| Format raw customer feedback as testimonials | Testimonial Formatter |
| See estimated automation ROI | ROI Report |

## Direct Automation

Use direct module commands when you want repeatable runs with flags:

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
