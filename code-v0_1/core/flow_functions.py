from functions.get_model_response import get_model_response
from core.code_act_executor import run_codeact_task
from functions.auto_configuration import stronger_model_configuration
import json
import re

CONFIG = stronger_model_configuration()
BASE_URL, API_KEY, MODEL_NAME, EXTRA_BODY = CONFIG[0], CONFIG[1], CONFIG[2], CONFIG[3]

AUTO_PLANNING_SYSTEM_PROMPT = """
You are an expert task planner for the 'condition flow' system. Your job is to decompose a complex task into a sequence of executable sub-tasks.

Given the current flow messages (which include the task description and possibly results from previous planning rounds), you must:

1. Analyze the [Task Description], [Background], [Existing Conditions], [Final Goal], and [Expected Result].
2. If previous step results exist in the flow messages, incorporate them — adjust the plan based on what has been completed or what new information has emerged.
3. Produce a list of sub-tasks to be executed in order. Each sub-task MUST follow this structure:

- What to do: the concrete action or analysis to perform.
- Current condition: what is already known, what environment/context is available at this step.
- Objective: the specific outcome this sub-task should achieve.
- Completion statement requirement: after executing, the sub-task must report what was done and what was produced.

Return ONLY a JSON list of strings, each string being one sub-task description following the above structure. Do NOT include any other text outside the JSON list.

Example output:
[
  "What to do: Read and parse the input data file at /data/input.csv. | Current condition: file path known, Python environment available. | Objective: Obtain the raw data as a DataFrame. | After completion, state: the file has been read, number of rows and columns identified.",
  "What to do: Clean the data by removing null values and normalizing columns. | Current condition: DataFrame loaded from previous step. | Objective: Produce a clean DataFrame ready for analysis. | After completion, state: null values removed, columns normalized, final row count reported."
]
"""

AUTO_PLANNING_USER_PROMPT = """
Here are the current flow messages. Generate the ordered sub-task list based on the task description and any prior execution results:

{flow_messages}
"""

SUB_TASK_SYSTEM_PROMPT = """
You are a sub-task executor in the 'condition flow' system. Your job is to execute a single assigned sub-task based on the current flow execution progress.

You will receive:
1. The full flow messages, which contain the original task description and all previously completed step results.
2. A specific sub-task description that you must complete now.

Your responsibilities:
- Carefully read the sub-task description, which specifies: what to do, current conditions, the objective, and the required completion statement format.
- Use the flow messages to understand the current execution context and what has already been done.
- Execute the sub-task thoroughly and produce a result that fulfills the stated objective.
- After completing the sub-task, you MUST provide a completion statement that clearly describes what was done and what was produced, following the format required in the sub-task description.

You MUST write executable Python code to accomplish the sub-task. Use the provided tool functions (write_file, read_file, execute_terminal_command, search_web, get_current_time) and allowed Python libraries.
"""

SUB_TASK_USER_PROMPT = """
Below are the current flow messages and the sub-task you need to execute.

=== Flow Messages ===
{flow_messages}

=== Sub-Task to Execute ===
{sub_task}
"""

JUDGE_SYSTEM_PROMPT = """
You are a completion judge in the 'condition flow' system. Your sole job is to determine whether the current flow execution has achieved the original task goal.

Review the flow messages, which contain:
- The original task description (including [Final Goal] and [Expected Result]).
- All sub-task execution results from the current planning round.

Compare the executed results against the [Final Goal] and [Expected Result] from the task description.

Return your judgment in exactly one of the following formats with no other text:

- If the goal has been fully achieved: [[True]]
- If the goal has NOT been fully achieved and further planning/execution is needed: [[False]]
"""

JUDGE_USER_PROMPT = """
Here are the current flow messages. Judge whether the original task goal has been achieved:

{flow_messages}
"""

CONCLUDE_SYSTEM_PROMPT = """
You are a flow conclusion writer in the 'condition flow' system. Your job is to summarize the entire execution process based on all flow messages.

The flow messages contain:
- The original task description (including [Task Description], [Background], [Existing Conditions], [Final Goal], [Expected Result]).
- All sub-task execution results from every planning round.

Your responsibilities:
- If the task was completed successfully: summarize what was accomplished, how each major step contributed, and present the final result clearly.
- If the task was NOT completed after multiple rounds: explain what progress was made, what remains unfinished, the reasons for incompletion, and the current state.

Provide a clear, well-structured summary that gives a complete picture of the flow execution journey and its outcome.
"""

CONCLUDE_USER_PROMPT = """
Here are the complete flow messages. Write a comprehensive summary of the execution:

{flow_messages}
"""

def parse_json_list(model_output:str):
    try:
        return json.loads(model_output)
    except json.JSONDecodeError:
        pass
    
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', model_output, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    
    match = re.search(r'\[.*\]', model_output, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Failed to extract the json list from model response.")

def auto_planning(flow_messages:list) -> list:
    try:
        response = get_model_response(
            base_url=BASE_URL,
            api_key=API_KEY,
            model_name=MODEL_NAME,
            user_prompt=AUTO_PLANNING_USER_PROMPT.format(flow_messages=str(flow_messages)),
            system_prompt=AUTO_PLANNING_SYSTEM_PROMPT,
            extra_body=EXTRA_BODY,
            max_tokens=20000
        ).content
        return parse_json_list(response)
    except Exception:
        return []

def execute_sub_task(sub_task_description:str, flow_messages:list) -> str:
    """
    Execute a single sub-task using CodeAct mode.
    
    Instead of the old JSON function-calling approach (which broke when
    write_file content contained unescaped quotes/newlines), we now use
    CodeAct: the LLM generates Python code directly, and we execute it
    in a restricted environment. Python's triple-quoted strings naturally
    handle multi-line content without escaping issues.
    """
    try:
        result = run_codeact_task(
            model_name=MODEL_NAME,
            base_url=BASE_URL,
            api_key=API_KEY,
            system_prompt=SUB_TASK_SYSTEM_PROMPT,
            user_prompt=SUB_TASK_USER_PROMPT.format(
                flow_messages=flow_messages,
                sub_task=sub_task_description
            ),
            extra_body=EXTRA_BODY,
            max_tokens=20000,
        )
        return result
    except Exception as e:
        print(f"[CodeAct] Sub-task execution failed: {e}")
        return f"Sub-task execution failed: {e}"

def judge_whether_finish(flow_messages:list) -> bool:
    try:
        judge_result = get_model_response(
            base_url=BASE_URL,
            api_key=API_KEY,
            model_name=MODEL_NAME,
            user_prompt=JUDGE_USER_PROMPT.format(flow_messages=flow_messages),
            system_prompt=JUDGE_SYSTEM_PROMPT,
            extra_body=EXTRA_BODY,
            max_tokens=2000
        ).content.strip()
        if "[[True]]" in judge_result:
            return True
        else:
            return False
    except Exception:
        print("[Condition Flow] Judge flow result failed")
        return False

def flow_conclusion(flow_messages:list) -> str:
    try:
        conclusion = get_model_response(
            base_url=BASE_URL,
            api_key=API_KEY,
            model_name=MODEL_NAME,
            user_prompt=CONCLUDE_USER_PROMPT.format(flow_messages=flow_messages),
            system_prompt=CONCLUDE_SYSTEM_PROMPT,
            extra_body=EXTRA_BODY,
            max_tokens=10000
        ).content
        return conclusion
    except RuntimeError:
        return "Flow conclusion failed."
