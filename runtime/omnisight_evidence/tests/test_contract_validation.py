import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from omnisight_evidence import EvidenceStore
from omnisight_evidence.envelope import to_observation_envelope


ROOT = Path(__file__).resolve().parents[3]


class PublishedEnvelopeContractTests(unittest.TestCase):
    def test_runtime_envelope_validates_against_published_schema(self):
        schema_path = ROOT / "schemas" / "omnisight" / "observation-envelope.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        with tempfile.TemporaryDirectory() as temp:
            store = EvidenceStore(Path(temp) / "evidence.sqlite3")
            record = store.append(
                source_id="schema-fixture", media_type="image/png",
                payload=b"schema-test", producer="adapter-test",
                producer_version="0.1.0", epistemic_status="interpreted",
                observation={"objects": []}, limitations=["synthetic"],
                captured_at="2026-11-25T00:00:00Z",
            )
            envelope = to_observation_envelope(record, correlation_id="schema-contract")
            errors = list(validator.iter_errors(envelope))
            self.assertEqual(errors, [], "\\n".join(error.message for error in errors))


if __name__ == "__main__":
    unittest.main()
