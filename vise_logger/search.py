import json
import logging
import os
import platform
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

MB = 1024 * 1024
MAX_FILE_SIZE = 10 * MB
MAX_DIR_SIZE = 50 * MB
MAX_SUFFIXES = 4

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

LOCATIONS_FILE = Path(__file__).parent / "locations.json"


def _read_locations() -> List[Dict[str, Any]]:
    """Reads log locations from the JSON file."""
    if not LOCATIONS_FILE.exists():
        return []
    with open(LOCATIONS_FILE, "r") as f:
        data: Dict[str, Any] = json.load(f)
        return data.get("locations", [])


def _detect_log_directory(found_path: Path) -> Path:
    """
    Detects the log path (found_path or it's directory) based on some criteria:
    1. if the directory contains only one file, return that file
    2. the size of the directory
    3. the number of files with the same suffix in the directory
    """
    directory = found_path.parent

    # sole file criterion
    if len(list(directory.iterdir())) == 1:
        assert(found_path.is_file()), "Expected found_path to be a file"
        logging.debug("Picking log file as it is the only file in the directory.")
        return found_path

    # directory size criterion
    try:
        size = sum(f.stat().st_size for f in directory.glob("**/*") if f.is_file())
        if size > MAX_DIR_SIZE:
            logging.debug(
                "Picking log file and not log dir as dir size exceeds limit: %s", size
            )
            return found_path
    except (IOError, OSError, FileNotFoundError):
        pass

    # suffix amount criterion
    suffix = found_path.suffix
    if suffix:
        try:
            files_with_same_suffix = [
                f for f in directory.iterdir() if f.suffix == suffix
            ]
            if len(files_with_same_suffix) > MAX_SUFFIXES:
                logging.debug(
                    "Picking log file and not log dir as too many files with the same suffix: %s",
                    len(files_with_same_suffix),
                )
                return found_path
        except (IOError, OSError, FileNotFoundError):
            pass
    return directory


def _add_location(found_path: Path, tool: str = "unknown") -> None:
    """Adds a new location with verified:true"""
    dir_of_all_logs = found_path.parent
    locations = _read_locations()
    locations.append({"dir": str(dir_of_all_logs), "tool": tool, "verified": True})
    with open(LOCATIONS_FILE, "w") as f:
        json.dump({"locations": locations}, f, indent=2)
    logging.info("Updated/Added and verified log location: %s", dir_of_all_logs)


def _expand_path(path_str: str) -> Path:
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


def _search_path(directory: Path, marker: str) -> Optional[Tuple[Path, Path]]:
    """Recursively searches a directory for a file containing the marker.
       Returns the file path and what path to zip (the file or its directory) if found, otherwise None."""
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
                            return file_path, _detect_log_directory(file_path)
            except (IOError, OSError, FileNotFoundError):
                continue
    return None


def find_log_path_with_marker(marker: str) -> Optional[Tuple[Path, Path, str]]:
    """
    Finds the log file containing the unique marker by searching in a prioritized order,
    or the directory where the log file is located in case that whole directory represents the log/session.

    returns:
        A tuple of the found log file path, the path to zip, and the tool name; or None if not found
    """
    logging.info("Searching for log file with marker: %s", marker)

    locations = _read_locations()
    verified_locations = [loc for loc in locations if loc.get("verified")]
    unverified_locations = [loc for loc in locations if not loc.get("verified")]

    # Stage 1: Search in verified predefined locations
    logging.info("Stage 1: Searching in verified predefined locations.")
    for loc in verified_locations:
        expanded_path = _expand_path(loc.get("dir", ""))
        if expanded_path.exists() and expanded_path.is_dir():
            found_path = _search_path(expanded_path, marker)
            if found_path:
                return *found_path, loc.get("tool", "unknown")

    # Stage 2: Search in unverified predefined locations
    logging.info("Stage 2: Searching in unverified predefined locations.")
    for loc in unverified_locations:
        expanded_path = _expand_path(loc.get("dir", ""))
        if expanded_path.exists() and expanded_path.is_dir():
            found_path = _search_path(expanded_path, marker)
            if found_path:
                loc["verified"] = True
                return *found_path, loc.get("tool", "unknown")

    # Stage 3: Search in home directory
    logging.info("Stage 3: Searching in home directory.")
    home_dir = Path.home()
    found_path = _search_path(home_dir, marker)
    if found_path:
        _add_location(found_path[1])
        return *found_path, "unknown"

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
                found_path = _search_path(root_path, marker)
                if found_path:
                    _add_location(found_path[1])
                    return *found_path, "unknown"
            except PermissionError:
                continue

    logging.error("Log file with marker not found.")
    return None
