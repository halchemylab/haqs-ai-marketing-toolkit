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

For multiline content prompts, paste the content and press Enter on a blank line when finished.
