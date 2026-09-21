import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from pqc_crypto_policy import KeyRecord, PQCPolicyError, audit_inventory, create_rotation_request


class PQCCryptoPolicyTests(unittest.TestCase):
    def make_record(self, **overrides):
        record = {
            "key_id": "key-001",
            "purpose": "backup",
            "kem": "ML-KEM-768",
            "signature": "ML-DSA-65",
            "status": "active",
            "created_at": "2020-01-01T00:00:00+00:00",
            "rotate_after_days": 90,
            "provider": "test-hsm",
        }
        record.update(overrides)
        return KeyRecord.from_dict(record)

    def test_audit_flags_rotation_due(self):
        with tempfile.TemporaryDirectory() as directory:
            inventory = Path(directory) / "inventory.json"
            inventory.write_text(json.dumps({"keys": [self.make_record().__dict__]}), encoding="utf-8")
            result = audit_inventory(inventory)
            self.assertEqual(result["status"], "action_required")
            self.assertEqual(result["rotation_due"], ["key-001"])

    def test_rejects_legacy_only_kem(self):
        with self.assertRaises(PQCPolicyError):
            self.make_record(kem="RSA-2048")

    def test_rotation_request_contains_no_private_material(self):
        request = create_rotation_request(self.make_record(), provider="test-hsm")
        self.assertEqual(request["status"], "pending_provider_execution")
        self.assertEqual(request["private_key_material"], "never_written_by_this_module")


if __name__ == "__main__":
    unittest.main()
