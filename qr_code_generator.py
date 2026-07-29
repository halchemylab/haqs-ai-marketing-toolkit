"""Generate a QR code image from a link."""

from __future__ import annotations

import qrcode

from utils.marketing import (
    get_hourly_rate,
    log_roi_event,
    print_roi_logged,
    read_required,
    timestamped_output_path,
    welcome,
)


def create_qr_code(link: str):
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=12,
        border=4,
    )
    qr.add_data(link)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")


def main() -> None:
    welcome("QR code generation")
    link = read_required("Paste your link: ")

    image = create_qr_code(link)
    path = timestamped_output_path("qr_code", "png")
    image.save(path)
    minutes_saved = 5
    money_saved = (minutes_saved / 60) * get_hourly_rate()
    log_roi_event(
        script="qr_code_generator",
        asset_type="qr_code",
        count=1,
        minutes_per_item=minutes_saved,
        notes="Generated QR code image",
    )

    print("\nQR code saved to:")
    print(path)
    print_roi_logged(1, minutes_saved, money_saved)


if __name__ == "__main__":
    main()
