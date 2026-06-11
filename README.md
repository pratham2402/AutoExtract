[![Made with Python](https://forthebadge.com/api/badges/generate?primaryLabel=MADE+WITH&secondaryLabel=PYTHON&primaryBGColor=%23306998&secondaryBGColor=%23ffd43b&primaryIcon=python&primaryIconColor=%23ffffff)](https://python.org)
[![Open Source](https://forthebadge.com/api/badges/generate?primaryLabel=OPEN&secondaryLabel=SOURCE&primaryBGColor=%232ea44f&secondaryBGColor=%231b4332)](https://github.com/pratham2402/AutoExtract)
[![MIT License](https://forthebadge.com/api/badges/generate?primaryLabel=MIT&secondaryLabel=LICENSE&primaryBGColor=%237c3aed&secondaryBGColor=%234c1d95)](https://github.com/pratham2402/AutoExtract/blob/master/LICENSE)
[![Docker Ready](https://forthebadge.com/api/badges/generate?primaryLabel=DOCKER&secondaryLabel=READY&primaryBGColor=%230db7ed&secondaryBGColor=%231e3a5f&primaryIcon=docker&primaryIconColor=%23ffffff)](https://docker.com)
[![Version 2.1.0](https://forthebadge.com/api/badges/generate?primaryLabel=VERSION&secondaryLabel=2.1.0&primaryBGColor=%23e01e5a&secondaryBGColor=%23ffd034)](https://github.com/pratham2402/AutoExtract/releases)

# AutoExtract

Automated multi-format archive extraction daemon. Watches folders for compressed archives and extracts them automatically with no manual unzipping required.

![](https://github.com/pratham2402/AutoExtract/blob/master/ReadMe%20Banner%20Design.png)

## ✨ Features

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

## 🚀 Quick Start

### 📥 Install

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

### 🛠️ Configure

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

### 🪄 Setup Wizard

The fastest way to get started — interactive prompts, no YAML editing:

```bash
autoextract setup
```

### ▶️ Run

```bash
autoextract
```

Or with a custom config:

```bash
autoextract --config /path/to/config.yaml
```

## 📦 Standalone Binary

Download a single executable for your platform — no Python or pip required. These are built automatically on every tagged release.

System dependencies still required: `unrar` for RAR support and `7z` for 7z/ISO support.

```bash
# Download the binary for your platform from:
#   https://github.com/pratham2402/AutoExtract/releases/latest
chmod +x autoextract-linux-x86_64
sudo mv autoextract-linux-x86_64 /usr/local/bin/autoextract

# Run
autoextract --config /path/to/config.yaml
```

### Build from source

```bash
pip install -e ".[full]" pyinstaller
bash scripts/build-binary.sh
# Binary at: dist/autoextract
```

## ⚙️ Configuration Reference

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
| `max_extracted_size` | int | `53687091200` | Max total uncompressed bytes before aborting (default 50 GB) |
| `max_file_count` | int | `10000` | Max files in a single archive before aborting |
| `min_free_space` | int | `1073741824` | Minimum free disk space required before extraction (default 1 GB) |

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

## 🔧 Environment Variables

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

## 🖥️ Systemd Service

```bash
sudo cp autoextract.service /etc/systemd/system/
sudo mkdir -p /etc/autoextract
sudo cp config.yaml /etc/autoextract/
sudo systemctl daemon-reload
sudo systemctl enable --now autoextract
```

## 🐳 Docker

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

## 📦 Supported Formats

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

## 📁 Project Structure

```
AutoExtract/
├── autoextract/
│   ├── __init__.py       # Package version
│   ├── __main__.py       # Entry point
│   ├── config.py         # YAML + env var configuration
│   ├── extractors.py     # Multi-format extraction engine
│   ├── monitor.py        # Watchdog + polling folder monitor
│   ├── security.py       # Zip-bomb protection, disk space check
│   ├── webhooks.py       # HTTP notification callbacks
│   └── cli_setup.py      # Interactive terminal setup wizard
├── scripts/
│   └── build-binary.sh   # PyInstaller standalone binary build
├── .github/workflows/
│   └── build.yml         # Multi-platform CI build + release
├── config.yaml           # Default configuration
├── setup.py              # Package installer
├── Dockerfile
├── docker-compose.yml
├── autoextract.service   # systemd unit file
├── requirements.txt
├── LICENSE
└── README.md
```

## 👥 Contributors

[![Contributors](https://contrib.rocks/image?repo=pratham2402/AutoExtract)](https://github.com/pratham2402/AutoExtract/graphs/contributors)
