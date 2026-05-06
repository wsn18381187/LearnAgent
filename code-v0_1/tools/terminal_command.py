import subprocess
import platform
import time
import os
import signal
from datetime import datetime

CURRENT_OS = platform.system()
ATTEMPT_TIME = 3
TIMEOUT = 30
BG_LOG_DIR = "/tmp/learnagent_bg_tasks"

def execute_terminal_command(command: str, background: bool = False) -> str:
    """
    Execute a terminal command on the local system.
    
    Args:
        command: The shell command string to execute.
        background: If False (default), run synchronously with timeout and retries.
                    If True, launch the command in background, redirect stdout/stderr
                    to a log file, and return immediately with PID and log path.
    """
    current_os = platform.system()
    
    if background:
        return _execute_background(command, current_os)
    else:
        return _execute_sync(command, current_os)


def _kill_process(proc: subprocess.Popen) -> None:
    """Kill a process and its entire process group. Best-effort, never raises."""
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            proc.wait()
    except (ProcessLookupError, OSError):
        pass  # Process already gone


def _execute_sync(command: str, current_os: str) -> str:
    """Synchronous execution with timeout and retries."""
    for attempt in range(ATTEMPT_TIME):
        proc = None
        try:
            proc = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )
            stdout, stderr = proc.communicate(timeout=TIMEOUT)
            
            output = (f"OS: {current_os}\n"
                      f"Stdout: {stdout}\n"
                      f"Stderr: {stderr}\n"
                      f"Return Code: {proc.returncode}")
            print("+--terminal------------------------")
            print(output)
            print("+----------------------------------")
            return output
            
        except subprocess.TimeoutExpired:
            _kill_process(proc)
            if attempt < ATTEMPT_TIME - 1:
                time.sleep(3)
                continue
            return f"Error: Command timed out after {ATTEMPT_TIME} attempts."
        except Exception as e:
            if proc is not None:
                _kill_process(proc)
            return f"Error: {str(e)}"


def _execute_background(command: str, current_os: str) -> str:
    """
    Launch command in background. stdout and stderr are redirected to a log file.
    Returns immediately with PID and log path so the caller can monitor progress.
    The process is started in its own session so it won't be affected if the
    parent exits.
    """
    os.makedirs(BG_LOG_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(BG_LOG_DIR, f"bg_{timestamp}.log")
    
    try:
        with open(log_path, "w") as log_file:
            log_file.write(f"=== Background Task ===\n")
            log_file.write(f"Command: {command}\n")
            log_file.write(f"Started at: {datetime.now().isoformat()}\n")
            log_file.write(f"{'='*50}\n\n")
            
            proc = subprocess.Popen(
                command,
                shell=True,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        
        output = (f"OS: {current_os}\n"
                  f"Background task started.\n"
                  f"PID: {proc.pid}\n"
                  f"Log file: {log_path}\n"
                  f"Check status: execute_terminal_command('ps -p {proc.pid}') — empty stdout means finished.\n"
                  f"Read output: read_file('{log_path}')\n"
                  f"Kill task: execute_terminal_command('kill -TERM -- -$(ps -o pgid= -p {proc.pid} | tr -d \" \")')")
        print("+--terminal (background)-----------")
        print(output)
        print("+----------------------------------")
        return output
        
    except Exception as e:
        return f"Error launching background task: {str(e)}"


EXECUTE_COMMAND_DEFINITION = {
    "type": "function",
    "function": {
        "name": "execute_terminal_command",
        "description": (
            f"Execute a terminal command on the local system. "
            f"The current Operating System is {CURRENT_OS}. "
            f"Use appropriate syntax for this OS. "
            f"Set background=True for long-running tasks (training, downloads, servers) "
            f"to launch them in background and return immediately with PID and log path."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The full shell command string to execute."
                },
                "background": {
                    "type": "boolean",
                    "description": (
                        "Set to true for long-running commands (training, downloads, servers). "
                        "The command will run in background, output goes to a log file. "
                        "Returns immediately with PID and log path. "
                        "Default is false (synchronous execution with 30s timeout)."
                    )
                }
            },
            "required": ["command"],
        },
    },
}
