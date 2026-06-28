from functions.auto_configuration import weaker_model_configuration
from functions.get_model_response import get_model_response

WEAKER_CONFIG = weaker_model_configuration()
WEAKER_BASE_URL, WEAKER_API_KEY, WEAKER_MODEL_NAME, WEAKER_EXTRA_BODY = WEAKER_CONFIG[0], WEAKER_CONFIG[1], WEAKER_CONFIG[2], WEAKER_CONFIG[3]

BTW_PROMPT = """
Now you are in \"by the way\" mode, your task is to answer a side question accroding to the former messages.
In this mode, you can not use any tools to get external information.
Just make a response to user's temporary question.
The user's question as follows:
"""

def by_the_way(messages:list = [], btw_request:str = ""):
    btw_messages = messages[:]
    btw_messages.append({"role":"user", "content":BTW_PROMPT+btw_request})
    btw_response = get_model_response(
        model_name=WEAKER_MODEL_NAME,
        base_url=WEAKER_BASE_URL,
        api_key=WEAKER_API_KEY,
        extra_body=WEAKER_EXTRA_BODY,
        messages=btw_messages
    ).content
    print(f"\033[32m[Model Response]\033[0m {btw_response}")