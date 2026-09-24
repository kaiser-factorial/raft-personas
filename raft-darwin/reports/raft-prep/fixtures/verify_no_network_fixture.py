"""Reproducible no-network RAFT format/ordering fixture; synthetic text only."""
import json
import socket
import tempfile
from pathlib import Path

from raft import generate_finetune
from raft.convo_structurer import import_conversation_file, write_transcript
from raft.project import DatasetPaths
from raft.sources import append_corpus_records, date_num, in_window


class NoNetwork:
    def __enter__(self):
        self.original = socket.socket
        socket.socket = self.blocked

    def __exit__(self, *_):
        socket.socket = self.original

    @staticmethod
    def blocked(*args, **kwargs):
        raise AssertionError("network access is forbidden in this fixture")


class MockMemoryManager:
    constructors = []
    calls = []

    @staticmethod
    def reset_trace_stats():
        pass

    def __init__(self, dataset, metadata):
        self.constructors.append({str(k.value): v for k, v in metadata.items()})

    def get_similar_and_summarize(self, exchange, prev_answer, store=True):
        self.calls.append({"question": exchange[0], "answer": exchange[1], "prev_answer": prev_answer, "store": store})
        return ""


def metadata_dates(path):
    return [item["metadata"]["date"] for item in json.loads(Path(path).read_text()) if "metadata" in item]


def main():
    with NoNetwork():
        root = Path(tempfile.mkdtemp(prefix="raft-format-fixture-"))
        (root / "raft.json").write_text(json.dumps({"format": "raft.project.v1", "name": "synthetic", "collection": "synthetic"}))
        dataset = DatasetPaths.from_project(root)
        source = root / "source.json"
        source.write_text(json.dumps({"participants": {"q": "Q", "a": "A"}, "date": "1840-01-02", "url": "u", "context": "a letter from Q", "exchanges": [["in", "out"]]}))
        imported = json.loads(Path(import_conversation_file(dataset, str(source), "A")).read_text())
        direct = json.loads(Path(write_transcript(dataset, {"q": "Q", "a": "A"}, "1840-01-02", "u", [["in", "out1"], ["in2", "out2"]], index=1, context="a letter from Q")).read_text())
        assert "context" not in imported
        assert direct["context"] == "a letter from Q"
        write_transcript(dataset, {"q": "Q", "a": "A"}, "1839-01-01", "u3", [["in3", "out3"]], index=3, context="a letter from Q")

        generate_finetune.MemoryManager = MockMemoryManager
        generate_finetune.generate_finetune(dataset)
        fresh_dates = metadata_dates(dataset.finetune_path)
        fresh_calls = list(MockMemoryManager.calls)
        assert fresh_dates == ["1840-01-02"], fresh_dates
        assert [c["prev_answer"] for c in fresh_calls] == ["", "out1"], fresh_calls
        assert all(c["store"] for c in fresh_calls)
        assert MockMemoryManager.constructors[0] == {"participants": {"q": "Q", "a": "A"}, "date": "1840-01-02", "url": "u"}

        write_transcript(dataset, {"q": "Q", "a": "A"}, "1841-01-01", "u2", [["in2f", "out2f"]], index=2, context="a letter from Q")
        generate_finetune.generate_finetune(dataset)
        resumed_dates = metadata_dates(dataset.finetune_path)
        assert resumed_dates == ["1840-01-02", "1841-01-01", "1839-01-01"], resumed_dates

        missing_key = root / "conversations" / "transcript-0004.json"
        missing_key_failures = []
        for absent in ("date", "url"):
            value = {"participants": {"q": "Q", "a": "A"}, "date": "1840-01-01", "url": "u4", "exchanges": [["q", "a"]]}
            del value[absent]
            missing_key.write_text(json.dumps(value))
            try:
                generate_finetune.process_transcripts(dataset, "4", False)
            except KeyError as exc:
                assert exc.args == (absent,), exc
                missing_key_failures.append(absent)
            else:
                raise AssertionError(f"Missing {absent} did not fail")
        assert missing_key_failures == ["date", "url"]

        duplicate_record = {"title": "one", "link": "same", "date": "1840-01-01", "content": "synthetic"}
        duplicate_counts = [append_corpus_records(dataset, [duplicate_record, duplicate_record]), append_corpus_records(dataset, [duplicate_record])]
        assert duplicate_counts == [1, 0], duplicate_counts
        assert len((root / "corpus" / "documents.jsonl").read_text().splitlines()) == 1
        result = {"importer_preserves_context": "context" in imported, "direct_writer_preserves_context": "context" in direct, "fresh_gap_metadata_dates": fresh_dates, "fresh_call_prev_answers": [c["prev_answer"] for c in fresh_calls], "fresh_constructor_metadata": MockMemoryManager.constructors[0], "resumed_metadata_dates": resumed_dates, "filename_order": [dataset.transcript_path(i).name for i in (1, 2, 3)], "date_num_same_day": date_num("1840-01-02"), "bounded_window_inclusive": [in_window("1840-01-01", "1840-01-01", "1840-01-01"), in_window("1840-01-02", "1840-01-01", "1840-01-01")], "duplicate_link_append_counts": duplicate_counts, "missing_date_url_keys_fail": True, "network_or_llm": False, "assertions": "passed"}
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
