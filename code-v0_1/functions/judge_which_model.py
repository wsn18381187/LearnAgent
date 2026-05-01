from functions.get_model_response import get_model_response
from functions.use_tools_to_analyze import use_tool_to_analyze
from functions.auto_configuration import weaker_model_configuration, stronger_model_configuration
from core.flow_entrance import flow_entrance

LOCAL_MODEL_NAME = "deepseek-r1:8b"
LOCAL_MODEL_URL = "http://localhost:11434/v1"


WEAKER_CONFIG = weaker_model_configuration()
WEAKER_BASE_URL, WEAKER_API_KEY, WEAKER_MODEL_NAME, WEAKER_EXTRA_BODY = WEAKER_CONFIG[0], WEAKER_CONFIG[1], WEAKER_CONFIG[2], WEAKER_CONFIG[3]

STRONGER_CONFIG = stronger_model_configuration()
STRONGER_BASE_URL, STRONGER_API_KEY, STRONGER_MODEL_NAME, STRONGER_EXTRA_BODY = STRONGER_CONFIG[0], STRONGER_CONFIG[1], STRONGER_CONFIG[2], STRONGER_CONFIG[3]

JUDGE_SYSTEM_PROMPT = """
# Role
You are a high-precision Instruction Router. Your task is to analyze a user's query based on complexity (Small, Large, or Extremely Hard) and tool requirements to route it to the appropriate execution flow.

# Classification Matrix

- **[[A]]**: Small Model + **No Tools**
- **[[B]]**: Small Model + **Tool Needed**
- **[[C]]**: Large Model + **No Tools**
- **[[D]]**: Large Model + **Tool Needed**
- **[[E]]**: **Condition Flow** (Extremely Hard task requiring task analysis, planning, and decomposition)

# Dimension 1: Model Capability (Complexity)
- **Small Model (A/B)**: 
    - Casual chitchat, greetings, and simple identity questions.
    - Retrieval of static, well-known facts (e.g., "Who is Einstein?").
    - Simple text transformations (basic translation, short summaries).
- **Large Model (C/D)**: 
    - Complex logical reasoning, mathematical problem solving, or coding.
    - High-precision professional advice (Legal, Medical, Technical).
    - Multi-step planning or creative writing.
    - Deep analysis of long/complex documents.
- **Extremely Hard (E)**:
    - Overwhelmingly complex, multi-faceted projects that cannot be resolved in a single standard prompt.
    - Necessitates a specialized workflow: deep task analysis, strategic step-by-step planning, and sub-task decomposition before execution.

# Dimension 2: Tool Requirement (Data Source)
- **No Tools (A/C)**: 
    - The question can be answered entirely using internal knowledge or the provided context.
    - General knowledge that does not change with time.
- **Tool Needed (B/D)**: 
    - **Real-time info**: Weather, current time, news, stock prices, search.
    - **External Action**: Database queries, API calls, or web browsing.
    - **Information Gap**: When the query is too vague and requires asking the user for clarification/supplementary information before proceeding.
*(Note: Category [[E]] inherently involves complex system coordination and supersedes the standard tool requirement check.)*

# Output Selection Guide
1. **[[A]]**: Simple conversational tasks or static facts that need no external data.
2. **[[B]]**: Simple tasks that require a specific tool (e.g., "What's the weather?", "What time is it?").
3. **[[C]]**: Difficult tasks (coding, reasoning) that can be solved with internal knowledge.
4. **[[D]]**: Difficult tasks that also require external search, real-time data, or multi-step tool execution.
5. **[[E]]**: Extremely difficult and ambitious tasks that must enter the Condition Flow to be analyzed, planned, and broken down into smaller achievable steps.

# Constraints
- Output ONLY the category tag: [[A]], [[B]], [[C]], [[D]], or [[E]].
- Do NOT provide any explanation or thoughts.
- If a task requires building a complete system or extensive multi-stage execution, prioritize [[E]].
- If a query is time-sensitive (even if simple), it MUST be categorized as [[B]] or [[D]].
- If in doubt about complexity (between Small/Large), lean towards **Large Model (C/D)**.
- If in doubt about information completeness, lean towards **Tool Needed (B/D)** to trigger a clarification question.

# Examples
- "Hi, how are you?" -> [[A]]
- "What's the current temperature in London?" -> [[B]]
- "Write a complex Python script for a neural network." -> [[C]]
- "Research the latest 2025 AI trends and write a 1000-word report." -> [[D]]
- "Develop a full-stack e-commerce web application from scratch, deploy it to a cloud server, and set up a CI/CD pipeline." -> [[E]]
- "Check my schedule for tomorrow." -> [[B]]
"""

JUDGE_USER_PROMPT_TEMPLATE = """
[Start of the Chat History]
{chat_history}
[End of the Chat History]
"""

def judge_which_model(messages: list) -> str:
    chat_history = str(messages) if messages else ""

    print("[Processing] Analysing the difficulty by router...")
    judge_user_prompt = JUDGE_USER_PROMPT_TEMPLATE.format(
        chat_history=chat_history
    )
    judge_result = get_model_response(WEAKER_MODEL_NAME,WEAKER_BASE_URL,WEAKER_API_KEY,user_prompt=judge_user_prompt,system_prompt=JUDGE_SYSTEM_PROMPT,extra_body=WEAKER_EXTRA_BODY).content
    if (judge_result and "[[A]]" in judge_result) or not judge_result:
        print("[Processing] Router choose to use the weaker model.")
        response = get_model_response(WEAKER_MODEL_NAME,WEAKER_BASE_URL,WEAKER_API_KEY,messages=messages,extra_body=WEAKER_EXTRA_BODY).content
        print(f"\033[32m[Model Response]\033[0m {response}")
        return response
    elif judge_result and "[[B]]" in judge_result:
        print("[Processing] Router choose to use the weaker model.")
        response = use_tool_to_analyze(WEAKER_MODEL_NAME,WEAKER_BASE_URL,WEAKER_API_KEY,messages=messages,extra_body=WEAKER_EXTRA_BODY).content
        print(f"\033[32m[Model Response]\033[0m {response}")
        return response
    elif judge_result and "[[C]]" in judge_result:
        print("[Processing] Router choose to use the stronger model.")
        response = get_model_response(STRONGER_MODEL_NAME,STRONGER_BASE_URL,STRONGER_API_KEY,max_tokens=20000,messages=messages,extra_body=STRONGER_EXTRA_BODY).content
        print(f"\033[32m[Model Response]\033[0m {response}")
        return response
    elif judge_result and "[[D]]" in judge_result:
        print("[Processing] Router choose to use the stronger model")
        response = use_tool_to_analyze(STRONGER_MODEL_NAME,STRONGER_BASE_URL,STRONGER_API_KEY,max_tokens=20000,messages=messages,extra_body=STRONGER_EXTRA_BODY).content
        print(f"\033[32m[Model Response]\033[0m {response}")
        return response
    elif judge_result and "[[E]]" in judge_result:
        print("[Processing] Router choose to use the Condition Flow to solve the task")
        response = flow_entrance(STRONGER_MODEL_NAME,STRONGER_BASE_URL,STRONGER_API_KEY,max_tokens=100000,messages=messages,extra_body=STRONGER_EXTRA_BODY).content
        print(f"\033[32m[Model Response]\033[0m {response}")
        return response
    else:
        raise RuntimeError("[Error] Router failed to choose the model.")