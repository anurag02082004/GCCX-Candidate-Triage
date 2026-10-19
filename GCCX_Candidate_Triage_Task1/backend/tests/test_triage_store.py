"""Small standard-library smoke test for the candidate store.
Run from backend with: python -m unittest discover -s tests
"""
import tempfile
import unittest
from pathlib import Path
import os

# Configure an isolated DB before importing the service.
_TMP = tempfile.TemporaryDirectory()
os.environ["TRIAGE_DB_PATH"] = str(Path(_TMP.name) / "test.sqlite3")

from services import triage_store


class TriageStoreTests(unittest.TestCase):
    def setUp(self):
        triage_store.init_db()

    def test_dataset_loaded(self):
        items = triage_store.list_candidates()
        self.assertEqual(len(items), 48)

    def test_search_and_skill_filter(self):
        results = triage_store.list_candidates(search="Sameer")
        self.assertTrue(any(item["name"] == "Sameer Rao" for item in results))
        skill_results = triage_store.list_candidates(skill="Python")
        self.assertTrue(all(any("python" in s.lower() for s in x["skills"]) for x in skill_results))

    def test_shortlist_and_tags_persist(self):
        updated = triage_store.update_candidate("cand_001", True, ["follow-up", "strong ownership"])
        self.assertTrue(updated["is_shortlisted"])
        self.assertEqual(updated["tags"], ["follow-up", "strong ownership"])
        self.assertTrue(any(x["id"] == "cand_001" for x in triage_store.list_candidates(shortlisted_only=True)))


if __name__ == "__main__":
    unittest.main()
