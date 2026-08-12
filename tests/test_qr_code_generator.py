import unittest

from qr_code_generator import build_parser, create_qr_code


class QrCodeGeneratorTests(unittest.TestCase):
    def test_rejects_url_without_http_scheme(self):
        with self.assertRaisesRegex(ValueError, "http:// or https://"):
            create_qr_code("example.com/page")

    def test_accepts_https_url(self):
        image = create_qr_code("https://example.com/page")

        self.assertTrue(hasattr(image, "save"))

    def test_parser_accepts_non_interactive_link(self):
        args = build_parser().parse_args(["--link", "https://example.com/page"])

        self.assertEqual(args.link, "https://example.com/page")


if __name__ == "__main__":
    unittest.main()
