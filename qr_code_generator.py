"""Generate a QR code image from a link."""

from __future__ import annotations

import qrcode

from haqs_cli import read_required, timestamped_output_path, welcome


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

    print("\nQR code saved to:")
    print(path)


if __name__ == "__main__":
    main()
