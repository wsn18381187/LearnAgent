"""
CodeAct Executor for LearnAgent condition flow.

Instead of having the LLM generate JSON function calls (which breaks when
content contains unescaped quotes/newlines), we let the LLM generate Python
code directly. Python's triple-quoted strings naturally handle multi-line
content without any escaping issues.

This module provides a restricted execution environment that:
- Pre-imports tool functions (write_file, read_file, etc.) so the LLM can
  call them directly in Python code.
- Restricts dangerous builtins (__import__, eval, exec, open, etc.).
- Captures stdout and return values.
"""

import sys
import io
import traceback
from tools.read_file import read_file
from tools.terminal_command import execute_terminal_command
from tools.write_file import write_file
from tools.search_web import search_web
from tools.get_current_time import get_current_time

# ---------------------------------------------------------------------------
# Allowed builtins – only safe, commonly needed functions
# ---------------------------------------------------------------------------
ALLOWED_BUILTINS = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "filter": filter,
    "float": float,
    "format": format,
    "frozenset": frozenset,
    "int": int,
    "isinstance": isinstance,
    "issubclass": issubclass,
    "iter": iter,
    "len": len,
    "list": list,
    "map": map,
    "max": max,
    "min": min,
    "next": next,
    "print": print,
    "range": range,
    "reversed": reversed,
    "round": round,
    "set": set,
    "slice": slice,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "type": type,
    "zip": zip,
    "True": True,
    "False": False,
    "None": None,
    "Exception": Exception,
    "ValueError": ValueError,
    "TypeError": TypeError,
    "KeyError": KeyError,
    "IndexError": IndexError,
    "StopIteration": StopIteration,
    "RuntimeError": RuntimeError,
    "OSError": OSError,
    "IOError": IOError,
    "json": __import__("json"),
    "re": __import__("re"),
    "os_path": __import__("os.path"),
    "datetime": __import__("datetime"),
    "math": __import__("math"),
    "time": __import__("time"),
    "pathlib": __import__("pathlib"),
    "textwrap": __import__("textwrap"),
    "itertools": __import__("itertools"),
    "functools": __import__("functools"),
    "collections": __import__("collections"),
    "hashlib": __import__("hashlib"),
    "base64": __import__("base64"),
    "csv": __import__("csv"),
    "urllib_parse": __import__("urllib.parse"),
}

# ---------------------------------------------------------------------------
# Tool functions exposed to the LLM
# ---------------------------------------------------------------------------
TOOL_FUNCTIONS = {
    "read_file": read_file,
    "execute_terminal_command": execute_terminal_command,
    "search_web": search_web,
    "get_current_time": get_current_time,
    "write_file": write_file,
}

# ---------------------------------------------------------------------------
# CodeAct system prompt – injected into the sub-task system prompt
# ---------------------------------------------------------------------------
CODEACT_INSTRUCTION = """
You are a CodeAct agent. Instead of describing what to do, you MUST write 
executable Python code to accomplish the sub-task.

The following functions are pre-imported and ready to use:

  write_file(file_path: str, content: str) -> str
      Write content to a file. Creates parent directories automatically.
      Returns a success/error message.

  read_file(file_path: str) -> str
      Read content from a file. Returns the file content or an error message.

  execute_terminal_command(command: str) -> str
      Execute a shell command. Returns stdout, stderr, and return code.

  search_web(query: str) -> str
      Search the web for up-to-date information.

  get_current_time() -> str
      Get the current date and time.

You may also use the following Python standard library modules:
  json, re, os.path, datetime, math, time, pathlib, textwrap,
  itertools, functools, collections, hashlib, base64, csv, urllib.parse

IMPORTANT RULES:
1. Your ENTIRE response must be a Python code block wrapped in ```python ... ```.
2. Use triple-quoted strings ('''...''' or \"\"\"...\"\"\") for any multi-line content.
3. Print your completion statement at the end using print().
4. Do NOT use __import__, eval, exec, compile, open, or any file I/O except 
   through the provided write_file/read_file functions.
5. Do NOT import modules other than those listed above.
6. Handle errors with try/except and print meaningful error messages.
"""


def extract_code_block(response_text: str) -> str:
    """
    Extract Python code from a markdown code block in the LLM response.
    Handles ```python ... ``` and ``` ... ``` formats.
    """
    # Try ```python ... ``` first
    import re
    match = re.search(r'```python\s*\n(.*?)```', response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Try ``` ... ``` (no language specifier)
    match = re.search(r'```\s*\n(.*?)```', response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # If no code block found, return the raw text as-is
    # (some models might output code without markdown fences)
    return response_text.strip()


def execute_code_act(code: str) -> str:
    """
    Execute Python code in a restricted environment.
    
    Args:
        code: Python code string to execute.
    
    Returns:
        Captured stdout output, or an error message with traceback.
    """
    # Capture stdout
    stdout_capture = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = stdout_capture
    
    # Build restricted globals
    restricted_globals = {
        "__builtins__": ALLOWED_BUILTINS,
        **TOOL_FUNCTIONS,
    }
    
    result = None
    try:
        exec(code, restricted_globals)
        result = stdout_capture.getvalue()
    except Exception as e:
        tb = traceback.format_exc()
        result = f"[CodeAct Error] {tb}"
    finally:
        sys.stdout = old_stdout
    
    return result


def run_codeact_task(
    model_name: str,
    base_url: str,
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    extra_body: dict = None,
    max_tokens: int = 20000,
) -> str:
    """
    Full CodeAct pipeline for a single sub-task:
    1. Send the prompt (with CodeAct instructions) to the LLM.
    2. Extract the Python code block from the response.
    3. Execute the code in the restricted environment.
    4. Return the execution output.
    
    Args:
        model_name: LLM model name.
        base_url: API base URL.
        api_key: API key.
        system_prompt: Base system prompt (CodeAct instructions will be appended).
        user_prompt: User prompt with sub-task details.
        extra_body: Extra body parameters for the API call.
        max_tokens: Max tokens for the LLM response.
    
    Returns:
        The stdout output from executing the generated code, or an error message.
    """
    from functions.get_model_response import get_model_response
    
    # Build the full system prompt with CodeAct instructions
    full_system_prompt = system_prompt + "\n\n" + CODEACT_INSTRUCTION
    
    # Get LLM response (no tools, just text completion)
    response = get_model_response(
        model_name=model_name,
        base_url=base_url,
        api_key=api_key,
        user_prompt=user_prompt,
        system_prompt=full_system_prompt,
        extra_body=extra_body,
        max_tokens=max_tokens,
    )
    
    llm_output = response.content if hasattr(response, 'content') else str(response)
    
    if llm_output is None:
        return "[CodeAct Error] LLM returned empty response."
    
    # Extract code block
    code = extract_code_block(llm_output)
    
    if not code:
        return f"[CodeAct Error] No executable code found in LLM response. Raw response:\n{llm_output[:500]}"
    
    print(f"[CodeAct] Extracted code ({len(code)} chars), executing...")
    
    # Execute the code
    result = execute_code_act(code)
    
    return result
