from dotenv import load_dotenv
import os

load_dotenv()

#API_KEY = os.getenv("OPENROUTER_API_KEY")
#BASE_URL = "https://openrouter.ai/api/v1"
#WEAKER_MODEL_NAME = "google/gemma-4-26b-a4b-it"
#STRONGER_MODEL_NAME = "qwen/qwen3-235b-a22b-2507"

API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = "https://api.deepseek.com/"
WEAKER_MODEL_NAME = "deepseek-v4-flash"
WEAKER_EXTRA_BODY = {"thinking": {"type": "disabled"}}
STRONGER_MODEL_NAME = "deepseek-v4-pro"
STRONGER_EXTRA_BODY = {"thinking": {"type": "disabled"}}


def weaker_model_configuration() -> list:
    return [BASE_URL, API_KEY, WEAKER_MODEL_NAME, WEAKER_EXTRA_BODY]

def stronger_model_configuration() -> list:
    return [BASE_URL, API_KEY, STRONGER_MODEL_NAME, STRONGER_EXTRA_BODY]