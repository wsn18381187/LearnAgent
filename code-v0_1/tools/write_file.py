# Note: this function is developed by LearnAgent itself.

import os

ALLOWED_EXTENSIONS = {
    ".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".hpp", ".rs", ".go",
    ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".xml", ".csv",
    ".html", ".css", ".sh", ".bash", ".zsh", ".sql", ".r", ".rb", ".swift",
    ".kt", ".scala", ".lua", ".vim", ".cfg", ".ini", ".conf", ".env",
    ".gitignore", ".dockerignore", ".Makefile", ".log",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def write_file(file_path: str, content: str) -> str:
    """Write content to a file. Creates parent directories if needed."""
    # Resolve to absolute path and normalize
    abs_path = os.path.abspath(os.path.expanduser(file_path))

    # Check file extension
    _, ext = os.path.splitext(abs_path)
    basename = os.path.basename(abs_path)
    if ext.lower() not in ALLOWED_EXTENSIONS and basename not in ALLOWED_EXTENSIONS:
        return f"Error: Unsupported file type: {ext or basename}"

    # Check content size
    content_bytes = content.encode("utf-8")
    if len(content_bytes) > MAX_FILE_SIZE:
        return f"Error: Content too large ({len(content_bytes)} bytes). Max 10MB allowed."

    # Create parent directories if they don't exist
    parent_dir = os.path.dirname(abs_path)
    if parent_dir and not os.path.exists(parent_dir):
        try:
            os.makedirs(parent_dir, exist_ok=True)
        except OSError as e:
            return f"Error: Cannot create directory {parent_dir}: {e}"

    # Write content to file
    try:
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Success: File written to {abs_path} ({len(content_bytes)} bytes)"
    except OSError as e:
        return f"Error: Cannot write file: {e}"

# Not used any more
WRITE_FILE_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": (
            "Request to write a file. The system will use CodeAct mode to generate and execute "
            "Python code to write the file, avoiding JSON escaping issues. "
            "Provide the file path and a description of what content to write. "
            "Supports code and markup formats (e.g., .py, .js, .md, .txt, .json, .html, .css)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Relative or absolute path to the file to write."
                },
                "description": {
                    "type": "string",
                    "description": "A detailed description of what content should be written to the file. Include all specifics: structure, styling, text content, etc."
                }
            },
            "required": ["file_path", "description"],
        },
    },
}
