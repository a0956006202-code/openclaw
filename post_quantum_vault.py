"""Compatibility boundary for post-quantum key management.

Key splitting is not encryption and random byte slices are not recoverable
secret sharing. Real PQC key generation belongs in an audited liboqs/HSM
provider and is represented by :mod:`pqc_crypto_policy`.
"""

from pqc_crypto_policy import KeyRecord, create_rotation_request


class PostQuantumSharding:
    def split_master_key(
        self,
        secret_key: bytes,
        total_shares: int = 5,
        threshold: int = 3,
    ):
        raise NotImplementedError(
            "不可將隨機 bytes 當作 PQC secret sharing；請使用 audited liboqs/HSM provider"
        )


__all__ = ["KeyRecord", "PostQuantumSharding", "create_rotation_request"]
