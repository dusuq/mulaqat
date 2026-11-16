import csv
import os
import sys
import tempfile
import unittest
from datetime import date

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "skills", "mulaqat", "scripts")
)

import tracker

TODAY = date(2026, 11, 16)


class TrackerLogicTest(unittest.TestCase):
    def setUp(self):
        self.leads = []

    def add(self, name, **kw):
        return tracker.add_lead(self.leads, TODAY, name=name, **kw)

    def test_add_assigns_incrementing_ids_and_found_stage(self):
        a = self.add("Sara", company="Acme")
        b = self.add("Ali")
        self.assertEqual((a["id"], b["id"]), ("1", "2"))
        self.assertEqual(a["stage"], "found")
        self.assertEqual(a["created"], "2026-11-16")

    def test_add_requires_name(self):
        with self.assertRaises(tracker.TrackerError):
            tracker.add_lead(self.leads, TODAY, name="  ")

    def test_formula_injection_is_neutralised(self):
        lead = self.add('=HYPERLINK("x")', company="+cmd")
        self.assertTrue(lead["name"].startswith("'="))
        self.assertTrue(lead["company"].startswith("'+"))

    def test_requested_sets_date_once(self):
        self.add("Sara")
        tracker.update_lead(self.leads, "1", TODAY, stage="requested")
        later = date(2026, 11, 18)
        tracker.update_lead(self.leads, "1", later, stage="requested")
        self.assertEqual(self.leads[0]["requested_on"], "2026-11-16")

    def test_reached_keeps_highest_stage_after_lost(self):
        self.add("Sara")
        tracker.update_lead(self.leads, "1", TODAY, stage="replied")
        tracker.update_lead(
            self.leads, "1", TODAY, stage="lost", next_action="2026-12-01"
        )
        lead = self.leads[0]
        self.assertEqual(lead["stage"], "lost")
        self.assertEqual(lead["reached"], "replied")
        self.assertEqual(lead["next_action"], "")

    def test_unknown_stage_and_id_raise(self):
        self.add("Sara")
        with self.assertRaises(tracker.TrackerError):
            tracker.update_lead(self.leads, "1", TODAY, stage="maybe")
        with self.assertRaises(tracker.TrackerError):
            tracker.update_lead(self.leads, "99", TODAY, stage="found")

    def test_notes_are_appended_with_dates(self):
        self.add("Sara")
        tracker.update_lead(self.leads, "1", TODAY, note="sent note")
        tracker.update_lead(self.leads, "1", date(2026, 11, 17), note="accepted")
        self.assertEqual(
            self.leads[0]["notes"], "2026-11-16: sent note | 2026-11-17: accepted"
        )

    def test_bad_next_date_raises(self):
        self.add("Sara")
        with self.assertRaises(tracker.TrackerError):
            tracker.update_lead(self.leads, "1", TODAY, next_action="next week")

    def test_due_excludes_future_terminal_and_undated(self):
        for name in ("A", "B", "C", "D"):
            self.add(name)
        tracker.update_lead(self.leads, "1", TODAY, next_action="2026-11-15")
        tracker.update_lead(self.leads, "2", TODAY, next_action="2026-11-20")
        tracker.update_lead(self.leads, "3", TODAY, next_action="2026-11-16")
        tracker.update_lead(self.leads, "3", TODAY, stage="won")
        ids = [l["id"] for l in tracker.due(self.leads, TODAY)]
        self.assertEqual(ids, ["1"])

    def test_limits_count_rolling_seven_days(self):
        for i, day in enumerate([16, 15, 10, 9]):
            self.add(f"L{i}")
            tracker.update_lead(
                self.leads, str(i + 1), date(2026, 11, day), stage="requested"
            )
        result = tracker.limits(self.leads, TODAY)
        # 16, 15, 10 are inside 10..16; the 9th is outside
        self.assertEqual(result["sent_last_7_days"], 3)
        self.assertEqual(result["sent_today"], 1)
        self.assertEqual(result["remaining_this_week"], 77)
        self.assertEqual(result["remaining_today"], 19)

    def test_small_account_cap_and_floor_at_zero(self):
        for i in range(35):
            self.add(f"L{i}")
            tracker.update_lead(self.leads, str(i + 1), TODAY, stage="requested")
        result = tracker.limits(self.leads, TODAY, small_account=True)
        self.assertEqual(result["weekly_cap"], 30)
        self.assertEqual(result["remaining_this_week"], 0)
        self.assertEqual(result["remaining_today"], 0)

    def test_stale_lists_old_pending_requests_only(self):
        self.add("Old")
        self.add("New")
        self.add("OldButConnected")
        tracker.update_lead(self.leads, "1", date(2026, 10, 20), stage="requested")
        tracker.update_lead(self.leads, "2", date(2026, 11, 10), stage="requested")
        tracker.update_lead(self.leads, "3", date(2026, 10, 20), stage="requested")
        tracker.update_lead(self.leads, "3", date(2026, 10, 25), stage="connected")
        self.assertEqual([l["name"] for l in tracker.stale(self.leads, TODAY)], ["Old"])

    def test_report_rates(self):
        stages = ["requested", "connected", "messaged", "replied", "booked"]
        for i, stage in enumerate(stages):
            self.add(f"L{i}")
            tracker.update_lead(self.leads, str(i + 1), TODAY, stage="requested")
            tracker.update_lead(self.leads, str(i + 1), TODAY, stage=stage)
        r = tracker.report(self.leads, TODAY)
        self.assertEqual(r["requested"], 5)
        self.assertEqual(r["connected"], 4)
        self.assertEqual(r["acceptance_rate_pct"], 80.0)
        self.assertEqual(r["messaged"], 3)
        self.assertEqual(r["replied"], 2)
        self.assertEqual(r["reply_rate_pct"], 66.7)
        self.assertEqual(r["booked"], 1)

    def test_report_with_no_data_has_no_rates(self):
        r = tracker.report(self.leads, TODAY)
        self.assertIsNone(r["acceptance_rate_pct"])
        self.assertIsNone(r["reply_rate_pct"])


class TrackerCliTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "pipeline.csv")

    def tearDown(self):
        self.dir.cleanup()

    def run_cli(self, *args):
        return tracker.main(["--file", self.path, "--today", "2026-11-16", *args])

    def test_round_trip_through_csv(self):
        self.assertEqual(
            self.run_cli(
                "add",
                "--name",
                "Sara Khan",
                "--company",
                "Acme",
                "--service",
                "WhatsApp",
            ),
            0,
        )
        self.assertEqual(
            self.run_cli(
                "update", "--id", "1", "--stage", "requested", "--next", "2026-11-19"
            ),
            0,
        )
        with open(self.path, newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["stage"], "requested")
        self.assertEqual(rows[0]["requested_on"], "2026-11-16")
        self.assertEqual(rows[0]["next_action"], "2026-11-19")
        self.assertEqual(list(rows[0].keys()), tracker.COLUMNS)

    def test_errors_return_nonzero_and_leave_file_untouched(self):
        self.run_cli("add", "--name", "Sara")
        before = self.read_file()
        self.assertEqual(self.run_cli("update", "--id", "7", "--stage", "connected"), 1)
        self.assertEqual(self.read_file(), before)

    def read_file(self):
        with open(self.path, encoding="utf-8") as handle:
            return handle.read()

    def test_read_commands_work_on_missing_file(self):
        for cmd in (["queue"], ["limits"], ["stale"], ["report"], ["list"]):
            self.assertEqual(self.run_cli(*cmd), 0)
        self.assertFalse(os.path.exists(self.path))


if __name__ == "__main__":
    unittest.main()
