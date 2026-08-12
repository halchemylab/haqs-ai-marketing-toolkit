"""Generate a QR code image from a link."""

from __future__ import annotations

import argparse

import qrcode

from haqs_toolkit.utils.marketing import (
    log_roi_event,
    print_roi_logged,
    read_url,
    timestamped_output_path,
    validate_url,
    welcome,
)


def create_qr_code(link: str):
    link = validate_url(link)
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=12,
        border=4,
    )
    qr.add_data(link)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")


def save_qr_code(link: str):
    image = create_qr_code(link)
    path = timestamped_output_path("qr_code", "png")
    image.save(path)
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a QR code PNG.")
    parser.add_argument("--link", help="Full http:// or https:// URL to encode.")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    welcome("QR code generation")
    link = args.link or read_url("Paste your full link, including https://: ")

    path = save_qr_code(link)
    minutes_saved = 5
    roi = log_roi_event(
        script="qr_code_generator",
        asset_type="qr_code",
        count=1,
        minutes_per_item=minutes_saved,
        notes="Generated QR code image",
    )

    print("\nQR code saved to:")
    print(path)
    print_roi_logged(roi)
    print(
        "\nNext step: Test the QR code with a phone camera before using it in "
        "print, signage, or campaign assets."
    )


if __name__ == "__main__":
    main()
