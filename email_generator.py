"""Generate three email variants from pasted source content."""

from __future__ import annotations

from haqs_cli import generate_text, read_multiline, read_required, save_text, welcome


def build_prompt(source_content: str, purpose: str) -> str:
    return f"""
Create three different email drafts based on the source content below.

Purpose of the email:
{purpose}

Requirements:
- Each email must include a subject line and body.
- Make each version meaningfully different in angle and wording.
- Use a clear, professional marketing voice.
- Include the exact placeholder [url here] anywhere a link should be inserted.
- Do not invent dates, speakers, prices, venues, or promises not present in the source text.
- Separate the three emails with exactly this divider on its own line:
=====
- Return only the three email drafts.

Source content:
{source_content}
""".strip()


def main() -> None:
    welcome("email generation")
    source_content = read_multiline("Enter or Paste the Content Here:")
    if not source_content:
        print("No content entered. Exiting.")
        return

    purpose = read_required("What is the purpose of the email? ")
    print("\nGenerating emails...\n")

    emails = generate_text(
        system_prompt="You are a precise marketing email copywriter.",
        user_prompt=build_prompt(source_content, purpose),
    )

    path = save_text("email", emails)
    print(emails)
    print(f"\nSaved to: {path}")


if __name__ == "__main__":
    main()
