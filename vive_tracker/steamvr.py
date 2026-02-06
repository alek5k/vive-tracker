import json
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple


def enable_vive_trackers_without_hmd(
    steam_root: Optional[str] = None,
    *,
    kill_steam_processes: bool = True,
    prompt_user: bool = True,
    dry_run: bool = False,
) -> Tuple[Path, Path]:
    """
    Enables Vive Trackers without an HMD by modifying SteamVR settings.

    - ALWAYS creates backups (default.vrsettings_BACKUP)
    - Enables driver_null
    - Disables requireHmd
    - Forces null driver
    - Enables multiple drivers

    WARNING:
      Unsupported workaround. SteamVR updates may break this.
    """

    warning = (
        "WARNING: This is an UNSUPPORTED SteamVR workaround.\n"
        "It modifies SteamVR configuration files and may require room setup again.\n\n"
        "DO YOU WISH TO CONTINUE?\n"
        "Type EXACTLY: YES\n> "
    )

    if prompt_user:
        if input(warning).strip() != "YES":
            raise SystemExit("Aborted by user.")

    steam_root_path = _infer_steam_root(steam_root)
    steamvr_root = steam_root_path / "steamapps" / "common" / "SteamVR"

    driver_null_settings = (
        steamvr_root
        / "drivers"
        / "null"
        / "resources"
        / "settings"
        / "default.vrsettings"
    )
    main_settings = (
        steamvr_root
        / "resources"
        / "settings"
        / "default.vrsettings"
    )

    if not driver_null_settings.exists():
        raise FileNotFoundError(driver_null_settings)
    if not main_settings.exists():
        raise FileNotFoundError(main_settings)

    if kill_steam_processes:
        _stop_steam_and_steamvr(dry_run=dry_run)

    # Backups are MANDATORY
    _backup_file(driver_null_settings, dry_run=dry_run)
    _backup_file(main_settings, dry_run=dry_run)

    _edit_driver_null_settings(driver_null_settings, dry_run=dry_run)
    _edit_main_steamvr_settings(main_settings, dry_run=dry_run)

    return driver_null_settings, main_settings


def check_steamvr_settings(steam_root: Optional[str] = None) -> Tuple[bool, str]:
    """
    Check if SteamVR is configured for trackers without HMD.
    
    Returns:
        Tuple[bool, str]: (is_configured_correctly, message)
    """
    try:
        steam_root_path = _infer_steam_root(steam_root)
        steamvr_root = steam_root_path / "steamapps" / "common" / "SteamVR"
        
        driver_null_settings = (
            steamvr_root
            / "drivers"
            / "null"
            / "resources"
            / "settings"
            / "default.vrsettings"
        )
        main_settings = (
            steamvr_root
            / "resources"
            / "settings"
            / "default.vrsettings"
        )
        
        if not driver_null_settings.exists():
            return False, f"Driver null settings not found: {driver_null_settings}"
        if not main_settings.exists():
            return False, f"Main settings not found: {main_settings}"
        
        # Check driver_null settings
        driver_data = _load_json(driver_null_settings)
        driver_null_enabled = driver_data.get("driver_null", {}).get("enable", False)
        
        # Check main SteamVR settings
        main_data = _load_json(main_settings)
        steamvr_config = main_data.get("steamvr", {})
        require_hmd = steamvr_config.get("requireHmd", True)
        forced_driver = steamvr_config.get("forcedDriver", "")
        multiple_drivers = steamvr_config.get("activateMultipleDrivers", False)
        
        issues = []
        if not driver_null_enabled:
            issues.append("driver_null is not enabled")
        if require_hmd:
            issues.append("requireHmd is set to true (should be false)")
        if forced_driver != "null":
            issues.append(f"forcedDriver is '{forced_driver}' (should be 'null')")
        if not multiple_drivers:
            issues.append("activateMultipleDrivers is not enabled")
        
        if issues:
            return False, "SteamVR not configured properly:\n  - " + "\n  - ".join(issues)
        
        return True, "SteamVR is configured correctly for trackers without HMD"
        
    except Exception as e:
        return False, f"Error checking SteamVR settings: {e}"


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _infer_steam_root(user_provided: Optional[str]) -> Path:
    if user_provided:
        p = Path(user_provided).expanduser()
        if not p.exists():
            raise FileNotFoundError(p)
        return p

    system = platform.system().lower()

    if "windows" in system:
        candidates = [
            Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Steam",
            Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Steam",
        ]
    elif "darwin" in system:
        candidates = [Path("~/Library/Application Support/Steam").expanduser()]
    else:
        candidates = [
            Path("~/.steam/steam").expanduser(),
            Path("~/.local/share/Steam").expanduser(),
        ]

    for c in candidates:
        if (c / "steamapps").exists():
            return c

    raise FileNotFoundError(
        "Could not auto-detect Steam install. "
        "Pass steam_root explicitly."
    )


def _stop_steam_and_steamvr(*, dry_run: bool) -> None:
    process_names = [
        "vrserver", "vrmonitor", "vrcompositor",
        "steam", "steamwebhelper",
    ]

    if dry_run:
        print("[dry_run] Would terminate Steam / SteamVR processes")
        return

    if platform.system().lower().startswith("win"):
        for p in [
            "vrserver.exe",
            "vrmonitor.exe",
            "vrcompositor.exe",
            "steam.exe",
            "steamwebhelper.exe",
        ]:
            subprocess.run(["taskkill", "/F", "/IM", p], capture_output=True)
    else:
        for p in process_names:
            subprocess.run(["pkill", "-f", p], capture_output=True)


def _backup_file(path: Path, *, dry_run: bool) -> Path:
    backup = Path(str(path) + "_BACKUP")
    if backup.exists():
        return backup

    if dry_run:
        print(f"[dry_run] Would create backup: {backup}")
        return backup

    shutil.copy2(path, backup)
    return backup


def _load_json(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace").lstrip("\ufeff")
    return json.loads(text)


def _write_json(path: Path, data: dict, *, dry_run: bool) -> None:
    if dry_run:
        print(f"[dry_run] Would write: {path}")
        return
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _edit_driver_null_settings(path: Path, *, dry_run: bool) -> None:
    data = _load_json(path)
    data.setdefault("driver_null", {})["enable"] = True
    _write_json(path, data, dry_run=dry_run)


def _edit_main_steamvr_settings(path: Path, *, dry_run: bool) -> None:
    data = _load_json(path)
    steamvr = data.setdefault("steamvr", {})
    steamvr["requireHmd"] = False
    steamvr["forcedDriver"] = "null"
    steamvr["activateMultipleDrivers"] = True
    _write_json(path, data, dry_run=dry_run)