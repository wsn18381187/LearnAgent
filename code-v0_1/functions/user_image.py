from functions.get_model_response import get_model_response
from functions.auto_configuration import weaker_model_configuration, stronger_model_configuration
from tools.get_current_time import get_current_time
import json
import os

USER_IMAGE_PATH = "user_info/user_image.json"

MODEL_CONFIG = stronger_model_configuration()
BASE_URL, API_KEY, MODEL_NAME, EXTRA_BODY = MODEL_CONFIG[0], MODEL_CONFIG[1], MODEL_CONFIG[2], MODEL_CONFIG[3]

UPDATE_SYSTEM_PROMPT = """
You are an intelligent User Profile Manager. Your task is to update the user's profile JSON based on the latest conversation. You will be provided with the current JSON, the new conversation, and the current time.

# Core Directives for Intelligent Management
1. IGNORE TRIVIAL CHATS: Do NOT update the profile (except `last_interaction`) if the conversation consists only of short greetings (e.g., "hi", "hello"), meaningless test words (e.g., "test", "123"), or lacks substantive information.
2. INTELLIGENT MERGING: If the current conversation relates to past topics or previous interactions, intelligently merge them into a single concise entry rather than adding a new one.
3. RUTHLESS PRUNING: Always discard outdated, transient, or less important details to maintain limits. Keep the profile dense and meaningful.

# JSON Schema (MUST be strictly followed)
{
  "basic_info": { ... },
  "preferences": [ ... ],
  "facts": [ ... ],
  "chat_history": [ ... ],
  "last_interaction": "..."
}

---

# Field Update Rules

## 1. `basic_info` (Stable identity attributes)
- Record ONLY fundamental, long-term identity info (name, location, profession, education, etc.).
- Overwrite only if new information contradicts or updates existing entries.

## 2. `preferences` (Enduring traits & preferences)
- STRICT LIMIT: Maximum 10 words/characters per item.
- Record stable preferences, habits, and interaction styles.
- Merge similar preferences. Remove outdated ones.

## 3. `facts` (Key factual knowledge - STRICT 30 ITEM LIMIT)
- ARRAY LIMIT: Maximum 30 items in total.
- LENGTH LIMIT: Maximum 10 words/characters per item.
- KEEP (High Value): Identity, achievements, core skills, active long-term projects.
- DISCARD (Low Value): One-time bugs, transient queries, minor tool usage, trivia.
- Pruning & Merging Strategy (if approaching 30 items): 
  1. Delete transient/low-value items first.
  2. Merge related facts (e.g., merge multiple bug fixes into one skill description).
  3. Delete the oldest/least important facts if necessary.

## 4. `chat_history` (Event log - STRICT 30 ITEM LIMIT)
- ARRAY LIMIT: Maximum 30 items in total.
- Format: "YYYY-MM-DD HH:mm, [Summary]".
- LENGTH LIMIT: The [Summary] part MUST NOT exceed 15 words/characters.
- Smart Merging: If continuing a previous topic, DO NOT add a new entry. Instead, UPDATE the existing entry's timestamp and summary.
- Ignore Trivialities: NEVER add greetings, test words, or meaningless chats to this array.
- De-duplication: Merge entries describing similar events. Drop the oldest entries (FIFO) if exceeding 30.

## 5. `last_interaction`
- Update with the provided current time string. This part alse MUST NOT exceed 15 words/characters.

---

# Strict Output Constraints
- Output ONLY the raw, valid JSON string.
- NO Markdown formatting of any kind (do NOT use ```json fences).
- NO greetings, explanations, or conversational text outside the JSON.
- The JSON must be parseable by Python's `json.loads()`.
- Use double quotes for all strings and keys.
"""

UPDATE_USER_PROMPT = """
[Start of Current User Profile]
{user_image_file}
[End of Current User Profile]

[Start of Current Conversation History]
{chat_history}
[End of Current Conversation History]

Time of current conversation: {conversation_time}

Please intelligently update the profile JSON based on the conversation history. Remember the absolute constraints:
- Ignore trivial conversations (greetings, tests, etc.) entirely.
- `facts` array: MAX 30 items. Each item MAX 10 words/characters.
- `chat_history` array: MAX 30 items. Each summary MAX 15 words/characters.
- `preferences` array: Each item MAX 10 words/characters.
- Intelligently merge similar or continuing topics to save space. Discard low-value details.
- Output ONLY valid, raw JSON. No markdown formatting.
"""

def update_user_image(messages: list = None):
    if not os.path.exists(USER_IMAGE_PATH):
        os.makedirs(os.path.dirname(USER_IMAGE_PATH), exist_ok=True)
        with open(USER_IMAGE_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "basic_info": {},
                "preferences": [],
                "facts": [],
                "chat_history": [],
                "last_interaction": ""
            }, f, ensure_ascii=False, indent=2)

    try:
        with open(USER_IMAGE_PATH, "r", encoding="utf-8") as f:
            old_user_image = json.load(f)
    except Exception as e:
        old_user_image = {}
        print(f"[Error] Load json file failed. {e}")

    update_user_prompt = UPDATE_USER_PROMPT.format(
        user_image_file=json.dumps(old_user_image, ensure_ascii=False) if old_user_image else "",
        chat_history=str(messages) if messages else "",
        conversation_time=str(get_current_time())
    )

    response = get_model_response(
        base_url=BASE_URL,
        api_key=API_KEY,
        model_name=MODEL_NAME,
        user_prompt=update_user_prompt,
        system_prompt=UPDATE_SYSTEM_PROMPT,
        response_format={"type": "json_object"},
        extra_body=EXTRA_BODY
    ).content

    try:
        updated_user_image = json.loads(response)
    except Exception as e:
        raise Exception(f"json.loads() failed. Raw response:\n{response}\nError: {e}")

    MAX_FACTS = 30
    MAX_CHAT_HISTORY = 30

    if "facts" in updated_user_image and len(updated_user_image["facts"]) > MAX_FACTS:
        print(f"[Warning] Model returned {len(updated_user_image['facts'])} facts, trimming to {MAX_FACTS}.")
        updated_user_image["facts"] = updated_user_image["facts"][:MAX_FACTS]

    if "chat_history" in updated_user_image and len(updated_user_image["chat_history"]) > MAX_CHAT_HISTORY:
        print(f"[Warning] Model returned {len(updated_user_image['chat_history'])} chat_history entries, trimming to {MAX_CHAT_HISTORY}.")
        updated_user_image["chat_history"] = updated_user_image["chat_history"][-MAX_CHAT_HISTORY:]

    with open(USER_IMAGE_PATH, "w", encoding="utf-8") as f:
        json.dump(updated_user_image, f, ensure_ascii=False, indent=2)
    return


def provide_user_image() -> str:
    try:
        with open(USER_IMAGE_PATH, "r", encoding="utf-8") as f:
            user_image = json.load(f)
        return json.dumps(user_image, ensure_ascii=False)
    except Exception as e:
        print(f"[Error] Load json file failed. {e}")
        return "{}"
