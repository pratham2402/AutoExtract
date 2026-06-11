"""Configuration system: YAML config file with environment variable overrides."""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

ENV_PREFIX = "AUTOEXTRACT_"


def _parse_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return value.strip().lower() in ("true", "1", "yes", "on")


@dataclass
class WatchConfig:
    paths: list[str] = field(default_factory=lambda: ["~/Downloads"])
    recursive: bool = False
    patterns: list[str] = field(
        default_factory=lambda: [
            "*.zip", "*.rar", "*.7z", "*.tar",
            "*.tar.gz", "*.tgz", "*.tar.bz2", "*.tbz2",
        ]
    )
    polling_interval: int = 10
    debounce_seconds: float = 5.0

    @classmethod
    def from_dict(cls, data: dict) -> "WatchConfig":
        return cls(
            paths=[os.path.expanduser(p) for p in data.get("paths", ["~/Downloads"])],
            recursive=_parse_bool(data.get("recursive", False)),
            patterns=data.get("patterns", cls().patterns),
            polling_interval=int(data.get("polling_interval", 10)),
            debounce_seconds=float(data.get("debounce_seconds", 5.0)),
        )


@dataclass
class ExtractionConfig:
    output_dir: Optional[str] = None
    extract_to_subfolder: bool = True
    delete_after: bool = False
    trash_after: bool = False
    keep_on_failure: bool = True
    password: Optional[str] = None
    password_file: Optional[str] = None
    recursive: bool = True
    max_recursion_depth: int = 5
    max_extracted_size: int = 50 * 1024 * 1024 * 1024
    max_file_count: int = 10000
    min_free_space: int = 1024 * 1024 * 1024

    @classmethod
    def from_dict(cls, data: dict) -> "ExtractionConfig":
        return cls(
            output_dir=data.get("output_dir"),
            extract_to_subfolder=_parse_bool(data.get("extract_to_subfolder", True)),
            delete_after=_parse_bool(data.get("delete_after", False)),
            trash_after=_parse_bool(data.get("trash_after", False)),
            keep_on_failure=_parse_bool(data.get("keep_on_failure", True)),
            password=data.get("password"),
            password_file=data.get("password_file"),
            recursive=_parse_bool(data.get("recursive", True)),
            max_recursion_depth=int(data.get("max_recursion_depth", 5)),
            max_extracted_size=int(data.get("max_extracted_size", 50 * 1024 * 1024 * 1024)),
            max_file_count=int(data.get("max_file_count", 10000)),
            min_free_space=int(data.get("min_free_space", 1024 * 1024 * 1024)),
        )


@dataclass
class WebhookConfig:
    url: str = ""
    events: list[str] = field(default_factory=lambda: ["extraction_success", "extraction_failure"])
    timeout: int = 30
    retries: int = 3

    @classmethod
    def from_dict(cls, data: dict) -> "WebhookConfig":
        return cls(
            url=data.get("url", ""),
            events=data.get("events", ["extraction_success", "extraction_failure"]),
            timeout=int(data.get("timeout", 30)),
            retries=int(data.get("retries", 3)),
        )


@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: Optional[str] = None
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @classmethod
    def from_dict(cls, data: dict) -> "LoggingConfig":
        return cls(
            level=data.get("level", "INFO"),
            file=data.get("file"),
            format=data.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
        )


@dataclass
class Config:
    watch: WatchConfig = field(default_factory=WatchConfig)
    extraction: ExtractionConfig = field(default_factory=ExtractionConfig)
    webhooks: list[WebhookConfig] = field(default_factory=list)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    processed_files: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        webhooks_raw = data.get("webhooks", []) or []
        webhooks = [WebhookConfig.from_dict(w) for w in webhooks_raw if w.get("url")]
        return cls(
            watch=WatchConfig.from_dict(data.get("watch", {})),
            extraction=ExtractionConfig.from_dict(data.get("extraction", {})),
            webhooks=webhooks,
            logging=LoggingConfig.from_dict(data.get("logging", {})),
            processed_files=data.get("processed_files"),
        )


def _find_config_file() -> Optional[Path]:
    search_paths = [
        os.environ.get(f"{ENV_PREFIX}CONFIG"),
        os.path.join(os.getcwd(), "config.yaml"),
        os.path.expanduser("~/.config/autoextract/config.yaml"),
        "/etc/autoextract/config.yaml",
    ]
    for sp in search_paths:
        if sp and os.path.isfile(sp):
            return Path(sp)
    return None


def load_config(config_path: Optional[str] = None) -> Config:
    path = config_path or _find_config_file()
    if path and os.path.isfile(path):
        logger.info("Loading configuration from %s", path)
        with open(path, "r") as fh:
            raw = yaml.safe_load(fh) or {}
    else:
        logger.info("No configuration file found; using defaults")
        raw = {}

    config = Config.from_dict(raw)
    config = _apply_env_overrides(config)
    return config


def _apply_env_overrides(config: Config) -> Config:
    if os.environ.get(f"{ENV_PREFIX}WATCH_PATHS"):
        config.watch.paths = [
            p.strip()
            for p in os.environ[f"{ENV_PREFIX}WATCH_PATHS"].split(",")
        ]
    if os.environ.get(f"{ENV_PREFIX}EXTRACTION_OUTPUT_DIR"):
        config.extraction.output_dir = os.environ[f"{ENV_PREFIX}EXTRACTION_OUTPUT_DIR"]
    if os.environ.get(f"{ENV_PREFIX}EXTRACTION_DELETE_AFTER"):
        config.extraction.delete_after = _parse_bool(
            os.environ[f"{ENV_PREFIX}EXTRACTION_DELETE_AFTER"]
        )
    if os.environ.get(f"{ENV_PREFIX}EXTRACTION_PASSWORD"):
        config.extraction.password = os.environ[f"{ENV_PREFIX}EXTRACTION_PASSWORD"]
    if os.environ.get(f"{ENV_PREFIX}LOG_LEVEL"):
        config.logging.level = os.environ[f"{ENV_PREFIX}LOG_LEVEL"]
    if os.environ.get(f"{ENV_PREFIX}WEBHOOK_URL"):
        config.webhooks.append(
            WebhookConfig(url=os.environ[f"{ENV_PREFIX}WEBHOOK_URL"])
        )
    return config
