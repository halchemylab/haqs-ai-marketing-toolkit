import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from project_plan_builder import (
    ASANA_FIELDNAMES,
    PROJECT_PLAN_FIELDNAMES,
    add_business_days,
    asana_rows,
    build_rows,
    parse_channels,
    parse_date,
    parse_team,
    write_csv,
)


class ProjectPlanBuilderTests(unittest.TestCase):
    def test_parse_date_accepts_iso_date(self):
        self.assertEqual(parse_date("2026-09-15"), date(2026, 9, 15))

    def test_parse_date_rejects_invalid_format(self):
        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
            parse_date("09/15/2026")

    def test_parse_channels_normalizes_aliases(self):
        channels = parse_channels("Email, LinkedIn Ads, facebook ads, paid social")

        self.assertEqual(
            channels,
            {"email", "linkedin_ads", "paid_social"},
        )

    def test_parse_team_maps_role_to_name(self):
        team = parse_team("Alex=Strategy, Sam=Copy, invalid")

        self.assertEqual(team, {"strategy": "Alex", "copy": "Sam"})

    def test_add_business_days_skips_weekends(self):
        friday = date(2026, 8, 7)

        self.assertEqual(add_business_days(friday, 1), date(2026, 8, 10))
        self.assertEqual(add_business_days(friday, -1), date(2026, 8, 6))

    def test_build_rows_filters_by_selected_channels_and_assigns_owner(self):
        rows = build_rows(
            campaign_name="Fall Launch",
            launch_date=date(2026, 9, 15),
            campaign_type="email_campaign",
            selected_channels={"email"},
            team={"copy": "Sam", "marketing ops": "Taylor"},
            buffer_days=2,
        )

        task_names = {row["Task Name"] for row in rows}
        self.assertIn("Draft email copy", task_names)
        self.assertIn("Send email", task_names)
        self.assertTrue(all(row["Campaign"] == "Fall Launch" for row in rows))
        self.assertEqual(
            next(row for row in rows if row["Task Name"] == "Draft email copy")[
                "Assignee"
            ],
            "Sam",
        )

    def test_write_csv_writes_headers_for_empty_project_plan(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "empty_plan.csv"

            write_csv(path, [], PROJECT_PLAN_FIELDNAMES)

            with open(path, encoding="utf-8") as file:
                self.assertEqual(
                    file.readline().strip(),
                    ",".join(PROJECT_PLAN_FIELDNAMES),
                )

    def test_asana_fieldnames_do_not_depend_on_export_rows(self):
        self.assertEqual(asana_rows([]), [])
        self.assertIn("Section/Column", ASANA_FIELDNAMES)


if __name__ == "__main__":
    unittest.main()
