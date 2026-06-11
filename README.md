[![Made with Python](https://forthebadge.com/api/badges/generate?primaryLabel=MADE+WITH&secondaryLabel=PYTHON&primaryBGColor=%23245bb8&secondaryBGColor=%23ffd034&primaryIcon=python&primaryIconColor=%23ffffff)](https://python.org)
[![Open Source](https://forthebadge.com/api/badges/generate?primaryLabel=OPEN&secondaryLabel=SOURCE&primaryBGColor=%23ffd034&secondaryBGColor=%23245bb8)](https://github.com/pratham2402/AutoExtract)
[![MIT License](https://forthebadge.com/api/badges/generate?primaryLabel=MIT&secondaryLabel=LICENSE&primaryBGColor=%23245bb8&secondaryBGColor=%23ffd034)](https://github.com/pratham2402/AutoExtract/blob/master/LICENSE)
[![Docker Ready](https://forthebadge.com/api/badges/generate?primaryLabel=DOCKER&secondaryLabel=READY&primaryBGColor=%23245bb8&secondaryBGColor=%23ffd034&primaryIcon=docker&primaryIconColor=%23ffffff)](https://docker.com)
[![Version 2.0.0](https://forthebadge.com/api/badges/generate?primaryLabel=VERSION&secondaryLabel=2.0.0&primaryBGColor=%23ffd034&secondaryBGColor=%23245bb8)](https://github.com/pratham2402/AutoExtract/releases)

# AutoExtract

Automated multi-format archive extraction daemon. Watches folders for compressed archives and extracts them automatically with no manual unzipping required.

![](https://github.com/pratham2402/AutoExtract/blob/master/ReadMe%20Banner%20Design.png)

## Features

- **Multi-format support** - ZIP, RAR, 7z, Tar, Tar.gz, Tar.bz2, ISO, CAB, and more
- **Event-driven** - Uses inotify (via watchdog) for instant extraction; falls back to polling
- **Recursive extraction** - Finds and extracts archives nested within archives
- **Password support** - Password-protected archives via config or password file
- **Webhook notifications** - Get notified on extraction success/failure via HTTP webhooks
- **Configurable** - YAML config file with environment variable overrides
- **Trash after extract** - Move archives to system Trash after successful extraction (safer than permanent delete)
- **Subfolder extraction** - Each archive extracted into its own folder
- **Daemon-ready** - Systemd service file and Docker support included
- **Graceful shutdown** - Signal handling for clean termination

## Quick Start

### Install

```bash
git clone https://github.com/pratham2402/AutoExtract.git
cd AutoExtract

python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Linux users also need the system `unrar` and `7z` binaries:
```bash
sudo apt-get update && sudo apt-get install -y unrar p7zip-full
```

### Configure

Edit `config.yaml` or set environment variables:

```yaml
watch:
  paths:
    - ~/Downloads
  patterns:
    - "*.zip"
    - "*.rar"
    - "*.7z"
    - "*.tar"
    - "*.tar.gz"
    - "*.tgz"
    - "*.tar.bz2"
    - "*.tbz2"
  debounce_seconds: 5.0

extraction:
  extract_to_subfolder: true
  delete_after: false
  trash_after: false
  recursive: true
  max_recursion_depth: 5
```

### Run

```bash
python -m autoextract
```

Or use the entry point after installing:
```bash
autoextract
```

## Configuration Reference

### Watch section

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `paths` | list | `[~/Downloads]` | Directories to monitor |
| `recursive` | bool | `false` | Watch subdirectories recursively |
| `patterns` | list | `*.zip, *.rar, *.7z, *.tar, *.tar.gz, *.tgz, *.tar.bz2, *.tbz2` | File patterns to match |
| `polling_interval` | int | `10` | Seconds between polls (when watchdog unavailable) |
| `debounce_seconds` | float | `5.0` | Wait for file to stop changing before extracting |

### Extraction section

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `output_dir` | str | `null` | Extraction target directory (null = same as source) |
| `extract_to_subfolder` | bool | `true` | Create subfolder named after archive |
| `delete_after` | bool | `false` | Permanently delete archive after successful extraction |
| `trash_after` | bool | `false` | Move archive to system Trash after successful extraction (safer than delete) |
| `keep_on_failure` | bool | `true` | Keep archive if extraction fails (only relevant with delete_after/trash_after) |
| `password` | str | `null` | Global password for encrypted archives |
| `password_file` | str | `null` | Path to file with passwords to try (one per line) |
| `recursive` | bool | `true` | Extract archives found within extracted content |
| `max_recursion_depth` | int | `5` | Maximum nesting depth for recursive extraction |

### Webhooks section

```yaml
webhooks:
  - url: "https://example.com/hook"
    events: ["extraction_success", "extraction_failure"]
    timeout: 30
    retries: 3
```

Events: `extraction_start`, `extraction_success`, `extraction_failure`

### Logging section

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `level` | str | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR) |
| `file` | str | `null` | Log file path (null = stdout) |
| `format` | str | `%(asctime)s - %(name)s - %(levelname)s - %(message)s` | Log format string |

## Environment Variables

All settings can be overridden with `AUTOEXTRACT_` prefixed env vars:

```bash
export AUTOEXTRACT_CONFIG=/path/to/config.yaml
export AUTOEXTRACT_WATCH_PATHS="/watch/dir1,/watch/dir2"
export AUTOEXTRACT_EXTRACTION_OUTPUT_DIR=/output
export AUTOEXTRACT_EXTRACTION_DELETE_AFTER=true
export AUTOEXTRACT_EXTRACTION_PASSWORD=secret
export AUTOEXTRACT_LOG_LEVEL=DEBUG
export AUTOEXTRACT_WEBHOOK_URL=https://hooks.example.com/notify
```

## Systemd Service

```bash
sudo cp autoextract.service /etc/systemd/system/
sudo mkdir -p /etc/autoextract
sudo cp config.yaml /etc/autoextract/
sudo systemctl daemon-reload
sudo systemctl enable --now autoextract
```

## Docker

```bash
docker compose up -d
```

Or manually:

```bash
docker build -t autoextract .
docker run -d \
  -v ~/Downloads:/watch \
  -v ./extracted:/output \
  -v ./config.yaml:/etc/autoextract/config.yaml:ro \
  autoextract
```

## Supported Formats

| Format | Extension | Backend |
|--------|-----------|---------|
| ZIP | `.zip` | stdlib `zipfile` |
| RAR | `.rar`, `.cbr` | `rarfile` + `unrar` |
| 7-Zip | `.7z` | `py7zr` |
| ISO | `.iso` | `py7zr` |
| CAB | `.cab` | `py7zr` |
| Tar | `.tar` | stdlib `tarfile` |
| Tar.gz | `.tar.gz`, `.tgz` | stdlib `tarfile` |
| Tar.bz2 | `.tar.bz2`, `.tbz2` | stdlib `tarfile` |
| Tar.xz | `.tar.xz`, `.txz` | stdlib `tarfile` |
| Tar.zst | `.tar.zst`, `.tzst` | stdlib `tarfile` |

## Project Structure

```
AutoExtract/
├── autoextract/
│   ├── __init__.py       # Package version
│   ├── __main__.py       # Entry point
│   ├── config.py         # YAML + env var configuration
│   ├── extractors.py     # Multi-format extraction engine
│   ├── monitor.py        # Watchdog + polling folder monitor
│   └── webhooks.py       # HTTP notification callbacks
├── config.yaml           # Default configuration
├── setup.py              # Package installer
├── Dockerfile
├── docker-compose.yml
├── autoextract.service   # systemd unit file
├── requirements.txt
├── LICENSE
└── README.md
```

## Author

[pratham2402](https://github.com/pratham2402)
