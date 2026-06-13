import os
import sys
import json
from datetime import datetime
from functions.judge_which_model import judge_difficulty
from core.flow_entrance import flow_entrance
from functions.user_image import update_user_image, provide_user_image
from functions.auto_history_embedding import auto_history_embedding
from functions.auto_configuration import show_current_config, set_config, validate_config

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

    if not validate_config():
        print("\033[33m[System] Entering config setup mode...\033[0m")
        set_config()
        if not validate_config():
            print("\033[31m[Error] Configuration still incomplete. Exiting.\033[0m")
            sys.exit(1)
    # Initialization of history chat file
    os.makedirs("history", exist_ok=True)
    filename = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join("history", f"chat_{filename}.json")

    # Initial save of the system prompt message
    messages = [{"role":"system", "content":SYSTEM_PROMPT_TEMPLATE.format(user_image=provide_user_image())}]
    try:
        user_request = input("\033[34mwhat can I do 4 u: \033[0m").strip()
        while True:
            if user_request == "/help" or user_request == "/?" or user_request == "/":
                print("\033[90m/config           --check or change configs")
                print("\033[90m/clear            --clear and save current conversation, then start a new one\033[0m")
                print("\033[90m/exit             --save conversation and exit the agent\033[0m")
                print("\033[90m/help or /?       --check for all available commands\033[0m")
                user_request = input("\033[34m>\033[0m ").strip()
                continue
            elif user_request == "/config":
                print(f"\033[90m/config-check    --check current configs\033[0m")
                print(f"\033[90m/config-set      --change config settings\033[0m")
                print(f"\033[90m/back            --go back and continue to chat\033[0m")
                user_request = input("\033[34m>\033[0m ").strip()
                if user_request == "/config-check":
                    show_current_config()
                elif user_request == "/config-set":
                    set_config()
                    if validate_config():
                        print("\033[32m[System] All configs are now complete. Ready to chat!\033[0m")
                    else:
                        print("\033[33m[System] Some configs are still missing. You can use /config-set again.\033[0m")
                elif user_request == "/back":
                    print("[Info] Back to chat.")
                else:
                    print("[Info] Undefined command. Back to chat.")
                user_request = input("\033[34mwhat can I do 4 u: \033[0m")
                continue
            elif user_request == "/exit":
                break
            elif user_request == "/clear":
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
            # ---- CHANGED: router only judges difficulty, flow_entrance handles the rest ----
            difficulty = judge_difficulty(messages)
            response = flow_entrance(
                difficulty=difficulty,
                messages=messages,
                max_tokens=20000 if difficulty in ("COMPLEX", "EXTREME") else 2000,
            )
            response_content = response.content if hasattr(response, 'content') else str(response)
            messages.append({"role":"assistant", "content":response_content})
            user_request = input("\033[34mAny other questions: \033[0m")
    except KeyboardInterrupt:
        print("\n\033[33m[System] Interrupted by user (Ctrl+C).\033[0m")
    finally:
        if len(messages) > 1:
            print("\033[32m[System] Updating user image...\033[0m")
            update_user_image(messages)
            print("\033[32m[System] Updating database...\033[0m")
            save_chat_history(filepath, messages)
            auto_history_embedding(filepath)
        print("\033[32mBye bye meow~\033[0m")
