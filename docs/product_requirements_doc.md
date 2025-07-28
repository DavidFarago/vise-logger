# Vise Logger - Product Requirements Document

## Overview

Vise Coding is any form of AI-assisted coding with a structured process, where logs store the performed steps. Vise Coding is typically conducted in various AI-Coding IDEs (Cline or Roo or Kilo, all on top of VS Code, Cursor, Claude Code, Windsurf, etc.).

Vise Logger is an MCP server that captures, rates, and archives these Vise Coding sessions from various IDEs via an MCP server, storing them on www.viselo.gr for future reference, comparisons, and searchability.

## Architecture

### System Components

```
[IDE] ←MCP→ [Local MCP Server] ←HTTPS→ [Firebase Backend] ←→ [Web Frontend]
```
The local MCP server filters data.
The firebase backend will be reachable at the URL www.viselo.gr

## 1. MCP Server Specification

### Core Functionality

- **Single tool**: `send_session(stars: float between 1.0 and 5.0, comment: str = None)`
- **No resources or prompts** - minimal MCP implementation
- **Runs locally** on user's machine as privacy gateway
- **Distributed:  via uv or uvx**: uvx -y vise-logger`

### Session Identification Method

Upon calling `send_session(stars: float, comment: str = None)`,  the vise-logger MCP server immediately responds with the progress state tracking response (e.g. `ctx.report_progress()` or alternatively via elicitation) "Rated session at {timestamp}: {stars} stars. Storing session asynchronously on server." , where `{timestamp}` has the format `yyyy-MM-dd-hh-mm-ss`. 

This response ends up in the current log, so the current log can be identified through the following marker:
```python
# Unique session identification using timestamp + stars marker
marker = f"Rated session at {timestamp}: {stars} stars. Now uploading session to server."
# This marker is written to the log and used to find the correct session file
```
If no file with that marker can be found in the log directory, the whole hard drive is searched for the marker. If no file on the whole hard drive can be found, the final progress state tracking response of the tool call will be an according error message. 

If `send_session()` is called multiple times in one AI coding session, there will still only be one log stored on the server. If there are multiple ratings for the same AI coding session, the average rating is taken to rate the overall AI coding session. However, the multiple ratings and their locations are kept as indication of which part of the AI coding session went how well.

The `server-session-ID` of the session on the server is `{timestamp}-{codingtool}`, where
* `{timestamp}` is the one from the first occurrence of "Rated session at {timestamp}: {stars} stars. Storing session asynchronously on server." in the AI coding session log
* `{codingtool}` is the corresponding tool, like `cline`, `roo`, `copilot`, `cursor`, or ... 
Example: `2025-07-26-19-55-16-roo`.

Once the vise-logger MCP successfuly uploaded the identified AI coding session and got a success message back from the server, the vise-logger MCP tool call returns the final progress state tracking response "Session {server-session-ID} successfully uploaded to server.". In case the upload did not success, even after retries, a final progress state tracking response about the error is returned by the tool call.

### Privacy Filtering (Default: auto_replace)

python

```python
# Regex patterns for sensitive data detection
patterns = {
    'openai_api_key': r'sk-[a-zA-Z0-9]{48}',
    'anthropic_api_key': r'sk-ant-[a-zA-Z0-9-]{40,}',
    'github_token': r'ghp_[a-zA-Z0-9]{36}',
    'aws_key': r'AKIA[0-9A-Z]{16}',
    'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    # ... more patterns
}

# Replacement format: [TYPE_NanoID]
# Example: "sk-abc123" → "[OPENAI_KEY_8xK9mP2q]"
```

### Log File Access

The MCP server reads IDE logs to extract:
- Full conversation history
- Token usage (input/output)
- Tool call information
- Timestamps and duration

Log directory:
- **Claude Code**: `~/.claude/projects/*/transcripts/*.jsonl`
- **Cursor**: `%APPDATA%\Cursor\User\workspaceStorage\*/state.vscdb`
- **Cline**: ~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/tasks/
- **Roo Code**: ~/.config/Code/User/globalStorage/rooveterinaryinc.roo-cline/tasks
- **Continue.dev**: `~/.continue/logs/core.log`
- **Windsurf**: Export via UI functionality
- **GitHub Copilot**: `AppData\Roaming\Code\logs\...\GitHub Copilot.log`

### Configuration

MCP servers are configured per IDE:

- **Cursor**: `~/.cursor/mcp.json`
- **Claude Code**: `.claude/config.yaml`
- **Cline**: `cline_mcp_settings.json`

Privacy settings configurable via:

json

```json
{
  "privacy_mode": "auto_replace",  // Options: strict, auto_replace, warn_only, disabled
  "filter_types": ["api_keys", "emails", "credit_cards"]
}
```

### Auto-installation of Rules

The installer creates rule files to prompt session saving:

**Cursor** (`.cursor/rules/ai-session-tracking.mdc`):

markdown

```markdown
---
name: session-tracking
---
At the end of each coding session, offer to rate and save the session.
When calling send_session, include the rating and let the tool find the correct log file.
```

**Cline/Roo** (integration with `<attempt_completion>`):

markdown

```markdown
In your <attempt_completion> results, always append:
"📊 Would you like to rate and save this coding session? (1-5 stars)"
```

## 2. Backend API Specification (Firebase)

### Technology Stack

- **API**: Cloud Functions (Python) - upgrade to Cloud Run at scale
- **Database**: Firestore for metadata
- **Storage**: Cloud Storage for session data (compressed)
- **Auth**: Firebase Auth with GitHub OAuth
- **Hosting**: Firebase Hosting

### API Endpoints

```
POST   /api/v1/sessions     # Upload new session
GET    /api/v1/sessions     # List user's sessions
GET    /api/v1/sessions/{id} # Get specific session
```

### Data Model

javascript

```javascript
// Firestore: sessions collection
{
  "id": "session_abc123",
  "user_id": "github_12345",
  "created_at": "2024-01-15T10:30:00Z",
  "tool": "cursor",
  "storage_url": "gs://sessions/abc123.json.gz",
  
  // Multiple ratings support
  "ratings": [
    {
      "stars": 4.5,
      "timestamp": "2024-01-15T10:30:00Z",
      "line_number": 1247, // Exact position in log, where timestamp is mentioned
      "comment": "Great refactoring help"
    },
    {
      "stars": 3.0,
      "timestamp": "2024-01-15T11:00:00Z",
      "location": "85%",
      "comment": "Struggled with the API integration"
    }
  ],
  "average_rating": 3.75,
  
  // Metadata from logs
  "metadata": {
    "total_tokens": 15420,
    "input_tokens": 12000,
    "output_tokens": 3420,
    "tool_calls": 5,
    "duration_minutes": 45,
    "model": "claude-3-sonnet"
  },
  
  // Privacy report
  "privacy_filtered": true,
  "replacements_count": 3
}

// Cloud Storage: compressed session data
// Path: sessions/{session_id}.json.gz
// Contains: filtered conversation history
```

### Authentication

1. **GitHub OAuth** for web users
2. **API Keys** for MCP server authentication
3. API key generation on first login, shown once

### Cost Optimization

- **Compression**: GZIP all sessions (500KB → 50KB)
- **Storage**: Use Cloud Storage ($0.02/GB) not Firestore ($0.18/GB)
- **Estimated costs** for 100 users: ~$0.53/month

## 3. Frontend Website Specification

### MVP Features

- **Login** with GitHub OAuth
- **Dashboard** showing user's sessions list
- **Session viewer** with syntax highlighting
- **API key management** (generate, view once, revoke)
- **Basic filtering** by date, rating, tool

### Future Features (Not in MVP)

- Full-text search across sessions
- Rating visualization over time
- Export capabilities (markdown, JSON)
- Public session sharing with privacy controls

### Technology Stack

- **Framework**: Next.js with TypeScript
- **Styling**: Tailwind CSS
- **Hosting**: Firebase Hosting (free tier)
- **Auth**: NextAuth.js with GitHub provider

## 4. Implementation Priority

### Phase 1: MCP Server (Week 1)

1. Basic tool implementation with file reading
2. Session identification via rating marker
3. Privacy filtering with regex: include the option so users see what is planned, but stick with `disabled` for Phase 1.
4. Package setup and distribution

### Phase 2: Backend API (Week 2)

1. Firebase project setup
2. Cloud Functions for API endpoints
3. GitHub OAuth integration
4. API key generation system

### Phase 3: Frontend MVP (Week 3)

1. Login flow with GitHub
2. Basic dashboard
3. Session viewer
4. API key management

### Phase 4: Auto-installation (Week 4)

1. Rule file generation for each IDE
2. Installation script (including grabbing API key from frontend to set it in mCP server to enable the API calls, see Authentication above)
3. Documentation

## 5. Security & Privacy

### Data Flow For Later Phases for other "privacy_mode"s than "disabled"

1. Raw session data never leaves user's machine unfiltered
2. MCP server applies privacy filtering locally: each private data is replaced by its hash, for anonymization
3. Only anonymized data sent to API
4. Replacements mapping (hash -> original private data for each anonymized private data) is stored locally in $VISE_LOGGER_CONFIG_PATH/deanonymize.csv.

### License

- **MIT License** for maximum adoption

## 6. Scaling Considerations

At 10,000 users:

- Upgrade Cloud Functions to Cloud Run
- Add Redis caching layer
- Multi-region deployment
- Estimated cost: ~$250/month

## 7. Success Metrics

- Number of active users
- Sessions uploaded per day
- (Average session rating)
- (Percentage of sessions with filtered content)
