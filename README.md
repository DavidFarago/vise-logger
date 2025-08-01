# Vise Logger

Vise Logger is an MCP server that captures, rates, and archives Vise Coding sessions from various IDEs, storing them for future reference, comparisons, and searchability.

## Installation and Setup

### Local installation

This project uses `uv` for package and environment management.

1.  **Create a virtual environment:**
    ```bash
    uv venv
    ```

2.  **Activate the virtual environment:**
    *   On macOS/Linux:
        ```bash
        source .venv/bin/activate
        ```
    *   On Windows:
        ```bash
        .venv\Scripts\activate
        ```

3.  **Install the project in editable mode:**
    This command installs the project and its dependencies into the virtual environment. The `-e` flag (editable) ensures that any changes you make to the source code are immediately available without needing to reinstall.
    ```bash
    uv pip install -e .
    ```

In Cline and Roo:
```json
    "vise-logger": {
      "disabled": false,
      "timeout": 60,
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/home/emergency/git/vise-logger",
        "run",
        "vise-logger"
      ]
    }
```

### Installation of MCP Server via PyPI


## Running the MCP Server

To run the MCP server directly from the command line:

```bash
vise-logger
```

## MCP Tools

This server provides two tools:

### `send_session(stars: float, comment: str = "")`

Rates and archives the current Vise Coding session. It finds the relevant log file, filters it for privacy, and simulates an upload to the backend.

### `configure_log_dir()`

Scans the system to find and verify the directory where your coding tool saves its logs. This helps speed up future searches.

**Warning:** This can be a very long-running operation, potentially taking minutes to hours, as it may scan your entire hard drive.

## Running Tests

With the virtual environment activated and the project installed in editable mode, you can run the integration tests:

```bash
python3 -m unittest discover tests
```

**Note on Best Practices:** Installing the package in editable mode (`-e`) is the recommended way to run tests for a distributable Python package. It correctly resolves imports without needing to modify `sys.path`, which is a less robust method. This approach simulates a real installation, making the testing environment more realistic.

## REST Endpoints The Sessions Are Sent to

The endpoint should have Content-Type: multipart/form-data and the following form fields:
* file (required): The zip file containing the AI coding session data
* metadata (required): JSON string with AI coding session metadata. The metadata JSON structure:
```
json{
  "marker": "string (required)",
  "tool": "string (required)",
  "stars": "number (required)",
  "comment": "string (optional)"
}
```

The official web application for Vise Logger is www.viselo.gr.
You can test it via
```
curl -X POST \
  -F "file=@session.zip" \
  -F 'metadata={"marker": "Rated session at 2025-07-30-20-56-11: 1.9 stars.", "tool": "curl", "stars": 1.9, "comment": "Just a curl test"}' \
  "https://studio--viselog.us-central1.hosted.app/api/v1/sessions"
```