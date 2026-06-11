"""Interactive terminal-based setup wizard for AutoExtract."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

import questionary
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

logger = logging.getLogger(__name__)
console = Console()

HEADER_COLOR = "#ffd034"
ACCENT_COLOR = "#245bb8"

DEFAULT_FORMATS = ["zip", "rar", "7z", "tar", "tar.gz", "tgz", "tar.bz2", "tbz2"]

STYLE = questionary.Style([
    ("qmark", "fg:#ffd034 bold"),
    ("question", "bold"),
    ("answer", "fg:#245bb8 bold"),
    ("pointer", "fg:#ffd034 bold"),
    ("highlighted", "fg:#245bb8 bold"),
    ("selected", "fg:#245bb8"),
    ("separator", "fg:#666666"),
    ("instruction", "fg:#888888 italic"),
])


def _header() -> None:
    panel = Panel(
        Text("AutoExtract Setup\nAutomated archive extraction daemon", style=f"bold {HEADER_COLOR}"),
        border_style=HEADER_COLOR,
        padding=(1, 4),
    )
    console.print()
    console.print(panel)
    console.print()


def _section(title: str) -> None:
    console.print(f"\n[bold {ACCENT_COLOR}]{title}[/bold {ACCENT_COLOR}]")


def _success(msg: str) -> None:
    console.print(f"  [green]✔[/green] {msg}")


def _warn(msg: str) -> None:
    console.print(f"  [yellow]⚠[/yellow] {msg}")


def _error(msg: str) -> None:
    console.print(f"  [red]✘[/red] {msg}")


def _detect_default_downloads() -> str:
    home = Path.home()
    candidates = [
        home / "Downloads",
        home / "downloads",
        home / "Download",
    ]
    for path in candidates:
        if path.is_dir():
            return str(path)
    return str(home)


def _find_binary(name: str) -> Optional[str]:
    path = shutil.which(name)
    if path:
        return path
    alt_paths = [
        f"/usr/bin/{name}",
        f"/usr/local/bin/{name}",
        f"/opt/homebrew/bin/{name}",
        f"/bin/{name}",
    ]
    for p in alt_paths:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None


def check_dependencies() -> dict[str, Optional[str]]:
    deps = {}
    for name in ("unrar", "7z", "7zz", "7za"):
        found = _find_binary(name)
        if found and name not in deps:
            deps[name] = found
    has_7z = any(deps.get(k) for k in ("7z", "7zz", "7za"))
    return {
        "unrar": deps.get("unrar"),
        "7z": next((deps[k] for k in ("7z", "7zz", "7za") if k in deps), None),
    }


def _run_setup_flow() -> dict:
    config = {}

    _section("Watch folders")
    default_dl = _detect_default_downloads()
    paths_input = questionary.text(
        "Which folders should I monitor for new archives?",
        default=default_dl,
        style=STYLE,
        instruction=" (comma-separated for multiple)",
    ).unsafe_ask()
    config["watch"] = {
        "paths": [p.strip() for p in paths_input.split(",") if p.strip()],
        "recursive": False,
        "patterns": [f"*.{f}" for f in DEFAULT_FORMATS],
        "polling_interval": 10,
        "debounce_seconds": 5.0,
    }

    _section("Output directory")
    use_default_output = questionary.confirm(
        "Extract to the same folder as the archive?", default=True, style=STYLE
    ).unsafe_ask()
    if not use_default_output:
        output_dir = questionary.text(
            "Where should extracted files go?", style=STYLE
        ).unsafe_ask()
        config["extraction"] = {"output_dir": output_dir}
    else:
        config["extraction"] = {"output_dir": None}

    _section("Archive formats")
    format_choices = [
        questionary.Choice("ZIP", checked=True),
        questionary.Choice("RAR", checked=True),
        questionary.Choice("7-Zip", checked=True),
        questionary.Choice("TAR / TAR.GZ / TAR.BZ2", checked=True),
        questionary.Choice("ISO", checked=False),
    ]
    selected = questionary.checkbox(
        "Which formats should I handle?", choices=format_choices, style=STYLE
    ).unsafe_ask()
    patterns = []
    for choice in selected:
        if choice == "ZIP":
            patterns.append("*.zip")
        elif choice == "RAR":
            patterns.append("*.rar")
        elif choice == "7-Zip":
            patterns.append("*.7z")
        elif choice == "TAR / TAR.GZ / TAR.BZ2":
            patterns.extend(["*.tar", "*.tar.gz", "*.tgz", "*.tar.bz2", "*.tbz2"])
        elif choice == "ISO":
            patterns.append("*.iso")
    config["watch"]["patterns"] = patterns

    _section("Post-extraction behavior")
    action = questionary.select(
        "What should happen to archives after extraction?",
        choices=[
            questionary.Choice("Keep them", value="keep"),
            questionary.Choice("Move to Trash (recoverable)", value="trash"),
            questionary.Choice("Delete permanently", value="delete"),
        ],
        style=STYLE,
    ).unsafe_ask()
    config["extraction"]["trash_after"] = (action == "trash")
    config["extraction"]["delete_after"] = (action == "delete")
    config["extraction"]["keep_on_failure"] = True
    config["extraction"]["extract_to_subfolder"] = True
    config["extraction"]["recursive"] = True
    config["extraction"]["max_recursion_depth"] = 5
    config["extraction"]["password"] = None
    config["extraction"]["password_file"] = None

    _section("Notifications")
    enable_webhooks = questionary.confirm(
        "Enable webhook notifications on extraction events?",
        default=False,
        style=STYLE,
    ).unsafe_ask()
    if enable_webhooks:
        webhook_url = questionary.text(
            "Webhook URL:", style=STYLE
        ).unsafe_ask()
        config["webhooks"] = [{
            "url": webhook_url,
            "events": ["extraction_success", "extraction_failure"],
            "timeout": 30,
            "retries": 3,
        }]
    else:
        config["webhooks"] = []

    _section("Logging")
    log_level = questionary.select(
        "Logging level?",
        choices=[
            questionary.Choice("INFO (recommended)", value="INFO"),
            questionary.Choice("DEBUG (verbose)", value="DEBUG"),
            questionary.Choice("WARNING (problems only)", value="WARNING"),
        ],
        style=STYLE,
    ).unsafe_ask()
    config["logging"] = {
        "level": log_level,
        "file": None,
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    }

    return config


def _save_config(config: dict, config_path: str) -> None:
    config_dir = os.path.dirname(os.path.abspath(config_path))
    if config_dir and not os.path.isdir(config_dir):
        os.makedirs(config_dir, exist_ok=True)
    with open(config_path, "w") as fh:
        yaml.safe_dump(config, fh, default_flow_style=False, allow_unicode=True, sort_keys=False)


def _test_extraction(config: dict) -> bool:
    console.print()
    console.print("[bold]Testing extraction...[/bold]")

    watch_paths = config.get("watch", {}).get("paths", [])
    if not watch_paths:
        _error("No watch paths configured")
        return False

    test_dir = Path(watch_paths[0])
    test_dir.mkdir(parents=True, exist_ok=True)

    tmp = tempfile.mkdtemp()
    try:
        test_zip = Path(tmp) / "_autoextract_test.zip"
        test_file = Path(tmp) / "_ae_test.txt"
        test_file.write_text("AutoExtract setup verification.")
        with zipfile.ZipFile(test_zip, "w") as zf:
            zf.write(test_file, test_file.name)

        dest = test_dir / test_zip.name
        shutil.copy2(test_zip, dest)

        extract_dir = test_dir / "_autoextract_test"
        extract_dir.mkdir(exist_ok=True)
        with zipfile.ZipFile(dest, "r") as zr:
            zr.extractall(extract_dir)

        extracted_file = extract_dir / test_file.name
        if extracted_file.exists() and extracted_file.read_text() == "AutoExtract setup verification.":
            dest.unlink()
            shutil.rmtree(extract_dir)
            _success("Extraction works correctly")
            return True
        else:
            _error("Extraction verification failed")
            return False
    except Exception as exc:
        _error(f"Extraction test failed: {exc}")
        return False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_setup() -> None:
    _header()

    _section("System check")
    deps = check_dependencies()
    if deps["unrar"]:
        _success(f"unrar found ({deps['unrar']})")
    else:
        _warn("unrar not found - RAR support unavailable. Install with: sudo apt install unrar")

    if deps["7z"]:
        _success(f"7z found ({deps['7z']})")
    else:
        _warn("7z not found - 7z/ISO support unavailable. Install with: sudo apt install p7zip-full")

    try:
        import send2trash
        _success("send2trash available")
    except ImportError:
        _warn("send2trash not installed - trash feature unavailable")

    config = _run_setup_flow()

    _section("Save configuration")
    default_config_path = os.path.expanduser("~/.config/autoextract/config.yaml")
    config_path = questionary.text(
        "Where should I save the configuration?",
        default=default_config_path,
        style=STYLE,
    ).unsafe_ask()

    _save_config(config, config_path)
    _success(f"Configuration saved to {config_path}")

    _test_extraction(config)

    _section("Systemd service")
    install_service = questionary.confirm(
        "Install as a systemd service to run automatically at startup?",
        default=False,
        style=STYLE,
    ).unsafe_ask()

    if install_service:
        _install_service(config_path)

    console.print()
    summary = Panel(
        Text(
            f"Setup complete!\n\n"
            f"Config: {config_path}\n"
            f"Run manually: autoextract\n"
            f"Run with config: autoextract --config {config_path}",
            style="bold",
        ),
        border_style=HEADER_COLOR,
        padding=(1, 3),
    )
    console.print(summary)
    console.print()


def _install_service(config_path: str) -> None:
    service_src = Path(__file__).parent.parent / "autoextract.service"
    service_dest = Path.home() / ".config" / "systemd" / "user" / "autoextract.service"

    if not service_src.is_file():
        _error("Service file not found in project directory")
        return

    if sys.platform != "linux":
        _warn("Systemd service installation is only supported on Linux")
        return

    service_dest.parent.mkdir(parents=True, exist_ok=True)

    content = service_src.read_text()
    content = content.replace(
        "ExecStart=/usr/bin/python3 -m autoextract",
        f"ExecStart={sys.executable} -m autoextract --config {config_path}",
    )
    content = content.replace("WorkingDirectory=/opt/autoextract", f"WorkingDirectory={Path(__file__).parent.parent}")
    service_dest.write_text(content)

    try:
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "--user", "enable", "--now", "autoextract"], check=True)
        _success("Service installed and started")
        _success("Check status: systemctl --user status autoextract")
    except subprocess.CalledProcessError:
        _warn(
            "Could not enable service automatically. Run these commands manually:\n"
            f"  cp {service_src} {service_dest}\n"
            "  systemctl --user daemon-reload\n"
            "  systemctl --user enable --now autoextract"
        )
