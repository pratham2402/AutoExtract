"""Entry point for AutoExtract — run with `python -m autoextract`."""

from __future__ import annotations

import logging
import os
import signal
import sys
import time
from pathlib import Path

from autoextract.config import load_config, Config
from autoextract.extractors import (
    extract_recursive,
    ExtractionError,
    PasswordRequiredError,
)
from autoextract.monitor import Monitor
from autoextract.webhooks import notify

logger: logging.Logger | None = None


def _setup_logging(config: Config) -> logging.Logger:
    root = logging.getLogger()
    root.setLevel(getattr(logging, config.logging.level.upper(), logging.INFO))
    root.handlers.clear()

    handler: logging.Handler
    if config.logging.file:
        handler = logging.FileHandler(os.path.expanduser(config.logging.file))
    else:
        handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(logging.Formatter(config.logging.format))
    root.addHandler(handler)

    pkg_logger = logging.getLogger("autoextract")
    return pkg_logger


def _load_passwords(config: Config) -> list[str]:
    passwords: list[str] = []
    if config.extraction.password:
        passwords.append(config.extraction.password)
    if config.extraction.password_file:
        pf = os.path.expanduser(config.extraction.password_file)
        if os.path.isfile(pf):
            with open(pf, "r") as fh:
                for line in fh:
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#"):
                        passwords.append(stripped)
    return passwords


def _process_archive(file_path: Path, config: Config) -> None:
    global logger
    passwords = _load_passwords(config)
    output_dir = Path(
        os.path.expanduser(config.extraction.output_dir or str(file_path.parent))
    )

    archive_name = file_path.name
    archive_path = str(file_path)

    t0 = time.monotonic()
    notify(config.webhooks, "extraction_start", archive_name, archive_path)

    try:
        extracted = extract_recursive(
            file_path,
            output_dir,
            extract_to_subfolder=config.extraction.extract_to_subfolder,
            delete_after=config.extraction.delete_after,
            keep_on_failure=config.extraction.keep_on_failure,
            password=config.extraction.password,
            passwords=passwords,
            max_depth=config.extraction.max_recursion_depth,
        )
        duration_ms = (time.monotonic() - t0) * 1000
        logger.info(
            "Extraction complete: %s (%d items, %.0f ms)",
            archive_name,
            len(extracted),
            duration_ms,
        )
        notify(
            config.webhooks,
            "extraction_success",
            archive_name,
            archive_path,
            output_path=str(extracted[0]) if extracted else str(output_dir),
            duration_ms=duration_ms,
        )
    except PasswordRequiredError as exc:
        duration_ms = (time.monotonic() - t0) * 1000
        logger.warning("Password required: %s", archive_name)
        notify(
            config.webhooks,
            "extraction_failure",
            archive_name,
            archive_path,
            error=str(exc),
            duration_ms=duration_ms,
        )
    except ExtractionError as exc:
        duration_ms = (time.monotonic() - t0) * 1000
        logger.error("Extraction failed: %s — %s", archive_name, exc)
        notify(
            config.webhooks,
            "extraction_failure",
            archive_name,
            archive_path,
            error=str(exc),
            duration_ms=duration_ms,
        )


def main() -> None:
    global logger

    config = load_config()
    logger = _setup_logging(config)
    logger.info("AutoExtract v%s starting", __import__("autoextract").__version__)

    passwords = _load_passwords(config)
    logger.debug(
        "Watch paths: %s | patterns: %s | passwords: %d loaded",
        config.watch.paths,
        config.watch.patterns,
        len(passwords),
    )

    monitor = Monitor(
        paths=config.watch.paths,
        patterns=config.watch.patterns,
        callback=lambda fp: _process_archive(fp, config),
        recursive=config.watch.recursive,
        debounce_seconds=config.watch.debounce_seconds,
        polling_interval=config.watch.polling_interval,
    )

    def _shutdown(signum: int, frame: any) -> None:
        logger.info("Received signal %d, shutting down", signum)
        monitor.stop()

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    try:
        monitor.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        monitor.stop()
        logger.info("AutoExtract stopped")


if __name__ == "__main__":
    main()
