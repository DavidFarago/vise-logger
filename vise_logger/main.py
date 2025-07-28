import asyncio
import logging
from datetime import datetime

from mcp.server.fastmcp import Context, FastMCP

from .privacy import filter_content
from .search import find_log_file_with_marker

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

mcp = FastMCP("vise-logger")


@mcp.tool()
async def configure_log_dir(ctx: Context) -> str:
    """
    Finds and verifies the log directory for the coding tool.
    This is a long-running operation and may take minutes to hours.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    marker = f"Starting at {timestamp} to search for the vise coding tool's log directory. This is a long-running operation and may take minutes to hours. The result will be stored in `locations.json`."
    await ctx.report_progress(progress=0, total=1, message=marker)

    find_result = await asyncio.to_thread(find_log_file_with_marker, marker)

    if find_result:
        log_file_path, _ = find_result
        result_message = f"Log directory found and verified: {log_file_path.parent}"
    else:
        result_message = "Could not find a verifiable log directory."

    await ctx.report_progress(progress=1, total=1, message=result_message)
    return result_message


@mcp.tool()
async def send_session(stars: float, comment: str, ctx: Context) -> str:
    """
    Rates and archives the current Vise Coding session.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    marker = (
        f"Rated session at {timestamp}: {stars} stars. Now uploading session to server."
    )

    logging.info("send_session called with stars=%s, comment='%s'", stars, comment)
    await ctx.report_progress(
        progress=0,
        total=1,
        message=f"Rated session at {timestamp}: {stars} stars. Storing session asynchronously on server.",
    )

    find_result = await asyncio.to_thread(find_log_file_with_marker, marker)

    if not find_result:
        error_message = "Could not find the log file with the session marker."
        logging.error(error_message)
        await ctx.report_progress(progress=1, total=1, message=error_message)
        return error_message

    log_file_path, coding_tool = find_result

    try:
        with open(log_file_path, "r", encoding="utf-8", errors="ignore") as f:
            log_content = f.read()
    except IOError as e:
        error_message = f"Error reading log file: {e}"
        logging.error(error_message)
        await ctx.report_progress(progress=1, total=1, message=error_message)
        return error_message

    filtered_content = filter_content(log_content)

    server_session_id = f"{timestamp}-{coding_tool}"

    # Simulate Firebase upload
    logging.info("--- SIMULATING FIREBASE UPLOAD ---")
    logging.info("Server Session ID: %s", server_session_id)
    logging.info("Stars: %s", stars)
    logging.info("Comment: %s", comment)
    logging.info("Log content length: %d", len(filtered_content))
    logging.info("--- END OF SIMULATION ---")

    success_message = (
        f"Session {server_session_id} successfully uploaded to server."
    )
    logging.info(success_message)
    await ctx.report_progress(progress=1, total=1, message=success_message)
    return success_message


def main():
    """Synchronous entry point."""
    mcp.run()


if __name__ == "__main__":
    main()
