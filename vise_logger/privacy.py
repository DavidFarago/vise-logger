from typing import Dict

# Regex patterns for sensitive data detection
PATTERNS: Dict[str, str] = {
    "openai_api_key": r"sk-[a-zA-Z0-9]{48}",
    "anthropic_api_key": r"sk-ant-[a-zA-Z0-9-]{40,}",
    "github_token": r"ghp_[a-zA-Z0-9]{36}",
    "aws_key": r"AKIA[0-9A-Z]{16}",
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    # TODO: add more patterns, see my TOSEM review
}


def filter_content(content: str, privacy_mode: str = "disabled") -> str:
    """
    Filters sensitive information from the content based on the privacy mode.
    For Phase 1, this is disabled by default.
    """
    if privacy_mode == "disabled":
        return content

    # In future phases, this function will implement the replacement logic.
    # For now, it just returns the original content.
    return content
