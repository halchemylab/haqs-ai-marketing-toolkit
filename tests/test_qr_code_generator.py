import unittest

from qr_code_generator import create_qr_code


class QrCodeGeneratorTests(unittest.TestCase):
    def test_rejects_url_without_http_scheme(self):
        with self.assertRaisesRegex(ValueError, "http:// or https://"):
            create_qr_code("example.com/page")

    def test_accepts_https_url(self):
        image = create_qr_code("https://example.com/page")

        self.assertTrue(hasattr(image, "save"))


if __name__ == "__main__":
    unittest.main()
