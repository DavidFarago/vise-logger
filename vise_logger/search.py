import json
import logging
import os
import platform
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

LOCATIONS_FILE = Path(__file__).parent / "locations.json"


def read_locations() -> List[Dict[str, Any]]:
    """Reads log locations from the JSON file."""
    if not LOCATIONS_FILE.exists():
        return []
    with open(LOCATIONS_FILE, "r") as f:
        data: Dict[str, Any] = json.load(f)
        return data.get("locations", [])


def detect_log_directory(found_path: Path) -> Path:
    """
    Detects the log directory based on some criterion (the number of files with the same suffix)
    """
    directory = found_path.parent
    suffix = found_path.suffix
    if suffix:
        try:
            files_with_same_suffix = [
                f for f in directory.iterdir() if f.suffix == suffix
            ]
            if len(files_with_same_suffix) > 3:
                return found_path
        except (IOError, OSError, FileNotFoundError):
            pass  # Ignore errors if we can't list the directory
    return directory


def update_or_add_location(found_path: Path, tool: str = "unknown") -> Path:
    """Adds a new location with verified:true or updates an existing one."""
    original_dir = found_path.parent
    log_dir = detect_log_directory(found_path)

    locations = read_locations()
    found = False
    for loc in locations:
        if loc.get("dir") in [str(log_dir), str(original_dir)]:
            loc["verified"] = True
            log_dir = Path(loc.get("dir"))
            found = True
            break
    if not found:
        locations.append({"dir": str(log_dir), "tool": tool, "verified": True})

    with open(LOCATIONS_FILE, "w") as f:
        json.dump({"locations": locations}, f, indent=2)
    logging.info("Updated/Added and verified log location: %s", log_dir)
    return log_dir


def expand_path(path_str: str) -> Path:
    """Expands environment variables and home directory tilde in a path string."""
    path_str = os.path.expanduser(path_str)

    if "%APPDATA%" in path_str:
        appdata = None
        if platform.system() == "Windows":
            appdata = os.getenv("APPDATA")
        elif platform.system() == "Linux":
            appdata = os.getenv("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        elif platform.system() == "Darwin":
            appdata = str(Path.home() / "Library/Application Support")

        if appdata:
            path_str = path_str.replace("%APPDATA%", appdata)
        else:
            return Path(f"/non_existent_path_{os.urandom(8).hex()}")

    return Path(os.path.expandvars(path_str))


def search_directory(directory: Path, marker: str) -> Optional[Path]:
    """Recursively searches a directory for a file containing the marker."""
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = Path(root) / file
            try:
                if file_path.stat().st_size > MAX_FILE_SIZE:
                    continue
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if marker in line:
                            logging.info("Marker found in: %s", file_path)
                            return file_path
            except (IOError, OSError, FileNotFoundError):
                continue
    return None


def find_log_file_with_marker(marker: str) -> Optional[Tuple[Path, str]]:
    """
    Finds the log file containing the unique marker by searching in a prioritized order.
    """
    logging.info("Searching for log file with marker: %s", marker)

    locations = read_locations()
    verified_locations = [loc for loc in locations if loc.get("verified")]
    unverified_locations = [loc for loc in locations if not loc.get("verified")]

    # Stage 1: Search in verified predefined locations
    logging.info("Stage 1: Searching in verified predefined locations.")
    for loc in verified_locations:
        expanded_path = expand_path(loc.get("dir", ""))
        if expanded_path.exists() and expanded_path.is_dir():
            found_path = search_directory(expanded_path, marker)
            if found_path:
                return found_path, loc.get("tool", "unknown")

    # Stage 2: Search in unverified predefined locations
    logging.info("Stage 2: Searching in unverified predefined locations.")
    for loc in unverified_locations:
        expanded_path = expand_path(loc.get("dir", ""))
        if expanded_path.exists() and expanded_path.is_dir():
            found_path = search_directory(expanded_path, marker)
            if found_path:
                found_path = update_or_add_location(
                    found_path, loc.get("tool", "unknown")
                )
                return found_path, loc.get("tool", "unknown")

    # Stage 3: Search in home directory
    logging.info("Stage 3: Searching in home directory.")
    home_dir = Path.home()
    found_path = search_directory(home_dir, marker)
    if found_path:
        found_path = update_or_add_location(found_path)
        return found_path, "unknown"

    # Stage 4: Search the rest of the hard drive
    logging.info(
        "Stage 4: Searching the rest of the hard drive. This may take a while."
    )
    drives = [Path("/")]
    if platform.system() == "Windows":
        drives.extend(
            [
                Path(f"{chr(drive)}:\\")
                for drive in range(ord("A"), ord("Z") + 1)
                if Path(f"{chr(drive)}:\\").exists()
            ]
        )

    for drive in drives:
        for root, dirs, _ in os.walk(drive):
            root_path = Path(root)
            if home_dir in root_path.parents or root_path == home_dir:
                dirs[:] = []
                continue

            try:
                found_path = search_directory(root_path, marker)
                if found_path:
                    found_path = update_or_add_location(found_path)
                    return found_path, "unknown"
            except PermissionError:
                continue

    logging.error("Log file with marker not found.")
    return None
