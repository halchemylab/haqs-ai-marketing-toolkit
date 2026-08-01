import unittest

from campaign_url_builder import add_utm_parameters


class CampaignUrlBuilderTests(unittest.TestCase):
    def test_adds_required_utm_parameters(self):
        url = add_utm_parameters(
            landing_page_url="https://example.com/page",
            source="linkedin",
            medium="social",
            campaign_name="summer_launch",
            campaign_content="hero_ad",
        )

        self.assertEqual(
            url,
            "https://example.com/page?utm_source=linkedin&utm_medium=social"
            "&utm_campaign=summer_launch&utm_content=hero_ad",
        )

    def test_preserves_existing_query_parameters(self):
        url = add_utm_parameters(
            landing_page_url="https://example.com/page?ref=partner",
            source="email",
            medium="newsletter",
            campaign_name="august_update",
            campaign_content="",
        )

        self.assertEqual(
            url,
            "https://example.com/page?ref=partner&utm_source=email"
            "&utm_medium=newsletter&utm_campaign=august_update",
        )

    def test_overwrites_existing_utm_parameters(self):
        url = add_utm_parameters(
            landing_page_url=(
                "https://example.com/page?utm_source=old&utm_medium=old"
                "&utm_campaign=old&utm_content=old"
            ),
            source="google",
            medium="cpc",
            campaign_name="new_campaign",
            campaign_content="search_ad",
        )

        self.assertEqual(
            url,
            "https://example.com/page?utm_source=google&utm_medium=cpc"
            "&utm_campaign=new_campaign&utm_content=search_ad",
        )


if __name__ == "__main__":
    unittest.main()
