import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from am_toolkit import synthetic
from am_toolkit.config import CLIENT, DATA, DATE, ROOT
from am_toolkit.io import read_csv, read_json, sha256
from am_toolkit.run import active_average, verify_snapshot
from am_toolkit.validation import monthly_sequence

# Configuration
WORK = ROOT / ".work"
FETCH_SCRIPT = ROOT / "scripts" / "fetch_nport.py"
VALID_URL = "https://www.sec.gov/Archives/edgar/data/123/456/test.xml"
SPEC = importlib.util.spec_from_file_location("fetch_nport", FETCH_SCRIPT)
FETCH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FETCH)


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        WORK.mkdir(exist_ok=True)

    def test_snapshot_matches_seeded_generation(self):
        expected = verify_snapshot()
        with tempfile.TemporaryDirectory(dir=WORK) as directory:
            temporary_paths = {key: Path(directory)/path.name for key, path in synthetic.SNAPSHOT_FILES.items()}
            with patch.object(synthetic, "DATA", Path(directory)), patch.object(synthetic, "SNAPSHOT_FILES", temporary_paths):
                synthetic.generate()
            for name, digest in expected["files"].items():
                self.assertEqual(sha256(Path(directory)/name), digest, name)

    def test_snapshot_counts(self):
        self.assertEqual(len(read_csv(DATA/"bonds.csv")), 444)
        self.assertEqual(len(read_csv(DATA/"manager_returns.csv")), 108)
        self.assertEqual(len(read_csv(DATA/"daily_aum.csv")), 169)

    def test_calendar_gap_fails(self):
        for dates in (("2025-01-31", "2025-03-31"), ("2025-01-30",), ("2025-01-31", "2025-01-31")):
            with self.assertRaises(ValueError):
                monthly_sequence(dates)

    def test_hand_average_and_coverage(self):
        account = {CLIENT: "A", "opened": "2025-09-29"}
        rows = [{CLIENT: "A", DATE: "2025-09-29", "aum": 100}, {CLIENT: "A", DATE: "2025-09-30", "aum": 200}]
        self.assertEqual(active_average(rows, account, "2025-09-01", "2025-09-30"), 150)
        self.assertEqual(active_average(rows, {**account, "closed": ""}, "2025-09-01", "2025-09-30"), 150)
        with self.assertRaises(ValueError):
            active_average(rows[:1], account, "2025-09-01", "2025-09-30")
        with self.assertRaises(ValueError):
            active_average([rows[0], rows[0]], account, "2025-09-01", "2025-09-30")


class FetchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        WORK.mkdir(exist_ok=True)

    def test_url_scope(self):
        self.assertEqual(FETCH.validate_url(VALID_URL), VALID_URL)
        for url in ("https://evil.example/test.xml", "https://www.sec.gov.evil.example/Archives/edgar/data/a", "http://www.sec.gov/Archives/edgar/data/a"):
            with self.assertRaises(ValueError):
                FETCH.validate_url(url)

    def test_mock_success_saves_raw_and_manifest(self):
        raw = (DATA/"nport_style.xml").read_bytes()

        class Response:
            status = 200
            url = VALID_URL

            def __enter__(self):
                return self

            def __exit__(self, *arguments):
                return False

            def read(self, limit):
                return raw[:limit]

        class Opener:
            def open(self, *arguments, **keywords):
                return Response()

        with tempfile.TemporaryDirectory(dir=WORK) as directory:
            with patch.object(FETCH, "OUTPUT", Path(directory)), patch.object(FETCH, "build_opener", return_value=Opener()), patch.object(FETCH.time, "sleep"):
                path = FETCH.fetch(VALID_URL, "Test project test@example.org")
            manifest = read_json(path)
            self.assertEqual(manifest["status"], "downloaded")
            self.assertEqual(manifest["holding_count"], 2)
            self.assertEqual(sha256(Path(directory)/manifest["filename"]), manifest["sha256"])

    def test_mock_failure_records_negative_result(self):
        with tempfile.TemporaryDirectory(dir=WORK) as directory:
            with patch.object(FETCH, "OUTPUT", Path(directory)), patch.object(FETCH, "build_opener", side_effect=OSError("offline")), patch.object(FETCH.time, "sleep"):
                with self.assertRaises(OSError):
                    FETCH.fetch(VALID_URL, "Test project test@example.org")
            manifests = list(Path(directory).glob("*.manifest.json"))
            self.assertEqual(len(manifests), 1)
            self.assertEqual(read_json(manifests[0])["status"], "failed")
            self.assertFalse(list(Path(directory).glob("*.xml")))


if __name__ == "__main__":
    unittest.main()

