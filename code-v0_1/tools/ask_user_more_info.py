def ask_user_more_info(question:str) -> str:
    user_ans = input(f"[Model's Query] {question}\n>>>")
    return f"The user replies: \" {user_ans} \""

ASK_USER_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "ask_user_more_info",
        "description": "Ask the user a follow-up question when more information is needed to complete the task.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question to ask the user to gather more details."
                }
            },
            "required": ["question"],
        },
    },
}