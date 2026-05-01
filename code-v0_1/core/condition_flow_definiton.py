CONDITION_FLOW_DESCRIPTION = """
This tool is the entrance of entering the \'condition flow\', a special mode which is designed for extremely hard task that not only require deep analyze and multi-tool-use, but also need a detailed plan to coorporate and execute with other SOTA models.
The \'condition flow\' will automatically make a multi-step plan to solve given task and carry it out step by step and return the processed result.
You need to analyze and conclude current task and provide the task description, background, existing conditions, final goal and expected result of it.
"""

TASK_DESCRIPTION = """
The detailed description of the task, include the description, background, existing conditions, final goal and expected result of it.
Your description of your task should follow the template below:

[Task Description]
(The concluded description of the whole task in a brief way)

[Background]
(Necessary background information of the task that can be used to analyze)

[Existing Conditions]
(Main conditions of current task, may include environment info, file path, hardware and software info, etc.)

[Final Goal]
(The description of the goal of the task)

[Expected Result]
(Content or format that expecting the \'condifion flow\' to return)
"""

CONDITION_FLOW_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "condition_flow",
        "description": CONDITION_FLOW_DESCRIPTION,
        "parameters": {
            "type": "object",
            "properties": {
                "task_description": {
                    "type": "string",
                    "description": TASK_DESCRIPTION,
                }
            },
            "required": ["task_description"],
        },
    },
}