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

The generated files are saved in the `output/` folder.

## Scripts

Generate an organic Facebook, LinkedIn, or X post for an event:

```powershell
python social_event_post.py
```

Build a campaign URL with UTM parameters:

```powershell
python campaign_url_builder.py
```

Generate three email options from pasted source content:

```powershell
python email_generator.py
```

For multiline content prompts, paste the content and press Enter on a blank line when finished.
