# HAQS AI Marketing Toolkit

Personal AI-assisted marketing toolkit for generating campaign assets, URLs,
emails, landing copy, QR codes, project plans, testimonials, and ROI tracking
reports.

## How I Use This

I usually open this repository folder in Codex and use the Codex chat as the
main interface.

Recommended daily flow:

- Open Codex in this folder.
- Describe the campaign, event, client task, or assets I need.
- Choose whether I need a complete packet or selected assets.
- Let Codex run `haqs-create` and organize the generated files.
- Review the generated files:
  - Each creation run writes to one folder under `runs/`.
  - Each run includes `brief.json`, `outputs/`, `packet-index.md`, and
    `quality-check.md`.
- Move approved copy, URLs, QR codes, or plans into the final client or campaign
  workspace.

Useful Codex prompts:

- "Create selected assets for this event."
- "Create a complete campaign packet."
- "Turn this client feedback into testimonials."
- "Build UTM links for this campaign."
- "Generate landing page copy from this offer."
- "Show me the ROI report."

## Choosing A Workflow

Start with the short command map when you only need to know what to run:

```text
COMMANDS.md
```

When using Codex, describe the outcome first and let Codex choose the command.
The user-facing creation command is:

```powershell
haqs-create
```

Use `haqs-create` for the two normal marketing creation modes:

- Complete packet: generate the recommended assets from one event or campaign
  brief.
- Selected assets: choose only the assets needed for the same event or campaign.

Every creation run saves one folder:

```text
runs/<job-slug>-<job-type>-<scope>-YYYY-MM-DD-HHMM/
  brief.json
  outputs/
  packet-index.md
  quality-check.md
```

Examples:

```text
runs/spring-workshop-event-complete-2026-09-09-1332/
runs/spring-workshop-event-selected-2026-09-09-1345/
runs/fall-lead-magnet-campaign-complete-2026-09-09-1401/
```

Complete event packets generate event summary, tracked registration URL, QR
code, email sequence, social posts, landing page copy, packet index, and quality
check.

Complete campaign packets generate campaign summary, tracked campaign URL, QR
code, email drafts, social posts, landing page copy, project plan when a launch
date is available, packet index, and quality check.

Selected asset runs use the same brief but generate only the chosen outputs,
such as tracked URL plus QR code, or email sequence plus social posts.

Use non-interactive flags for repeatable creation:

```powershell
haqs-create --scope selected --job-type event --brief path/to/event-brief.json `
  --assets tracked_url,qr_code,social
```

Direct generator commands are still available for automation:

```powershell
python -m haqs_toolkit.generators.campaign_url_builder --landing-page-url https://example.com `
  --source linkedin --medium social --campaign-name fall_launch
```

Quality checks run automatically after creation. The checker scans generated
Markdown and text files for unresolved placeholders, sample URLs such as
`example.com`, missing CTA links, empty sections, and generation fallback notes.

## File Structure

```text
brand_voice.txt             Editable global voice for AI copy.
haqs_toolkit/               Packaged CLI, workflows, generators, and helpers.
haqs_toolkit/data/          Packaged data templates used by generators.
campaigns/                  Recommended home for reusable campaign packets.
runs/                       One folder per marketing creation run.
docs/                       Usage notes and script guidance.
tests/                      Unit tests for generators and shared helpers.
output/                     Ignored generated assets and ROI logs.
```

`campaigns/`, `runs/`, and `output/` may not exist in a fresh checkout. They
are created when needed.

## Brand Voice

The toolkit uses one editable brand voice file:

```text
brand_voice.txt
```

Before generating assets for a company, client, or event, edit that file with
the voice you want to use. Every AI copy script loads it automatically. The
individual scripts can still use local asset tone, such as email tone, social
channel style, or landing page tone.

## Setup

Install dependencies:

```powershell
pip install -r requirements.txt
```

Set your OpenAI API key for the current PowerShell session:

```powershell
$env:OPENAI_API_KEY="your-api-key-here"
```

Or copy `.env.example` to `.env` and use a dotenv loader of your choice.
The toolkit does not automatically load `.env`; Codex or the terminal session
must expose those variables before running AI-powered scripts.

By default, the AI scripts use `gpt-4.1-mini`. To use a different model for
the current PowerShell session:

```powershell
$env:OPENAI_MODEL="gpt-4.1"
```

The ROI tracker uses `$50/hour` by default. To override it for the current
PowerShell session:

```powershell
$env:HOURLY_RATE="75"
```

Marketing creation runs are saved under `runs/`. Direct generator files are
still saved in dated category folders under `output/`, for example
`output/2026-08-05/emails/` or `output/2026-08-05/qr_codes/`.

To save generated files somewhere else for the current PowerShell session:

```powershell
$env:HAQS_OUTPUT_DIR="custom-output"
```

## Commands

The primary interface is the installed console commands:

```powershell
pip install -e .
haqs-create
```

Use `haqs-create` to create a complete packet or selected assets in one run
folder. Use `haqs-toolkit` only when you want the older menu of individual
generators.

Create selected assets from an existing event brief:

```powershell
haqs-create --scope selected --job-type event --brief path/to/event-brief.json `
  --assets tracked_url,qr_code,social
```

Create a complete campaign packet from an existing campaign brief:

```powershell
haqs-create --scope complete --job-type campaign --brief campaigns/fall-workshop/brief.json
```

Each run automatically writes `packet-index.md` and `quality-check.md`.

Repurpose pasted source material into several marketing content formats:

```powershell
haqs-toolkit
```

Build a campaign URL with UTM parameters:

```powershell
haqs-toolkit
```

Generate three email options from pasted source content:

```powershell
haqs-toolkit
```

Generate a QR code PNG from a link:

```powershell
haqs-toolkit
```

Generate landing page copy from a guided mini-brief:

```powershell
haqs-toolkit
```

Build a marketing project plan CSV for spreadsheet editing or Asana import:

```powershell
haqs-toolkit
```

Turn raw customer feedback into short quotes, a case-study snippet, social
proof, a website testimonial, and marketing callouts:

```powershell
haqs-toolkit
```

The testimonial formatter asks whether the customer's identity may be shown.
Choose the anonymous option to omit their name and company from generated copy.

View automation ROI totals:

```powershell
haqs-toolkit
```

For multiline content prompts, paste the content and press Enter on a blank line when finished.

## ROI Tracking

Each completed generator run appends a row to `output/roi/automation_roi.csv`.

Default estimates:

- QR code: 5 minutes saved per code
- Campaign URL: 10 minutes saved per URL
- Email draft: 15 minutes saved per email
- LinkedIn, Facebook, and X posts: 15 minutes saved per post
- Email subject line, hook, or pull quote: 5 minutes saved per item
- Newsletter blurb: 15 minutes saved per blurb
- Landing page copy: 90 minutes saved per page
- Project plan: 45 minutes saved per plan
- Testimonial content: 10 minutes saved per item
