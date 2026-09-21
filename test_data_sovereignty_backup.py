import io
import tarfile
import unittest
from pathlib import Path

from data_sovereignty_backup import BackupError, _safe_members


class DataSovereigntyBackupTests(unittest.TestCase):
    def test_rejects_path_traversal_member(self):
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w") as archive:
            info = tarfile.TarInfo("../../outside.txt")
            info.size = 0
            archive.addfile(info)
        stream.seek(0)
        with tarfile.open(fileobj=stream, mode="r") as archive:
            with self.assertRaises(BackupError):
                _safe_members(archive)

    def test_accepts_relative_member(self):
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w") as archive:
            info = tarfile.TarInfo("data/example.json")
            info.size = 0
            archive.addfile(info)
        stream.seek(0)
        with tarfile.open(fileobj=stream, mode="r") as archive:
            self.assertEqual(len(_safe_members(archive)), 1)

    def test_rejects_symlink_member(self):
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w") as archive:
            info = tarfile.TarInfo("data/link")
            info.type = tarfile.SYMTYPE
            info.linkname = "../../outside"
            archive.addfile(info)
        stream.seek(0)
        with tarfile.open(fileobj=stream, mode="r") as archive:
            with self.assertRaises(BackupError):
                _safe_members(archive)


if __name__ == "__main__":
    unittest.main()
