# Client profiles

Edit `default.txt` directly, or copy it to a new client filename and customize it.
Only `.txt` files appear in the picker. Blank fields are requested during brief
intake when needed. The starter profile contains:

```text
Client: Default
Voice: Clear, practical, professional, and direct.
Audience:
Products/services:
Preferred CTA:
Website:
Channels:
Avoid: Hype, jargon, exaggerated promises, unsupported claims, fake urgency, and excessive emojis.

Use the audience, offer, CTA, and channels supplied in the campaign brief.
Use short paragraphs, make the next step obvious, and stay grounded in the supplied material.
```

Use any additional plain-text instructions you need. Audience, Preferred CTA
(or CTA), and Channels fill missing brief fields. All other text guides AI copy.
Website is background only: supply the actual campaign destination during intake.
Explicit brief values override client defaults; use the brief preview to edit them.

`haqs-create` offers a numbered picker when profiles exist. Choose General brand
voice to use `brand_voice.txt`. For saved briefs, pass `--brands default` or
`--brands default.txt`; `--brands general` removes a saved profile. Without that flag,
saved briefs reuse their embedded profile without prompting.

Each client run saves the profile in `brief.json` and `client-profile.txt`.
Changing the client file later does not change past runs. Pass `--brands default`
again to use its latest contents. Event copy uses AI when a client is selected;
if AI is unavailable, the normal template fallback is flagged for review.
