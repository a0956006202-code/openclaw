"""Encrypted, multi-destination backup and disaster recovery CLI.

The command intentionally delegates encryption and remote transports to mature
CLI tools so secrets stay outside Python and the same workflow works on a NAS,
CI runner, or a recovery host.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Iterable

DEFAULT_SOURCE_PATHS = (
    "*.py",
    "*.gs",
    "*.json",
    "*.md",
    "requirements.txt",
    "package.json",
    ".github/workflows",
    "data",
    "digital_assets",
    "vault",
    "logs",
)
DEFAULT_EXCLUDES = (".git", "__pycache__", ".venv", "*.env", "*secret*", "*token*", "*.key")


class BackupError(RuntimeError):
    """Raised when a backup or restore cannot be completed safely."""


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _run(command: list[str], *, input_path: Path | None = None) -> None:
    try:
        if input_path:
            with input_path.open("rb") as source:
                result = subprocess.run(command, stdin=source, capture_output=True, text=True, check=False)
        else:
            result = subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise BackupError(f"找不到必要工具：{command[0]}") from exc
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise BackupError(f"命令失敗：{' '.join(command)}\n{detail}")


def _matches_exclude(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    return any(
        part in {".git", "__pycache__", ".venv"}
        or part.endswith((".env", ".key"))
        or "secret" in part.lower()
        or "token" in part.lower()
        for part in relative.parts
    )


def _iter_files(root: Path, source_paths: Iterable[str]) -> list[Path]:
    files: set[Path] = set()
    for pattern in source_paths:
        matches = root.glob(pattern)
        for match in matches:
            if match.is_file() and not _matches_exclude(match, root):
                files.add(match)
            elif match.is_dir():
                for child in match.rglob("*"):
                    if child.is_file() and not _matches_exclude(child, root):
                        files.add(child)
    return sorted(files)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_archive(root: Path, files: list[Path], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output, "w:gz") as archive:
        for path in files:
            archive.add(path, arcname=path.relative_to(root).as_posix(), recursive=False)


def _encrypt(archive: Path, encrypted: Path) -> None:
    recipient = os.getenv("BACKUP_AGE_RECIPIENT")
    if not recipient:
        raise BackupError("請設定 BACKUP_AGE_RECIPIENT；未提供金鑰時拒絕建立未加密備份")
    try:
        result = subprocess.run(
            ["age", "-r", recipient, "-o", str(encrypted), str(archive)],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise BackupError("找不到 age，請先安裝 age") from exc
    if result.returncode:
        raise BackupError(result.stderr.strip() or "age 加密失敗")


def _upload_rclone(archive: Path) -> list[str]:
    destinations = [item.strip() for item in os.getenv("BACKUP_RCLONE_DESTINATIONS", "").split(",") if item.strip()]
    for destination in destinations:
        _run(["rclone", "copyto", str(archive), f"{destination.rstrip('/')}/{archive.name}"])
    return destinations


def _copy_to_nas(archive: Path) -> str | None:
    destination = os.getenv("BACKUP_NAS_PATH")
    if not destination:
        return None
    target = Path(destination).expanduser()
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(archive, target / archive.name)
    return str(target)


def _pin_ipfs(archive: Path) -> str | None:
    if os.getenv("BACKUP_IPFS_ENABLED", "false").lower() != "true":
        return None
    try:
        result = subprocess.run(["ipfs", "add", "-Q", str(archive)], capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise BackupError("已啟用 IPFS，但找不到 ipfs CLI") from exc
    if result.returncode:
        raise BackupError(result.stderr.strip() or "IPFS 封存失敗")
    return result.stdout.strip()


def create_backup(root: Path, output_dir: Path, source_paths: Iterable[str], *, dry_run: bool = False) -> Path:
    files = _iter_files(root, source_paths)
    if not files:
        raise BackupError("沒有找到可備份的檔案")
    stamp = _utc_stamp()
    archive = output_dir / f"openclaw-{stamp}.tar.gz"
    encrypted = output_dir / f"{archive.name}.age"
    if dry_run:
        print(json.dumps({"files": len(files), "archive": str(encrypted), "dry_run": True}, ensure_ascii=False))
        return encrypted

    _write_archive(root, files, archive)
    _encrypt(archive, encrypted)
    archive.unlink()
    destinations = _upload_rclone(encrypted)
    nas = _copy_to_nas(encrypted)
    cid = _pin_ipfs(encrypted)
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "archive": encrypted.name,
        "sha256": _sha256(encrypted),
        "file_count": len(files),
        "destinations": destinations,
        "nas": nas,
        "ipfs_cid": cid,
        "encryption": "age",
        "pqc_status": "migration_required",
        "pqc_provider": os.getenv("PQC_PROVIDER"),
    }
    (output_dir / f"{encrypted.name}.manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return encrypted


def _safe_members(archive: tarfile.TarFile) -> list[tarfile.TarInfo]:
    members = archive.getmembers()
    for member in members:
        path = PurePosixPath(member.name)
        if path.is_absolute() or ".." in path.parts or member.issym() or member.islnk():
            raise BackupError(f"拒絕不安全的封存路徑：{member.name}")
    return members


def restore_backup(encrypted: Path, destination: Path) -> None:
    identity = os.getenv("BACKUP_AGE_IDENTITY")
    if not identity:
        raise BackupError("請設定 BACKUP_AGE_IDENTITY 才能還原")
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        archive = Path(temporary) / "restore.tar.gz"
        try:
            result = subprocess.run(
                ["age", "-d", "-i", identity, "-o", str(archive), str(encrypted)],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise BackupError("找不到 age，請先安裝 age") from exc
        if result.returncode:
            raise BackupError(result.stderr.strip() or "age 解密失敗")
        with tarfile.open(archive, "r:gz") as source:
            members = _safe_members(source)
            source.extractall(destination, members=members)
    print(f"已還原至：{destination}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OpenClaw 跨平台加密備份與災難還原")
    subparsers = parser.add_subparsers(dest="command", required=True)
    backup = subparsers.add_parser("backup")
    backup.add_argument("--root", type=Path, default=Path.cwd())
    backup.add_argument("--output-dir", type=Path, default=Path("vault/disaster-recovery"))
    backup.add_argument("--dry-run", action="store_true")
    restore = subparsers.add_parser("restore")
    restore.add_argument("archive", type=Path)
    restore.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "backup":
            create_backup(args.root.resolve(), args.output_dir, DEFAULT_SOURCE_PATHS, dry_run=args.dry_run)
        else:
            restore_backup(args.archive.resolve(), args.destination.resolve())
    except BackupError as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
