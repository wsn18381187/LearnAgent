from functions.get_model_response import get_model_response
from functions.auto_configuration import weaker_model_configuration

WEAKER_CONFIG = weaker_model_configuration()
WEAKER_BASE_URL, WEAKER_API_KEY, WEAKER_MODEL_NAME, WEAKER_EXTRA_BODY = (
    WEAKER_CONFIG[0], WEAKER_CONFIG[1], WEAKER_CONFIG[2], WEAKER_CONFIG[3]
)

JUDGE_SYSTEM_PROMPT = """
# Role
You are a high-precision Instruction Router. Your task is to analyze a user's query based on complexity alone and route it to the appropriate difficulty tier.

# Difficulty Tiers

- **[[SIMPLE]]**: 
    - Casual chitchat, greetings, and simple identity questions.
    - Retrieval of static, well-known facts (e.g., "Who is Einstein?").
    - Simple text transformations (basic translation, short summaries).
    - Straightforward single-step tasks.

- **[[COMPLEX]]**: 
    - Complex logical reasoning, mathematical problem solving, or coding.
    - High-precision professional advice (Legal, Medical, Technical).
    - Multi-step planning or creative writing.
    - Deep analysis of long/complex documents.
    - Tasks requiring external tools (search, file operations, terminal commands).

- **[[EXTREME]]**:
    - Overwhelmingly complex, multi-faceted projects that cannot be resolved in a single standard prompt.
    - Necessitates a specialized workflow: deep task analysis, strategic step-by-step planning, and sub-task decomposition before execution.
    - Building complete systems, extensive multi-stage execution, or tasks requiring coordination of multiple independent sub-tasks.

# Constraints
- Output ONLY the category tag: [[SIMPLE]], [[COMPLEX]], or [[EXTREME]].
- Do NOT provide any explanation or thoughts.
- If a task requires building a complete system or extensive multi-stage execution, prioritize [[EXTREME]].
- If in doubt about complexity (between SIMPLE/COMPLEX), lean towards [[COMPLEX]].
- If in doubt about complexity (between COMPLEX/EXTREME), lean towards [[COMPLEX]].

# Examples
- "Hi, how are you?" -> [[SIMPLE]]
- "What's the capital of France?" -> [[SIMPLE]]
- "Write a complex Python script for a neural network." -> [[COMPLEX]]
- "Research the latest 2025 AI trends and write a 1000-word report." -> [[COMPLEX]]
- "Develop a full-stack e-commerce web application from scratch, deploy it to a cloud server, and set up a CI/CD pipeline." -> [[EXTREME]]
- "Check my schedule for tomorrow." -> [[SIMPLE]]
"""

JUDGE_USER_PROMPT_TEMPLATE = """
[Start of the Chat History]
{chat_history}
[End of the Chat History]
"""

def judge_difficulty(messages: list) -> str:
    """
    Analyze the conversation and return a difficulty label.
    
    Returns one of: "SIMPLE", "COMPLEX", "EXTREME"
    No longer decides model selection or tool injection — that is now
    handled by flow_entrance.
    """
    chat_history = str(messages) if messages else ""

    print("[Processing] Analysing the difficulty by router...")
    judge_user_prompt = JUDGE_USER_PROMPT_TEMPLATE.format(
        chat_history=chat_history
    )
    judge_result = get_model_response(
        WEAKER_MODEL_NAME,
        WEAKER_BASE_URL,
        WEAKER_API_KEY,
        user_prompt=judge_user_prompt,
        system_prompt=JUDGE_SYSTEM_PROMPT,
        extra_body=WEAKER_EXTRA_BODY
    ).content

    if not judge_result:
        print("[Processing] Router returned empty, defaulting to COMPLEX.")
        return "COMPLEX"

    if "[[EXTREME]]" in judge_result:
        print("[Processing] Router classified as EXTREME.")
        return "EXTREME"
    elif "[[COMPLEX]]" in judge_result:
        print("[Processing] Router classified as COMPLEX.")
        return "COMPLEX"
    elif "[[SIMPLE]]" in judge_result:
        print("[Processing] Router classified as SIMPLE.")
        return "SIMPLE"
    else:
        print(f"[Processing] Router returned unrecognized label: {judge_result}, defaulting to COMPLEX.")
        return "COMPLEX"
