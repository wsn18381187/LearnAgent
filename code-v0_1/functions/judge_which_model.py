from functions.get_model_response import get_model_response
from functions.use_tools_to_analyze import use_tool_to_analyze
from functions.auto_configuration import weaker_model_configuration, stronger_model_configuration
from core.flow_entrance import flow_entrance

WEAKER_CONFIG = weaker_model_configuration()
WEAKER_BASE_URL, WEAKER_API_KEY, WEAKER_MODEL_NAME, WEAKER_EXTRA_BODY = WEAKER_CONFIG[0], WEAKER_CONFIG[1], WEAKER_CONFIG[2], WEAKER_CONFIG[3]

STRONGER_CONFIG = stronger_model_configuration()
STRONGER_BASE_URL, STRONGER_API_KEY, STRONGER_MODEL_NAME, STRONGER_EXTRA_BODY = STRONGER_CONFIG[0], STRONGER_CONFIG[1], STRONGER_CONFIG[2], STRONGER_CONFIG[3]

JUDGE_SYSTEM_PROMPT = """
# Role
You are a high-precision Instruction Router. Your task is to analyze a user's query based purely on its complexity and difficulty (Normal, Complex, or Extremely Hard) to route it to the appropriate execution flow.
You will be provided with the recent chat history. Use the history for context, but YOUR MAIN GOAL IS TO CLASSIFY THE LATEST USER REQUEST.

# Classification Matrix
- **[[A]]**: Normal (Suitable for Small Model / Simple Routing)
- **[[B]]**: Complex (Suitable for Large Model / Advanced Reasoning)
- **[[C]]**: Extremely Hard (Requires Condition Flow / Task Decomposition)

# Complexity Levels
- **Normal ([[A]])**: 
    - Casual chitchat, greetings, and simple identity questions.
    - Retrieval of straightforward facts (e.g., "Who is Einstein?", "What is the weather today?").
    - Simple text transformations (basic translation, short summaries).
    - Basic single-step instructions.
- **Complex ([[B]])**: 
    - Complex logical reasoning, mathematical problem solving, or coding.
    - High-precision professional advice (Legal, Medical, Technical).
    - Multi-step planning, creative writing, or extensive research.
    - Deep analysis of long/complex documents.
- **Extremely Hard ([[C]])**:
    - Overwhelmingly complex, multi-faceted projects that cannot be resolved in a single standard prompt.
    - Necessitates a specialized workflow: deep task analysis, strategic step-by-step planning, and sub-task decomposition before execution.
    - Examples include building full software systems from scratch or executing massive multi-stage workflows.

# Output Selection Guide
1. **[[A]]**: Everyday queries, basic factual questions, and simple tasks that require minimal reasoning.
2. **[[B]]**: Difficult tasks that require deep thinking, logic, professional knowledge, or moderate generation effort.
3. **[[C]]**: Ambitious, massive tasks that MUST be analyzed, planned, and broken down into smaller achievable steps to succeed.

# Constraints
- Output ONLY the category tag: [[A]], [[B]], or [[C]].
- Do NOT provide any explanation or thoughts.
- If a task requires building a complete system or extensive multi-stage execution, prioritize [[C]].
- If in doubt about complexity (between Normal and Complex), lean towards **Complex ([[B]])**.

# Examples
- "Hi, how are you?" -> [[A]]
- "What's the current temperature in London?" -> [[A]]
- "Translate this short email to Spanish." -> [[A]]
- "Write a complex Python script to train a neural network on a custom dataset." -> [[B]]
- "Research the latest 2026 AI trends and write a highly detailed 1000-word report." -> [[B]]
- "Develop a full-stack e-commerce web application from scratch, deploy it to a cloud server, and set up a CI/CD pipeline." -> [[C]]
"""

JUDGE_USER_PROMPT_TEMPLATE = """
[Start of the Chat History]
{chat_history}
[End of the Chat History]
"""

def judge_which_model(messages: list) -> str:
    chat_history = str(messages[-60:]) if messages else ""

    print("[Processing] Analysing the difficulty by router...")
    judge_user_prompt = JUDGE_USER_PROMPT_TEMPLATE.format(
        chat_history=chat_history
    )
    judge_result = get_model_response(WEAKER_MODEL_NAME,WEAKER_BASE_URL,WEAKER_API_KEY,user_prompt=judge_user_prompt,system_prompt=JUDGE_SYSTEM_PROMPT,extra_body=WEAKER_EXTRA_BODY).content
    if judge_result and "[[A]]" in judge_result:
        print("[Processing] Router choose to use the weaker model.")
        response = use_tool_to_analyze(WEAKER_MODEL_NAME,WEAKER_BASE_URL,WEAKER_API_KEY,messages=messages,extra_body=WEAKER_EXTRA_BODY).content
        print(f"\033[32m[Model Response]\033[0m {response}")
        return response
    elif judge_result and "[[B]]" in judge_result:
        print("[Processing] Router choose to use the stronger model")
        response = use_tool_to_analyze(STRONGER_MODEL_NAME,STRONGER_BASE_URL,STRONGER_API_KEY,max_tokens=20000,messages=messages,extra_body=STRONGER_EXTRA_BODY).content
        print(f"\033[32m[Model Response]\033[0m {response}")
        return response
    elif judge_result and "[[C]]" in judge_result:
        print("[Processing] Router choose to use the Condition Flow to solve the task")
        response = flow_entrance(STRONGER_MODEL_NAME,STRONGER_BASE_URL,STRONGER_API_KEY,max_tokens=100000,messages=messages,extra_body=STRONGER_EXTRA_BODY).content
        print(f"\033[32m[Model Response]\033[0m {response}")
        return response
    else:
        raise RuntimeError("[Error] Router failed to choose the model.")