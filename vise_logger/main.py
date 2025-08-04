import asyncio
import json
import logging
import tempfile
import zipfile
from datetime import datetime

import requests
from mcp.server.fastmcp import FastMCP

from .privacy import filter_content
from .search import find_log_file_with_marker

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Remove existing handlers to avoid duplicates
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# Add file handler
file_handler = logging.FileHandler("/home/emergency/git/vise-logger/mcp_server.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)

mcp = FastMCP("vise-logger")


async def _configure_log_dir_background(marker: str, timestamp: str):
    """Background task for configure_log_dir."""
    logging.info("--- STARTING BACKGROUND LOG DIRECTORY CONFIGURATION ---")

    find_result = await asyncio.to_thread(find_log_file_with_marker, marker)

    if find_result:
        log_file_path, _ = find_result
        result_message = f"Log directory found and verified: {log_file_path.parent}"
    else:
        result_message = "Could not find a verifiable log directory."
    logging.info(result_message)


@mcp.tool()
async def configure_log_dir() -> str:
    """
    Finds and verifies the log directory for the coding tool.
    This is a long-running operation and may take minutes to hours.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    marker = f"Starting at {timestamp} to search for the vise coding tool's log directory. This will be a long-running background task, result will be stored in `locations.json`."

    asyncio.create_task(_configure_log_dir_background(marker, timestamp))
    return marker


async def _send_session_background(
    marker: str, timestamp: str, stars: float, comment: str
):
    """Background task for send_session."""
    logging.info("--- STARTING BACKGROUND SESSION UPLOAD ---")

    find_result = await asyncio.to_thread(find_log_file_with_marker, marker)

    if not find_result:
        error_message = "Could not find the log file with the session marker."
        logging.error(error_message)
        return

    log_file_path, coding_tool = find_result

    try:
        with open(log_file_path, "r", encoding="utf-8", errors="ignore") as f:
            log_content = f.read()
    except IOError as e:
        error_message = f"Error reading log file: {e}"
        logging.error(error_message)
        return

    filtered_content = filter_content(log_content)
    server_session_id = f"{timestamp}-{coding_tool}"

    try:
        # Create a temporary file that is automatically deleted
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=True) as temp_zip:
            # Create the zip archive using the temporary file's path
            with zipfile.ZipFile(
                temp_zip.name, "w", zipfile.ZIP_DEFLATED
            ) as zip_archive:
                zip_archive.writestr(log_file_path.name, filtered_content)

            metadata = {
                "marker": marker,
                "tool": coding_tool,
                "stars": stars,
                "comment": comment,
            }

            # The tempfile is opened by default, but we need to re-open it for reading in binary mode
            # after zipfile has written to it.
            with open(temp_zip.name, "rb") as file_to_upload:
                files = {
                    "file": ("session.zip", file_to_upload, "application/zip"),
                    "metadata": (None, json.dumps(metadata), "application/json"),
                }

                response = requests.post(
                    "https://studio--viselog.us-central1.hosted.app/api/v1/sessions",
                    files=files,
                    timeout=30,
                )
                response.raise_for_status()

            success_message = (
                f"Session {server_session_id} successfully uploaded to server."
            )
            logging.info(success_message)
            logging.info(f"Temporary file {temp_zip.name} removed.")

    except (IOError, requests.exceptions.RequestException, zipfile.BadZipFile) as e:
        error_message = f"Failed to create or upload session zip file: {e}"
        logging.error(error_message)


@mcp.tool()
async def send_session(stars: float, comment: str) -> str:
    """
    Rates and archives the current Vise Coding session.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    marker = f"Rated session at {timestamp}: {stars} stars. Uploading session in the background."
    asyncio.create_task(_send_session_background(marker, timestamp, stars, comment))
    return marker


def main():
    """Synchronous entry point."""
    mcp.run()


if __name__ == "__main__":
    main()
