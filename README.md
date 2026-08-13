# HAQS AI Marketing Toolkit

Personal AI-assisted marketing toolkit for generating campaign assets, URLs,
emails, landing copy, QR codes, project plans, testimonials, and ROI tracking
reports.

## How I Use This

I usually open this repository folder in Codex and use the Codex chat as the
main interface.

Recommended daily flow:

- Open Codex in this folder.
- Describe the campaign, event, client task, or asset I need.
- Ask Codex which script or workflow fits the job.
- Let Codex run or update the scripts and organize the generated files.
- Review the generated files:
  - Campaign packets write to `<campaign_dir>/outputs/`.
  - Event packets write to `<event_dir>/outputs/`.
  - One-off tools write to dated folders under `output/`.
- Move approved copy, URLs, QR codes, or plans into the final client or campaign
  workspace.

Useful Codex prompts:

- "Run the event pipeline for `events/demo-event`."
- "Turn this client feedback into testimonials."
- "Build UTM links for this campaign."
- "Generate landing page copy from this offer."
- "Show me the ROI report."

## Choosing A Workflow

When using Codex, describe the outcome first and let Codex choose the command.
Use this routing as the default decision guide:

- Full reusable campaign brief -> `haqs-campaign`
- Structured event brief under `events/<event-slug>/brief.json` -> `haqs-event`
- One-off asset such as a URL, QR code, email, testimonial, or ROI report ->
  `haqs-toolkit`
- Repeatable automation with known inputs -> a direct `python <script>.py`
  command with flags

Use a campaign packet when one brief should produce a full campaign set:

```powershell
haqs-campaign --new campaigns/fall-workshop
haqs-campaign campaigns/fall-workshop
```

The `campaigns/` folder is only a recommended location. It is created when you
create your first campaign packet.

Use an event packet when the work starts from `events/<event-slug>/brief.json`
and needs predictable review files:

```powershell
haqs-event events/demo-event
```

Use the interactive toolkit when you only need one asset, such as a UTM link,
email draft, QR code, project plan, testimonial, or ROI report:

```powershell
haqs-toolkit
```

Use non-interactive flags for repeatable automation:

```powershell
python campaign_url_builder.py --landing-page-url https://example.com `
  --source linkedin --medium social --campaign-name fall_launch
```

## File Structure

```text
brand_voice.txt             Editable global voice for AI copy.
haqs_toolkit/               Packaged CLI, workflows, generators, and helpers.
haqs_toolkit/data/          Packaged data templates used by generators.
campaigns/                  Recommended home for reusable campaign packets.
events/                     Event packet briefs, inputs, and outputs.
docs/                       Usage notes and script guidance.
tests/                      Unit tests for generators and shared helpers.
output/                     Ignored generated assets and ROI logs.
```

`campaigns/` may not exist in a fresh checkout until the first campaign packet
is created.

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

One-off generator files are saved in dated category folders under `output/`, for
example `output/2026-08-05/emails/` or `output/2026-08-05/qr_codes/`. Campaign
and event packet workflows write to their packet `outputs/` folders by default.

To save generated files somewhere else for the current PowerShell session:

```powershell
$env:HAQS_OUTPUT_DIR="custom-output"
```

## Commands

The primary interface is the installed console commands:

```powershell
pip install -e .
haqs-toolkit
```

Use `haqs-toolkit` to launch the interactive menu for individual generators.
The root-level `python <script>.py` files remain as legacy compatibility
wrappers, but new workflows should prefer the packaged commands.

Generate a complete campaign packet from one brief:

```powershell
haqs-campaign --new campaigns/fall-workshop
haqs-campaign campaigns/fall-workshop
```

The campaign packet workflow creates a starter `brief.json`, optional source
notes, and review-ready outputs such as email drafts, social posts, landing page
copy, a campaign URL, QR code, project plan, and `packet-index.md`.

Generate a predictable event asset packet from `events/<event-slug>/brief.json`:

```powershell
python scripts/run_event_pipeline.py events/demo-event
```

If the package is installed, the same runner is available as:

```powershell
haqs-event events/demo-event
```

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
