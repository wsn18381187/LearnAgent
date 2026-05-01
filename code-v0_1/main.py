import os
import json
from datetime import datetime
from functions.judge_which_model import judge_which_model
from functions.user_image import update_user_image, provide_user_image
from functions.auto_history_embedding import auto_history_embedding

SYSTEM_PROMPT_TEMPLATE = """
You are LearnAgent, an intelligent and highly configurable AI agent framework developed by GitHub user wsn18381187.
You are capable of operating on various underlying LLMs and seamlessly invoking a wide range of external tools.
Your primary role is to accurately understand user instructions, logically select and use the provided tools, and efficiently complete the assigned tasks.
Since your character is a cat, you should add the interjection "meow~" after each paragraph of your answer.

In addition, you have access to a User Profile.
You should analyze this profile to provide personalized, context-aware responses that align with the user's preferences, habits, and background.

[Start of User Profile]
{user_image}
[End of User Profile]
"""

def save_chat_history(path, messages):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    print("\033[32mWelcome to use LearnAgent!\033[0m")
    # Initialization of history chat file
    os.makedirs("history", exist_ok=True)
    filename = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join("history", f"chat_{filename}.json")

    # Initial save of the system prompt message
    messages = [{"role":"system", "content":SYSTEM_PROMPT_TEMPLATE.format(user_image=provide_user_image())}]
    try:
        user_request = input("\033[34mwhat can I do 4 u: \033[0m").strip()
        while True:
            if user_request == "exit":
                break
            elif user_request == "clear":
                print("\033[32m[System] Updating user image...\033[0m")
                update_user_image(messages)
                print("\033[32m[System] Updating database...\033[0m")
                save_chat_history(filepath, messages)
                auto_history_embedding(filepath)
                print("\033[32mChat history saved and new session started~\033[0m")
                
                filename = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = os.path.join("history", f"chat_{filename}.json")
                messages = [{"role":"system", "content":SYSTEM_PROMPT_TEMPLATE.format(user_image=provide_user_image())}]
                user_request = input("\033[34mwhat can I do 4 u: \033[0m")
                continue

            messages.append({"role":"user", "content":user_request})
            response_content = judge_which_model(messages)
            messages.append({"role":"assistant", "content":response_content})
            user_request = input("\033[34mAny other questions: \033[0m")
    except KeyboardInterrupt:
        print("\n\033[33m[System] Interrupted by user (Ctrl+C).\033[0m")
    finally:
        print("\033[32m[System] Updating user image...\033[0m")
        update_user_image(messages)
        print("\033[32m[System] Updating database...\033[0m")
        save_chat_history(filepath, messages)
        auto_history_embedding(filepath)
        print("\033[32mBye bye meow~\033[0m")