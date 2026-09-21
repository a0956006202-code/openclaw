"""Policy and lifecycle controls for post-quantum cryptography.

Cryptographic primitives are intentionally supplied by an audited liboqs/HSM
provider. This module does not implement ML-KEM or ML-DSA itself; it validates
algorithm choices, migration state, and rotation evidence.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

PQC_KEM = {"ML-KEM-768", "ML-KEM-1024"}
PQC_SIGNATURES = {"ML-DSA-65", "ML-DSA-87", "SLH-DSA-SHAKE-128s"}
LEGACY_ALGORITHMS = {"RSA", "RSA-2048", "ECDH", "ECDSA", "X25519", "Ed25519"}
HYBRID_ALGORITHMS = {"X25519+ML-KEM-768", "ECDH+ML-KEM-768"}


class PQCPolicyError(ValueError):
    """Raised when an inventory or lifecycle action violates the PQC policy."""


@dataclass(frozen=True)
class KeyRecord:
    key_id: str
    purpose: str
    kem: str
    signature: str
    status: str
    created_at: str
    rotate_after_days: int
    provider: str
    legacy_dependency: bool = False

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "KeyRecord":
        required = (
            "key_id",
            "purpose",
            "kem",
            "signature",
            "status",
            "created_at",
            "rotate_after_days",
            "provider",
        )
        missing = [field for field in required if field not in value]
        if missing:
            raise PQCPolicyError(f"金鑰紀錄缺少欄位：{', '.join(missing)}")
        record = cls(**{field: value[field] for field in required}, legacy_dependency=bool(value.get("legacy_dependency", False)))
        if record.kem not in PQC_KEM:
            raise PQCPolicyError(f"不接受的 KEM：{record.kem}")
        if record.signature not in PQC_SIGNATURES:
            raise PQCPolicyError(f"不接受的簽章演算法：{record.signature}")
        if record.status not in {"active", "pending", "retired"}:
            raise PQCPolicyError(f"不接受的金鑰狀態：{record.status}")
        if record.rotate_after_days <= 0:
            raise PQCPolicyError("rotate_after_days 必須大於零")
        return record

    @property
    def rotation_due(self) -> bool:
        created = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) >= created + timedelta(days=self.rotate_after_days)


def audit_inventory(path: Path, *, today: date | None = None) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_records = payload.get("keys", payload) if isinstance(payload, dict) else payload
    if not isinstance(raw_records, list):
        raise PQCPolicyError("金鑰庫存必須是陣列或包含 keys 陣列的 JSON")
    records = [KeyRecord.from_dict(item) for item in raw_records]
    expired = []
    for record in records:
        created = datetime.fromisoformat(record.created_at.replace("Z", "+00:00"))
        reference = datetime.combine(today or date.today(), datetime.min.time(), tzinfo=timezone.utc)
        if reference >= created + timedelta(days=record.rotate_after_days):
            expired.append(record.key_id)
    return {
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "total_keys": len(records),
        "pqc_keys": len(records),
        "rotation_due": expired,
        "legacy_dependencies": [record.key_id for record in records if record.legacy_dependency],
        "status": "action_required" if expired or any(record.legacy_dependency for record in records) else "compliant",
    }


def create_rotation_request(record: KeyRecord, *, provider: str | None = None) -> dict[str, Any]:
    if record.status == "retired":
        raise PQCPolicyError("不可替換已 retired 的金鑰紀錄")
    selected_provider = provider or os.getenv("PQC_PROVIDER")
    if not selected_provider:
        raise PQCPolicyError("請設定 PQC_PROVIDER，或明確提供 audited provider")
    return {
        "type": "pqc_key_rotation_request",
        "request_id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "replaces_key_id": record.key_id,
        "purpose": record.purpose,
        "kem": record.kem,
        "signature": record.signature,
        "provider": selected_provider,
        "status": "pending_provider_execution",
        "activation_requires": ["provider_attestation", "dual_control_approval", "decrypt_test", "audit_log"],
        "private_key_material": "never_written_by_this_module",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PQC 金鑰庫存審計與輪換請求工具")
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit = subparsers.add_parser("audit")
    audit.add_argument("inventory", type=Path)
    rotate = subparsers.add_parser("rotate")
    rotate.add_argument("inventory", type=Path)
    rotate.add_argument("key_id")
    rotate.add_argument("--provider")
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.inventory.read_text(encoding="utf-8"))
        records = [KeyRecord.from_dict(item) for item in payload.get("keys", payload)]
        if args.command == "audit":
            print(json.dumps(audit_inventory(args.inventory), indent=2, ensure_ascii=False))
        else:
            record = next(item for item in records if item.key_id == args.key_id)
            print(json.dumps(create_rotation_request(record, provider=args.provider), indent=2, ensure_ascii=False))
    except (PQCPolicyError, OSError, json.JSONDecodeError, StopIteration) as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
