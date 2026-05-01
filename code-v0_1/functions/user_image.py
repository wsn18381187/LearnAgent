from functions.get_model_response import get_model_response
from functions.auto_configuration import weaker_model_configuration, stronger_model_configuration
from tools.get_current_time import get_current_time
import json
import os

USER_IMAGE_PATH = "user_info/user_image.json"

MODEL_CONFIG = stronger_model_configuration()
BASE_URL, API_KEY, MODEL_NAME, EXTRA_BODY = MODEL_CONFIG[0], MODEL_CONFIG[1], MODEL_CONFIG[2], MODEL_CONFIG[3]

UPDATE_SYSTEM_PROMPT = """
You are an intelligent User Profile Manager. Your task is to update the user's profile JSON based on the latest conversation. You will be provided with the current JSON, the new conversation, and the **current time**.

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
- Record ONLY fundamental, long-term identity information about the user: name, location, profession, education level, etc.
- Update only when new information contradicts or supplements existing entries.
- Do NOT record transient states or one-time events here.

## 2. `preferences` (Enduring user preferences & traits)
- Record the user's stable preferences, habits, interaction style, and personality traits.
- Examples: "prefers concise answers", "enjoys dark humor", "uses Python as primary language".
- Merge similar preferences. Remove preferences that are clearly contradicted by recent behavior.
- Keep this array concise — aim for 5-10 items maximum.

## 3. `facts` (Key factual knowledge about the user — STRICT 50 ITEM LIMIT)
This is the most critical field. You MUST keep it at or under 50 items. If the current facts plus new ones would exceed 50, you MUST intelligently prune before adding.

### What BELONGS in facts (HIGH VALUE — keep these):
- **Identity & Background**: nationality, passport/citizenship, education, professional credentials.
- **Achievements & Awards**: competition results, certifications, honors, GPA/rankings.
- **Technical Skills & Knowledge**: programming languages, frameworks, tools the user has demonstrated proficiency in.
- **Active Projects**: ongoing development work, research, learning goals the user is actively pursuing.
- **Hardware/Environment**: devices, OS, development environment that affect how the user works.
- **Strong Opinions & Stances**: firmly held technical opinions, design philosophies, tool preferences.
- **Relationship with AI**: how the user views and interacts with the AI assistant (only if it's a stable pattern).

### What does NOT belong in facts (LOW VALUE — remove these first when pruning):
- **One-time debugging events**: "check the bug in one function", "find problem in one line of code" — these are chat_history, not facts.
- **Transient queries**: "query the meaning of one API argument", "use AI to check the code of one filepath" — one-off questions.
- **Minor tool usage**: "using condition flow mode to do something" — unless it reveals a new skill or preference.
- **Redundant details**: if a fact is already covered by a more general fact, remove the specific one.
- **Stale/outdated information**: if the user has clearly moved on from something, remove it.
- **Conversational trivia**: casual remarks, jokes, memes that don't reveal enduring traits.

### Pruning Strategy (when facts exceed 50):
1. **First, remove LOW VALUE items** as defined above — one-time events, transient queries, minor tool usage.
2. **Then, merge similar items**: combine multiple related facts into one concise statement. E.g., "排查了A bug", "排查了B bug", "排查了C bug" → "多次排查LearnAgent框架代码bug".
3. **Then, remove stale items**: facts about things the user has clearly finished or abandoned.
4. **As a last resort**, remove the oldest less-important facts, but NEVER remove identity, achievements, or active project facts.

### Format:
- Each fact MUST be a single, concise sentence in Chinese.
- Each fact MUST describe the USER directly, not the AI or the conversation.
- Do NOT include timestamps or dates within fact strings.

## 4. `chat_history` (Event log — STRICT 50 ITEM LIMIT)
- Each entry format: "YYYY-MM-DD HH:mm, [Brief summary of the conversation/event]".
- **Smart Merging**: If the current conversation continues a topic already in chat_history, update the existing entry's timestamp and summary instead of adding a new one.
- **De-duplication**: If two entries describe essentially the same event, merge them.
- When exceeding 50 items, remove the oldest entries first (FIFO).
- Keep summaries extremely concise — one line each.

## 5. `last_interaction`
- Update with the provided current time string.

---

# Strict Output Constraints
- Output ONLY the raw, valid JSON string.
- NO Markdown formatting (no ```json fences).
- NO greetings, explanations, or any text outside the JSON.
- The JSON must be valid and parseable by Python's json.loads().
- All string values must use double quotes.
"""

UPDATE_USER_PROMPT = """
[Start of Current User Profile]
{user_image_file}
[End of Current User Profile]

[Start of Current Conversation History]
{chat_history}
[End of Current Conversation History]

Time of current conversation: {conversation_time}

Please update the profile based on the conversation history. Remember:
- facts array MUST NOT exceed 50 items. Prune low-value items if needed.
- chat_history array MUST NOT exceed 50 items. Remove oldest if needed.
- Update the summary to reflect the latest understanding of the user.
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

    MAX_FACTS = 50
    MAX_CHAT_HISTORY = 50

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
