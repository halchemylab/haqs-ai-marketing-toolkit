# HAQS AI Marketing Toolkit

Terminal Python scripts for generating marketing content and campaign URLs.

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

The ROI tracker uses `$50/hour` by default. To override it for the current
PowerShell session:

```powershell
$env:HOURLY_RATE="75"
```

The generated files are saved in the `output/` folder.

## Scripts

Repurpose pasted source material into several marketing content formats:

```powershell
python content_repurposer.py
```

Build a campaign URL with UTM parameters:

```powershell
python campaign_url_builder.py
```

Generate three email options from pasted source content:

```powershell
python email_generator.py
```

Generate a QR code PNG from a link:

```powershell
python qr_code_generator.py
```

Generate landing page copy from a guided mini-brief:

```powershell
python landing_page_copy_generator.py
```

Build a marketing project plan CSV for spreadsheet editing or Asana import:

```powershell
python project_plan_builder.py
```

View automation ROI totals:

```powershell
python roi_report.py
```

For multiline content prompts, paste the content and press Enter on a blank line when finished.

## ROI Tracking

Each completed generator run appends a row to `output/automation_roi.csv`.

Default estimates:

- QR code: 5 minutes saved per code
- Campaign URL: 10 minutes saved per URL
- Email draft: 15 minutes saved per email
- LinkedIn, Facebook, and X posts: 15 minutes saved per post
- Email subject line, hook, or pull quote: 5 minutes saved per item
- Newsletter blurb: 15 minutes saved per blurb
- Landing page copy: 90 minutes saved per page
- Project plan: 45 minutes saved per plan
