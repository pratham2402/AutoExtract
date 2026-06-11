"""Event-driven folder monitoring using watchdog with polling fallback."""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

WATCHDOG_AVAILABLE = False
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    WATCHDOG_AVAILABLE = True
except ImportError:
    logger.info("watchdog not installed; falling back to polling mode")


class _ArchiveHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[Path], None], patterns: list[str]):
        super().__init__()
        self._callback = callback
        self._patterns = patterns
        self._pending: dict[str, float] = {}
        self._debounce_seconds: float = 5.0
        self._stable_size: dict[str, tuple[int, int]] = {}

    def set_debounce(self, seconds: float) -> None:
        self._debounce_seconds = seconds

    def on_created(self, event: any) -> None:
        if not event.is_directory:
            self._on_file_event(Path(event.src_path))

    def on_moved(self, event: any) -> None:
        if not event.is_directory:
            self._on_file_event(Path(event.dest_path))

    def on_modified(self, event: any) -> None:
        if not event.is_directory:
            self._on_file_event(Path(event.src_path))

    def _matches_pattern(self, file_path: Path) -> bool:
        name = file_path.name.lower()
        for pattern in self._patterns:
            p = pattern.lower()
            if p.startswith("*."):
                if name.endswith(p[1:]):
                    return True
            elif p == name:
                return True
        return False

    def _on_file_event(self, file_path: Path) -> None:
        if not self._matches_pattern(file_path):
            return
        if not file_path.exists():
            return

        now = time.time()
        key = str(file_path)

        try:
            current_size = file_path.stat().st_size
        except OSError:
            return

        prev = self._pending.get(key, 0)
        if now - prev < self._debounce_seconds:
            prev_state = self._stable_size.get(key, (0, 0))
            if prev_state[0] == current_size and prev_state[1] >= 2:
                self._pending.pop(key, None)
                self._stable_size.pop(key, None)
                logger.info("File stable, triggering extraction: %s", file_path.name)
                self._callback(file_path)
            else:
                checks = prev_state[1] + 1 if prev_state[0] == current_size else 0
                self._stable_size[key] = (current_size, checks)
        else:
            self._pending[key] = now
            self._stable_size[key] = (current_size, 0)


class Monitor:
    def __init__(
        self,
        paths: list[str],
        patterns: list[str],
        callback: Callable[[Path], None],
        recursive: bool = False,
        debounce_seconds: float = 5.0,
        polling_interval: int = 10,
    ):
        self._paths = [Path(p).expanduser().resolve() for p in paths]
        self._patterns = patterns
        self._callback = callback
        self._recursive = recursive
        self._debounce_seconds = debounce_seconds
        self._polling_interval = polling_interval
        self._observer: Optional[any] = None
        self._running = False

    def start(self) -> None:
        self._running = True
        if WATCHDOG_AVAILABLE:
            self._start_watchdog()
        else:
            self._start_polling()

    def stop(self) -> None:
        self._running = False
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None

    def _start_watchdog(self) -> None:
        logger.info(
            "Starting watchdog monitor on %d path(s): %s",
            len(self._paths),
            [str(p) for p in self._paths],
        )
        handler = _ArchiveHandler(self._callback, self._patterns)
        handler.set_debounce(self._debounce_seconds)
        self._observer = Observer()
        for watch_path in self._paths:
            if watch_path.is_dir():
                self._observer.schedule(handler, str(watch_path), recursive=self._recursive)
                logger.info("Watching: %s", watch_path)
            else:
                logger.warning("Path does not exist, skipping: %s", watch_path)
        self._observer.start()

    def _start_polling(self) -> None:
        logger.info(
            "Starting polling monitor on %d path(s), interval=%ds",
            len(self._paths),
            self._polling_interval,
        )
        seen: dict[str, float] = {}
        while self._running:
            for watch_path in self._paths:
                if not watch_path.is_dir():
                    continue
                iterator = watch_path.rglob("*") if self._recursive else watch_path.glob("*")
                for item in iterator:
                    if not item.is_file():
                        continue
                    key = str(item)
                    name = item.name.lower()
                    matched = any(
                        name.endswith(p.lstrip("*").lower())
                        for p in self._patterns
                        if p.startswith("*.")
                    ) or any(
                        name == p.lower() for p in self._patterns if not p.startswith("*.")
                    )
                    if not matched:
                        continue

                    try:
                        mtime = item.stat().st_mtime
                        size = item.stat().st_size
                    except OSError:
                        continue

                    prev = seen.get(key)
                    if prev is None:
                        seen[key] = mtime
                    elif mtime > prev:
                        seen[key] = mtime
                    elif mtime == prev and size > 0:
                        stable_key = f"stable_{key}"
                        if stable_key not in seen:
                            seen[stable_key] = time.time()
                        elif time.time() - seen[stable_key] > self._debounce_seconds:
                            seen[key] = mtime
                            del seen[stable_key]
                            logger.info("File stable, triggering extraction: %s", item.name)
                            self._callback(item)

            time.sleep(self._polling_interval)
