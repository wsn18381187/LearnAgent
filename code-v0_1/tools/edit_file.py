"""
edit_file tool - Precise old_str → new_str replacement mechanism (Claude Code style).

Core logic:
1. Read the entire content of the target file.
2. Find old_str in the file (must match exactly once).
3. Replace with new_str.
4. Return the replacement result (success/failure reason).

Key design decisions:
- old_str must match uniquely, otherwise error (prevents accidental modifications).
- Supports multi-line replacement (naturally handles long content).
- Returns detailed success/failure information to help the LLM correct itself.
- File extension whitelist consistent with write_file.
- Uses CodeAct mode to avoid JSON escaping issues.
"""

import os
from pathlib import Path

# File extension whitelist (consistent with write_file)
ALLOWED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".scss", ".less",
    ".json", ".yaml", ".yml", ".toml", ".xml", ".md", ".txt", ".csv",
    ".sh", ".bash", ".zsh", ".fish", ".ps1", ".bat", ".cmd",
    ".java", ".kt", ".kts", ".swift", ".c", ".h", ".cpp", ".hpp", ".cc", ".hh",
    ".rs", ".go", ".rb", ".php", ".lua", ".r", ".m", ".mm",
    ".sql", ".graphql", ".proto", ".env", ".cfg", ".ini", ".conf",
    ".dockerfile", ".makefile", ".cmake", ".gradle",
    ".vue", ".svelte", ".astro", ".tf", ".tfvars",
    ".ipynb", ".tex", ".rst", ".org",
}


def _get_file_extension(file_path: str) -> str:
    """Extract the file extension, handling special cases like Dockerfile."""
    filename = os.path.basename(file_path)
    # Handle files without extensions but with known names
    special_names = {
        "dockerfile": ".dockerfile",
        "makefile": ".makefile",
        "gemfile": ".gemfile",
        "rakefile": ".rakefile",
        "procfile": ".procfile",
    }
    lower_name = filename.lower()
    if lower_name in special_names:
        return special_names[lower_name]
    return Path(file_path).suffix.lower()


def _validate_file_path(file_path: str) -> str | None:
    """Validate the file path. Returns error message or None if valid."""
    if not file_path or not isinstance(file_path, str):
        return "Error: file_path must be a non-empty string."

    ext = _get_file_extension(file_path)
    if not ext:
        return (
            f"Error: File '{file_path}' has no extension. "
            f"Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    if ext not in ALLOWED_EXTENSIONS:
        return (
            f"Error: File extension '{ext}' is not allowed. "
            f"Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    return None


def _find_unique_occurrence(content: str, old_str: str) -> tuple[int, int] | str:
    """
    Find the unique occurrence of old_str in content.
    Returns (start_index, end_index) if exactly one match is found.
    Returns an error string if zero or multiple matches are found.
    """
    if not old_str:
        return "Error: old_str must not be empty."

    occurrences = []
    start = 0
    while True:
        idx = content.find(old_str, start)
        if idx == -1:
            break
        occurrences.append((idx, idx + len(old_str)))
        start = idx + 1

    if len(occurrences) == 0:
        # Provide helpful context for debugging
        # Show first and last few lines of old_str
        old_lines = old_str.split("\n")
        preview = old_str[:200]
        if len(old_str) > 200:
            preview += "..."
        return (
            f"Error: old_str not found in file.\n"
            f"Searched for ({len(old_str)} chars, {len(old_lines)} lines):\n"
            f"---\n{preview}\n---\n"
            f"Please verify the content matches exactly (including whitespace and indentation)."
        )

    if len(occurrences) > 1:
        lines_info = []
        content_before = content
        for i, (s, e) in enumerate(occurrences):
            # Find line number
            line_num = content_before[:s].count("\n") + 1
            # Get surrounding context
            context_start = max(0, s - 40)
            context_end = min(len(content), e + 40)
            context = content[context_start:context_end].replace("\n", "\\n")
            lines_info.append(f"  Occurrence {i + 1}: line ~{line_num}, context: ...{context}...")

        return (
            f"Error: old_str matches {len(occurrences)} locations in the file. "
            f"Must match exactly one location.\n"
            f"Matches found:\n" + "\n".join(lines_info) + "\n\n"
            f"Please provide more surrounding context to make the match unique."
        )

    return occurrences[0]


def edit_file(
    file_path: str,
    old_str: str,
    new_str: str,
    description: str = "",
) -> str:
    """
    Replace old_str with new_str in the specified file.

    Args:
        file_path: Path to the target file.
        old_str: The exact text to replace (must match exactly once).
        new_str: The new text to insert in place of old_str.
        description: Brief description of the modification intent.

    Returns:
        A success/error message string.
    """
    # Validate file path
    error = _validate_file_path(file_path)
    if error:
        return error

    # Check if file exists
    if not os.path.exists(file_path):
        return f"Error: File '{file_path}' does not exist."

    if not os.path.isfile(file_path):
        return f"Error: '{file_path}' is not a file."

    # Read file content
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        return (
            f"Error: Cannot read '{file_path}' as UTF-8 text. "
            f"Binary files are not supported by edit_file."
        )
    except Exception as e:
        return f"Error reading file '{file_path}': {e}"

    # Find the unique occurrence of old_str
    result = _find_unique_occurrence(content, old_str)
    if isinstance(result, str):
        return result  # Error message

    start_idx, end_idx = result

    # Perform the replacement
    new_content = content[:start_idx] + new_str + content[end_idx:]

    # Write back to file
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
    except Exception as e:
        return f"Error writing to file '{file_path}': {e}"

    # Build success message
    old_lines = old_str.count("\n") + 1
    new_lines = new_str.count("\n") + 1
    line_num = content[:start_idx].count("\n") + 1

    msg_parts = [f"✓ Successfully edited '{file_path}'"]
    if description:
        msg_parts.append(f"  Description: {description}")
    msg_parts.append(f"  Location: line ~{line_num}")
    msg_parts.append(f"  Replaced: {old_lines} line(s) → {new_lines} line(s)")
    msg_parts.append(f"  Characters: {len(old_str)} → {len(new_str)}")

    return "\n".join(msg_parts)


# Tool definition for CodeAct agent registration
EDIT_FILE_TOOL_DEFINITION = {
    "name": "edit_file",
    "description": (
        "Precisely replace a text fragment in a file using old_str → new_str matching. "
        "The old_str must match exactly one location in the file (including whitespace "
        "and indentation). If zero or multiple matches are found, the operation fails "
        "with detailed error information to help you correct the match. "
        "Supports multi-line replacements naturally."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the target file to edit."
            },
            "old_str": {
                "type": "string",
                "description": (
                    "The exact text fragment to replace. Must match the file content "
                    "exactly, including all whitespace, indentation, and newlines. "
                    "Must be unique within the file."
                )
            },
            "new_str": {
                "type": "string",
                "description": "The new text to insert in place of old_str."
            },
            "description": {
                "type": "string",
                "description": "Brief description of the modification intent (helps with understanding the purpose)."
            }
        },
        "required": ["file_path", "old_str", "new_str"]
    }
}
