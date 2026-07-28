"""Generate organic social media posts for events."""

from __future__ import annotations

from haqs_cli import choose_option, generate_text, read_multiline, save_text, welcome


PLATFORMS = ["Facebook", "LinkedIn", "X"]


def build_prompt(event_details: str, platform: str) -> str:
    return f"""
Create one organic {platform} post for the event described below.

Requirements:
- Write in a clear, professional, audience-focused marketing voice.
- Make the event value obvious quickly.
- Include a natural call to action.
- Include the exact placeholder [url here] where the registration or landing page URL should go.
- Do not invent dates, speakers, prices, venues, or promises not present in the source text.
- Keep platform conventions in mind.
- Return only the finished post.

Event details:
{event_details}
""".strip()


def main() -> None:
    welcome("organic event social post generation")
    event_details = read_multiline("Enter or Paste the Content Here:")
    if not event_details:
        print("No content entered. Exiting.")
        return

    platform = choose_option("What would you like to generate?", PLATFORMS)
    print("\nGenerating post...\n")

    post = generate_text(
        system_prompt="You are a precise marketing copywriter for event promotion.",
        user_prompt=build_prompt(event_details, platform),
    )

    path = save_text(platform.lower(), post)
    print(post)
    print(f"\nSaved to: {path}")


if __name__ == "__main__":
    main()
