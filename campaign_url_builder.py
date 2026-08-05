"""Build campaign tracking URLs with UTM parameters."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from utils.marketing import (
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

    return urlunparse(
        parsed._replace(query=urlencode(existing_query, doseq=True))
    )


def main() -> None:
    welcome("campaign URL building")
    landing_page_url = read_url("Paste your full Landing Page URL, including https://: ")
    source = read_required(
        "Enter campaign source, e.g. google, medium, substack, linkedin, facebook: "
    )
    medium = read_required("Enter medium, e.g. cpc, banner, email, qr_code: ")
    campaign_name = read_required("Enter campaign_name: ")
    campaign_content = read_optional(
        "Enter campaign content to differentiate ads (optional): "
    )

    campaign_url = add_utm_parameters(
        landing_page_url=landing_page_url,
        source=source,
        medium=medium,
        campaign_name=campaign_name,
        campaign_content=campaign_content,
    )

    path = save_text("campaign_url", campaign_url)
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


if __name__ == "__main__":
    main()
