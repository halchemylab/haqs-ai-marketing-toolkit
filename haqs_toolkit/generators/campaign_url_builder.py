"""Build campaign tracking URLs with UTM parameters."""

from __future__ import annotations

import argparse
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from haqs_toolkit.utils.marketing import (
    log_roi_event,
    print_roi_logged,
    read_optional,
    read_required,
    read_url,
    save_text,
    validate_url,
    welcome,
)


def add_utm_parameters(
    landing_page_url: str,
    source: str,
    medium: str,
    campaign_name: str,
    campaign_content: str,
) -> str:
    landing_page_url = validate_url(landing_page_url)
    parsed = urlparse(landing_page_url)
    existing_query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    existing_query["utm_source"] = source
    existing_query["utm_medium"] = medium
    existing_query["utm_campaign"] = campaign_name
    if campaign_content:
        existing_query["utm_content"] = campaign_content

    return urlunparse(parsed._replace(query=urlencode(existing_query, doseq=True)))


def save_campaign_url(
    landing_page_url: str,
    source: str,
    medium: str,
    campaign_name: str,
    campaign_content: str = "",
) -> tuple[str, object]:
    campaign_url = add_utm_parameters(
        landing_page_url=landing_page_url,
        source=source,
        medium=medium,
        campaign_name=campaign_name,
        campaign_content=campaign_content,
    )
    return campaign_url, save_text("campaign_url", campaign_url)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a tracked campaign URL.")
    parser.add_argument("--landing-page-url", help="Full http:// or https:// URL.")
    parser.add_argument("--source", help="UTM source, such as linkedin or google.")
    parser.add_argument("--medium", help="UTM medium, such as email or cpc.")
    parser.add_argument("--campaign-name", help="UTM campaign value.")
    parser.add_argument("--campaign-content", default="", help="Optional UTM content.")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    welcome("campaign URL building")
    has_cli_input = any(
        [args.landing_page_url, args.source, args.medium, args.campaign_name]
    )
    if has_cli_input:
        missing = [
            name
            for name, value in {
                "--landing-page-url": args.landing_page_url,
                "--source": args.source,
                "--medium": args.medium,
                "--campaign-name": args.campaign_name,
            }.items()
            if not value
        ]
        if missing:
            parser.error(f"missing required arguments: {', '.join(missing)}")
        landing_page_url = args.landing_page_url
        source = args.source
        medium = args.medium
        campaign_name = args.campaign_name
        campaign_content = args.campaign_content
    else:
        landing_page_url = read_url(
            "Paste your full Landing Page URL, including https://: "
        )
        source = read_required(
            "Enter campaign source, e.g. google, medium, substack, linkedin, facebook: "
        )
        medium = read_required("Enter medium, e.g. cpc, banner, email, qr_code: ")
        campaign_name = read_required("Enter campaign_name: ")
        campaign_content = read_optional(
            "Enter campaign content to differentiate ads (optional): "
        )

    campaign_url, path = save_campaign_url(
        landing_page_url=landing_page_url,
        source=source,
        medium=medium,
        campaign_name=campaign_name,
        campaign_content=campaign_content,
    )
    minutes_saved = 10
    roi = log_roi_event(
        script="campaign_url_builder",
        asset_type=f"campaign_url_{source.lower()}",
        count=1,
        minutes_per_item=minutes_saved,
        notes=f"Generated campaign URL for {source}",
    )

    print("\nCampaign URL:")
    print(campaign_url)
    print(f"\nSaved to: {path}")
    print_roi_logged(roi)
    print("\nNext step: Use this link in your ad, email, QR code, or social post.")


if __name__ == "__main__":
    main()
