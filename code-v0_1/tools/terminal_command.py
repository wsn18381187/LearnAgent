import subprocess
import platform
import time

CURRENT_OS = platform.system()
ATTEMPT_TIME = 3

def execute_terminal_command(command: str) -> str:
    current_os = platform.system()
    
    for attempt in range(ATTEMPT_TIME+1):  # Total 3 attempts
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=30
            )
            
            output = (f"OS: {current_os}\n"
                      f"Stdout: {result.stdout}\n"
                      f"Stderr: {result.stderr}\n"
                      f"Return Code: {result.returncode}")
            print("+--terminal------------------------")
            print(output)
            print("+----------------------------------")
            return output
        except subprocess.TimeoutExpired:
            if attempt < ATTEMPT_TIME:
                time.sleep(3)  # Wait before retrying
                continue
            return f"Error: Command timed out after 3 attempts."
        except Exception as e:
            return f"Error: {str(e)}"

EXECUTE_COMMAND_DEFINITION = {
    "type": "function",
    "function": {
        "name": "execute_terminal_command",
        "description": (
            f"Execute a terminal command on the local system. "
            f"The current Operating System is {CURRENT_OS}. "
            f"Use appropriate syntax for this OS."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The full shell command string to execute."
                }
            },
            "required": ["command"],
        },
    },
}