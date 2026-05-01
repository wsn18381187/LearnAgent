# Note: this function is developed by LearnAgent itself.

import os

ALLOWED_EXTENSIONS = {
    ".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".hpp", ".rs", ".go",
    ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".xml", ".csv",
    ".html", ".css", ".sh", ".bash", ".zsh", ".sql", ".r", ".rb", ".swift",
    ".kt", ".scala", ".lua", ".vim", ".cfg", ".ini", ".conf", ".env",
    ".gitignore", ".dockerignore", ".Makefile", ".log",
}


def read_file(file_path: str) -> str:
    """Read content from a file. Supports code and markup formats."""
    # Resolve to absolute path and normalize
    abs_path = os.path.abspath(os.path.expanduser(file_path))

    # Check if path exists
    if not os.path.exists(abs_path):
        return f"Error: File not found: {abs_path}"

    # Check if it's a file (not a directory)
    if not os.path.isfile(abs_path):
        return f"Error: Path is not a file: {abs_path}"

    # Check file extension
    _, ext = os.path.splitext(abs_path)
    basename = os.path.basename(abs_path)
    if ext.lower() not in ALLOWED_EXTENSIONS and basename not in ALLOWED_EXTENSIONS:
        return f"Error: Unsupported file type: {ext or basename}"

    # Check file size (max 1MB)
    try:
        size = os.path.getsize(abs_path)
        if size > 1 * 1024 * 1024:
            return f"Error: File too large ({size} bytes). Max 1MB allowed."
    except OSError as e:
        return f"Error: Cannot access file: {e}"

    # Read and return content
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except UnicodeDecodeError:
        return "Error: File is not a valid UTF-8 text file."
    except OSError as e:
        return f"Error: Cannot read file: {e}"


READ_FILE_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read content from a file. Supports code and markup formats (e.g., .py, .js, .md, .txt, .json). Provide a relative or absolute file path.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Relative or absolute path to the file to read."
                }
            },
            "required": ["file_path"],
        },
    },
}
