"""Comprehensive validation tests for darwin_1 RAFT dataset."""
import json
import re
from pathlib import Path
import unittest

from raft.convo_structurer import is_transcript
from raft.project import DatasetPaths

ROOT = Path(__file__).resolve().parents[1]
DARWIN_1 = ROOT / "darwin_1"
START_DATE = "1859-11-25"
END_DATE = "1868-12-31"


class Darwin1ValidationTests(unittest.TestCase):
    def test_project_manifest(self):
        manifest_path = DARWIN_1 / "raft.json"
        self.assertTrue(manifest_path.exists())
        data = json.loads(manifest_path.read_text())
        self.assertEqual(data.get("format"), "raft.project.v1")
        self.assertEqual(data.get("name"), "darwin_1")
        self.assertEqual(data.get("collection"), "darwin_1")
        self.assertEqual(data.get("target"), "Charles Darwin")

        # Test RAFT dataset paths loading
        paths = DatasetPaths.from_project(DARWIN_1)
        self.assertEqual(paths.name, "darwin_1")
        self.assertEqual(paths.collection, "darwin_1")
        self.assertTrue(paths.project)

    def test_required_directories(self):
        for sub in ["conversations", "corpus", "blobs", "fetch", "metadata"]:
            d = DARWIN_1 / sub
            self.assertTrue(d.is_dir(), f"Missing directory {d}")

    def test_transcripts_integrity(self):
        conv_dir = DARWIN_1 / "conversations"
        transcripts = sorted(conv_dir.glob("transcript-*.json"))
        self.assertEqual(len(transcripts), 765)

        # Check gapless numbering
        expected_names = [f"transcript-{i:04d}.json" for i in range(1, 766)]
        actual_names = [t.name for t in transcripts]
        self.assertEqual(actual_names, expected_names)

        answer_hashes = set()
        for t_path in transcripts:
            t = json.loads(t_path.read_text())
            self.assertTrue(is_transcript(t), f"Failed is_transcript for {t_path.name}")

            # Check participants
            self.assertEqual(t["participants"]["a"], "Charles Darwin")
            self.assertTrue(t["participants"]["q"])
            self.assertNotEqual(t["participants"]["q"], "Charles Darwin")

            # Check date
            date = t["date"]
            self.assertTrue(re.fullmatch(r"\d{4}-\d{2}-\d{2}", date), f"Bad date {date} in {t_path.name}")
            self.assertTrue(START_DATE <= date <= END_DATE, f"Date {date} outside interval in {t_path.name}")

            # Check URL
            self.assertTrue(t["url"].startswith("https://www.darwinproject.ac.uk/letter/?docId=letters/"))
            self.assertIn("#raft-response-", t["url"])

            # Check context
            self.assertTrue(t.get("context"))

            # Check exchange
            self.assertEqual(len(t["exchanges"]), 1)
            q, a = t["exchanges"][0]
            self.assertTrue(q.strip(), f"Empty question in {t_path.name}")
            self.assertTrue(a.strip(), f"Empty answer in {t_path.name}")

            # Check no HTML tags leaked
            self.assertFalse(re.search(r"<(?:p|div|span|br|a|table|tr|td)\b", q), f"HTML in question {t_path.name}")
            self.assertFalse(re.search(r"<(?:p|div|span|br|a|table|tr|td)\b", a), f"HTML in answer {t_path.name}")

    def test_grounding_documents_integrity(self):
        doc_path = DARWIN_1 / "corpus/documents.jsonl"
        self.assertTrue(doc_path.exists())

        lines = [line.strip() for line in doc_path.read_text().splitlines() if line.strip()]
        self.assertEqual(len(lines), 1262)

        # Load conversation answers to verify strict disjointness
        conv_dir = DARWIN_1 / "conversations"
        answer_texts = set()
        for t_path in conv_dir.glob("transcript-*.json"):
            t = json.loads(t_path.read_text())
            answer_texts.add(t["exchanges"][0][1].strip())

        titles = set()
        for i, line in enumerate(lines, 1):
            doc = json.loads(line)
            self.assertEqual(set(doc.keys()), {"title", "link", "date", "content"})

            date = doc["date"]
            self.assertTrue(re.fullmatch(r"\d{4}-\d{2}-\d{2}", date), f"Bad date in doc {i}: {date}")
            self.assertTrue(START_DATE <= date <= END_DATE, f"Date outside interval in doc {i}: {date}")

            content = doc["content"]
            self.assertTrue(content.strip(), f"Empty content in doc {i}")
            self.assertFalse(re.search(r"<(?:p|div|span|br|a|table|tr|td)\b", content), f"HTML in doc {i}")

            # Strict disjointness
            self.assertNotIn(content.strip(), answer_texts, f"Grounding document {doc['title']} duplicates a conversation answer!")

            # Title uniqueness
            self.assertNotIn(doc["title"], titles, f"Duplicate title: {doc['title']}")
            titles.add(doc["title"])


if __name__ == "__main__":
    unittest.main()
