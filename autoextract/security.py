"""Security checks: zip-bomb protection, disk space verification, format detection."""

from __future__ import annotations

import logging
import shutil
import zipfile
import tarfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

MAGIC_SIGNATURES: dict[bytes, str] = {
    b"\x50\x4b\x03\x04": "zip",
    b"\x50\x4b\x05\x06": "zip",
    b"\x50\x4b\x07\x08": "zip",
    b"\x52\x61\x72\x21\x1a\x07\x00": "rar",
    b"\x52\x61\x72\x21\x1a\x07\x01\x00": "rar5",
    b"\x37\x7a\xbc\xaf\x27\x1c": "7z",
    b"\x1f\x8b\x08": "gz",
    b"\x42\x5a\x68": "bz2",
    b"\xfd\x37\x7a\x58\x5a\x00": "xz",
    b"\x28\xb5\x2f\xfd": "zst",
}


class SecurityError(Exception):
    pass


class ZipBombError(SecurityError):
    pass


class DiskSpaceError(SecurityError):
    pass


def detect_format(file_path: Path) -> Optional[str]:
    """Read magic bytes to identify the actual archive format."""
    try:
        with open(file_path, "rb") as fh:
            header = fh.read(16)
    except OSError:
        return None

    # Check longest signatures first to avoid partial matches
    # (e.g. RAR5 8-byte signature starts with RAR4's 7-byte sequence)
    signatures: list[tuple[bytes, str]] = sorted(
        MAGIC_SIGNATURES.items(), key=lambda kv: len(kv[0]), reverse=True
    )
    for signature, fmt in signatures:
        if header.startswith(signature):
            return fmt
    return None


def check_zip_bomb_zfile(file_path: Path, max_size: int, max_files: int) -> tuple[int, int]:
    """Scan a ZIP file's central directory to estimate uncompressed size and file count."""
    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            total_size = 0
            file_count = 0
            for info in zf.infolist():
                file_count += 1
                if file_count > max_files:
                    raise ZipBombError(
                        f"Archive contains {file_count} files (limit: {max_files})"
                    )
                total_size += info.file_size
                if total_size > max_size:
                    raise ZipBombError(
                        f"Archive expands to {_fmt_size(total_size)} (limit: {_fmt_size(max_size)})"
                    )
                if info.file_size > 10 * 1024 * 1024 and info.compress_size > 0:
                    ratio = info.file_size / info.compress_size
                    if ratio > 100:
                        raise ZipBombError(
                            f"Suspicious compression ratio {ratio:.0f}:1 for '{info.filename}'"
                        )
            return total_size, file_count
    except zipfile.BadZipFile:
        return 0, 0


def check_zip_bomb_tarfile(file_path: Path, max_size: int, max_files: int) -> tuple[int, int]:
    """Scan a TAR file to estimate uncompressed size and file count."""
    try:
        with tarfile.open(file_path, "r:*") as tf:
            total_size = 0
            file_count = 0
            for member in tf.getmembers():
                if not member.isfile():
                    continue
                file_count += 1
                if file_count > max_files:
                    raise ZipBombError(
                        f"Archive contains {file_count} files (limit: {max_files})"
                    )
                total_size += member.size
                if total_size > max_size:
                    raise ZipBombError(
                        f"Archive expands to {_fmt_size(total_size)} (limit: {_fmt_size(max_size)})"
                    )
            return total_size, file_count
    except tarfile.TarError:
        return 0, 0


def check_disk_space(output_dir: Path, estimated_size: int, min_free: int) -> None:
    """Verify enough disk space is available before extraction."""
    output_dir = output_dir.resolve()
    while not output_dir.exists():
        output_dir = output_dir.parent
    usage = shutil.disk_usage(output_dir)
    if estimated_size > 0 and usage.free < estimated_size + min_free:
        raise DiskSpaceError(
            f"Not enough disk space: need {_fmt_size(estimated_size + min_free)}, "
            f"have {_fmt_size(usage.free)} free on {output_dir}"
        )
    elif usage.free < min_free:
        raise DiskSpaceError(
            f"Minimum free space not met: need {_fmt_size(min_free)}, "
            f"have {_fmt_size(usage.free)} free on {output_dir}"
        )


def _fmt_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"
