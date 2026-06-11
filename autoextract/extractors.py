"""Multi-format archive extraction engine."""

from __future__ import annotations

import logging
import os
import shutil
import zipfile
import tarfile
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from send2trash import send2trash

import py7zr

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    pass


class PasswordRequiredError(ExtractionError):
    pass


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


class ArchiveExtractor(ABC):
    @abstractmethod
    def can_handle(self, file_path: Path) -> bool: ...

    @abstractmethod
    def extract(
        self,
        file_path: Path,
        output_dir: Path,
        password: Optional[str] = None,
    ) -> None: ...


class ZipExtractor(ArchiveExtractor):
    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".zip"

    def extract(
        self,
        file_path: Path,
        output_dir: Path,
        password: Optional[str] = None,
    ) -> None:
        try:
            pwd = password.encode("utf-8") if password else None
            with zipfile.ZipFile(file_path, "r") as zf:
                zf.extractall(output_dir, pwd=pwd)
            logger.info("Extracted ZIP: %s -> %s", file_path.name, output_dir)
        except RuntimeError as exc:
            if "password" in str(exc).lower():
                raise PasswordRequiredError(
                    f"Password required for {file_path.name}"
                ) from exc
            raise ExtractionError(f"Failed to extract {file_path.name}: {exc}") from exc
        except Exception as exc:
            raise ExtractionError(f"Failed to extract {file_path.name}: {exc}") from exc


class RarExtractor(ArchiveExtractor):
    def __init__(self):
        import rarfile
        self._rarfile = rarfile

    def can_handle(self, file_path: Path) -> bool:
        suffix = file_path.suffix.lower()
        return suffix in (".rar", ".cbr")

    def extract(
        self,
        file_path: Path,
        output_dir: Path,
        password: Optional[str] = None,
    ) -> None:
        try:
            rf = self._rarfile.RarFile(file_path)
            if rf.needs_password() and password:
                rf.setpassword(password)
            rf.extractall(output_dir)
            rf.close()
            logger.info("Extracted RAR: %s -> %s", file_path.name, output_dir)
        except self._rarfile.NeedFirstVol as exc:
            raise ExtractionError(
                f"Multi-volume RAR missing first volume: {file_path.name}"
            ) from exc
        except self._rarfile.PasswordRequired as exc:
            raise PasswordRequiredError(
                f"Password required for {file_path.name}"
            ) from exc
        except Exception as exc:
            raise ExtractionError(f"Failed to extract {file_path.name}: {exc}") from exc


class SevenZipExtractor(ArchiveExtractor):
    _handled = {".7z", ".iso", ".xz", ".bz2", ".lzma", ".zst", ".lz4", ".arj", ".cab"}

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self._handled

    def extract(
        self,
        file_path: Path,
        output_dir: Path,
        password: Optional[str] = None,
    ) -> None:
        try:
            with py7zr.SevenZipFile(
                file_path, mode="r", password=password
            ) as archive:
                archive.extractall(output_dir)
            logger.info("Extracted 7z: %s -> %s", file_path.name, output_dir)
        except py7zr.Bad7zFile as exc:
            raise ExtractionError(
                f"Corrupt or unsupported archive: {file_path.name}"
            ) from exc
        except py7zr.PasswordRequired as exc:
            raise PasswordRequiredError(
                f"Password required for {file_path.name}"
            ) from exc
        except Exception as exc:
            raise ExtractionError(f"Failed to extract {file_path.name}: {exc}") from exc


class TarExtractor(ArchiveExtractor):
    _handled = {
        ".tar", ".gz", ".tgz", ".bz2", ".tbz2",
        ".tbz", ".xz", ".txz", ".zst", ".tzst", ".lz", ".lzma",
    }
    _tar_mode_map = {
        ".gz": "r:gz", ".tgz": "r:gz",
        ".bz2": "r:bz2", ".tbz2": "r:bz2", ".tbz": "r:bz2",
        ".xz": "r:xz", ".txz": "r:xz",
        ".zst": "r:zst", ".tzst": "r:zst",
        ".lz": "r:lzma", ".lzma": "r:lzma",
    }

    def can_handle(self, file_path: Path) -> bool:
        name = file_path.name.lower()
        if name.endswith(".tar"):
            return True
        for double in (".tar.gz", ".tar.bz2", ".tar.xz", ".tar.zst", ".tar.lz", ".tar.lzma"):
            if name.endswith(double):
                return True
        suffix = file_path.suffix.lower()
        if suffix in self._handled and suffix != ".tar":
            return True
        return False

    def _resolve_mode(self, file_path: Path) -> str:
        name = file_path.name.lower()
        if name.endswith(".tar.gz") or name.endswith(".tgz"):
            return "r:gz"
        if name.endswith(".tar.bz2") or name.endswith(".tbz2") or name.endswith(".tbz"):
            return "r:bz2"
        if name.endswith(".tar.xz") or name.endswith(".txz"):
            return "r:xz"
        if name.endswith(".tar.zst") or name.endswith(".tzst"):
            return "r:zst"
        if name.endswith(".tar.lz") or name.endswith(".tar.lzma"):
            return "r:lzma"
        if name.endswith(".tar"):
            return "r:"
        suffix = file_path.suffix.lower()
        return self._tar_mode_map.get(suffix, "r:*")

    def extract(
        self,
        file_path: Path,
        output_dir: Path,
        password: Optional[str] = None,
    ) -> None:
        try:
            mode = self._resolve_mode(file_path)
            with tarfile.open(file_path, mode) as tf:
                tf.extractall(output_dir)
            logger.info("Extracted TAR: %s -> %s", file_path.name, output_dir)
        except tarfile.TarError as exc:
            raise ExtractionError(f"Failed to extract {file_path.name}: {exc}") from exc
        except Exception as exc:
            raise ExtractionError(f"Failed to extract {file_path.name}: {exc}") from exc


EXTRACTORS: list[ArchiveExtractor] = [
    ZipExtractor(),
    RarExtractor(),
    TarExtractor(),
    SevenZipExtractor(),
]


def _find_archives(directory: Path) -> list[Path]:
    archives: list[Path] = []
    for item in directory.rglob("*"):
        if item.is_file():
            for ext in EXTRACTORS:
                try:
                    if ext.can_handle(item):
                        archives.append(item)
                        break
                except Exception:
                    pass
    return archives


def extract_archive(
    file_path: Path,
    output_dir: Path,
    extract_to_subfolder: bool = True,
    delete_after: bool = False,
    trash_after: bool = False,
    keep_on_failure: bool = True,
    password: Optional[str] = None,
) -> str:
    if extract_to_subfolder:
        stem = file_path.stem
        if stem.endswith(".tar"):
            stem = stem[:-4]
        extract_dir = output_dir / stem
    else:
        extract_dir = output_dir

    _ensure_dir(extract_dir)

    for extractor in EXTRACTORS:
        if extractor.can_handle(file_path):
            try:
                extractor.extract(file_path, extract_dir, password=password)
                if trash_after:
                    send2trash(str(file_path))
                    logger.info("Moved archive to trash: %s", file_path.name)
                elif delete_after:
                    file_path.unlink()
                    logger.info("Deleted archive after extraction: %s", file_path.name)
                return str(extract_dir)
            except Exception:
                if keep_on_failure and (delete_after or trash_after):
                    logger.warning(
                        "Extraction failed, keeping archive (keep_on_failure=true): %s",
                        file_path.name,
                    )
                raise
    raise ExtractionError(f"No extractor found for: {file_path.name}")


def extract_recursive(
    file_path: Path,
    output_dir: Path,
    extract_to_subfolder: bool = True,
    delete_after: bool = False,
    trash_after: bool = False,
    keep_on_failure: bool = True,
    password: Optional[str] = None,
    passwords: Optional[list[str]] = None,
    max_depth: int = 5,
    _depth: int = 0,
) -> list[str]:
    if _depth >= max_depth:
        logger.debug("Max recursion depth reached at %d: %s", _depth, file_path.name)
        return []

    candidates = [password] if password else []
    if passwords:
        candidates.extend(passwords)

    extracted_paths: list[str] = []
    last_error: Optional[Exception] = None

    for pwd in candidates or [None]:
        try:
            target = extract_archive(
                file_path,
                output_dir,
                extract_to_subfolder=extract_to_subfolder,
                delete_after=delete_after,
                trash_after=trash_after,
                keep_on_failure=keep_on_failure,
                password=pwd,
            )
            extracted_paths.append(target)
            last_error = None
            break
        except PasswordRequiredError:
            last_error = PasswordRequiredError(
                f"Password required for {file_path.name}"
            )
            continue
        except ExtractionError as exc:
            last_error = exc
            continue

    if last_error is not None:
        raise last_error

    if not extracted_paths:
        return []

    nested = _find_archives(Path(extracted_paths[0]))
    for archive in nested:
        try:
            extracted_paths.extend(
                extract_recursive(
                    archive,
                    archive.parent,
                    extract_to_subfolder=extract_to_subfolder,
                    delete_after=delete_after,
                    trash_after=trash_after,
                    keep_on_failure=keep_on_failure,
                    password=password,
                    passwords=passwords,
                    max_depth=max_depth,
                    _depth=_depth + 1,
                )
            )
        except ExtractionError as exc:
            logger.warning("Failed recursive extraction: %s", exc)

    return extracted_paths
