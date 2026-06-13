from functions.get_model_response import get_model_response
from core.condition_flow_definiton import CONDITION_FLOW_TOOL_DEFINITION
from core.condition_flow import condition_flow
from functions.choose_which_tools import choose_which_tools, get_tool_result
from core.code_act_executor import run_codeact_task
from functions.auto_configuration import weaker_model_configuration, stronger_model_configuration
import json

WEAKER_CONFIG = weaker_model_configuration()
WEAKER_BASE_URL, WEAKER_API_KEY, WEAKER_MODEL_NAME, WEAKER_EXTRA_BODY = (
    WEAKER_CONFIG[0], WEAKER_CONFIG[1], WEAKER_CONFIG[2], WEAKER_CONFIG[3]
)

STRONGER_CONFIG = stronger_model_configuration()
STRONGER_BASE_URL, STRONGER_API_KEY, STRONGER_MODEL_NAME, STRONGER_EXTRA_BODY = (
    STRONGER_CONFIG[0], STRONGER_CONFIG[1], STRONGER_CONFIG[2], STRONGER_CONFIG[3]
)


def flow_entrance(
        difficulty: str,
        messages: list = None,
        max_tokens: int = 2000,
        max_retries: int = 3,
        temperature: float = 0,
        response_format: dict = None,
        extra_body: dict = None,
        max_tool_turns: int = 50
    ) -> str:
    """
    Unified entry point for all difficulty levels.
    
    Args:
        difficulty: "SIMPLE", "COMPLEX", or "EXTREME"
        messages: conversation messages list
        ...
    
    Router now only judges difficulty. Model selection and tool injection
    are handled here, with tools built once at the start.
    """
    # ---- 1. Select model based on difficulty ----
    if difficulty == "SIMPLE":
        model_name = WEAKER_MODEL_NAME
        base_url = WEAKER_BASE_URL
        api_key = WEAKER_API_KEY
        if extra_body is None:
            extra_body = WEAKER_EXTRA_BODY
    elif difficulty in ("COMPLEX", "EXTREME"):
        model_name = STRONGER_MODEL_NAME
        base_url = STRONGER_BASE_URL
        api_key = STRONGER_API_KEY
        if extra_body is None:
            extra_body = STRONGER_EXTRA_BODY
    else:
        raise ValueError(f"Unknown difficulty: {difficulty}. Must be SIMPLE, COMPLEX, or EXTREME.")

    # ---- 2. Build tools ONCE at the start ----
    tools = choose_which_tools()
    if difficulty == "EXTREME":
        tools = [CONDITION_FLOW_TOOL_DEFINITION] + tools

    tool_call_count = 0
    consecutive_json_failures = 0
    MAX_CONSECUTIVE_JSON_FAILURES = 3

    if messages is None:
        raise ValueError("messages must be provided.")

    while tool_call_count < max_tool_turns:
        response = get_model_response(
            model_name=model_name,
            base_url=base_url,
            api_key=api_key,
            messages=messages,
            tools=tools,
            response_format=response_format,
            extra_body=extra_body,
            max_tokens=max_tokens
        )

        if not response.tool_calls:
            print(f"[Processing] Model decides to reply without tools or finished tools.")
            return response

        messages.append(response.model_dump(exclude_none=True))

        for tool_call in response.tool_calls:
            function_name = tool_call.function.name
            print(f"[Processing] Model chooses to use {function_name}.")
            try:
                args = json.loads(tool_call.function.arguments)
                if function_name == "condition_flow":
                    result = condition_flow(args['task_description'])
                    content = str(result)
                elif function_name == "write_file":
                    print(f"[CodeAct] write_file triggered for {args.get('file_path')}, switching to CodeAct...")
                    codeact_user_prompt = f"""Write a file at "{args.get('file_path')}" with the following description:
{args.get('description', 'No description provided.')}

Use the write_file() function to write the content. Make sure to create parent directories if needed (write_file handles this automatically).
Print a success message when done."""
                    result = run_codeact_task(
                        model_name=model_name,
                        base_url=base_url,
                        api_key=api_key,
                        system_prompt=messages[0]["content"] if messages and messages[0]["role"] == "system" else "",
                        user_prompt=codeact_user_prompt,
                        extra_body=extra_body,
                        max_tokens=max_tokens,
                    )
                    content = str(result)
                else:
                    result = get_tool_result(function_name, args)
                    content = str(result)
                consecutive_json_failures = 0
            except json.JSONDecodeError as e:
                consecutive_json_failures += 1
                print(f"[Warning] JSON parse failed for {function_name}: {e}")
                if consecutive_json_failures >= MAX_CONSECUTIVE_JSON_FAILURES:
                    print(f"[Warning] {MAX_CONSECUTIVE_JSON_FAILURES} consecutive JSON failures, aborting tool loop.")
                    content = f"[Error] JSON parse failed {consecutive_json_failures} times consecutively. Last error: {e}. The tool call arguments could not be parsed. Please simplify your tool call or break the task into smaller steps."
                else:
                    content = (
                        f"[Error] Your previous tool call arguments were invalid JSON: {e}. "
                        f"Please regenerate with properly escaped JSON. "
                        f"Common issues: unescaped double quotes in string values, unescaped newlines, "
                        f"or the JSON string was truncated. Make sure all special characters inside "
                        f"string values are properly escaped (e.g., \\\" for double quotes, \\n for newlines)."
                    )
            except Exception as e:
                print(f"[Warning] Tool call failed: {e}")
                content = f"[Error] {e}"
                consecutive_json_failures = 0
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": content
            })
        tool_call_count += len(response.tool_calls)
    print(f"[Processing] Exceeded max tool call turns {max_tool_turns}.")
    return response
