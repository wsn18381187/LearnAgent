from openai import OpenAI
from dotenv import load_dotenv
import time
import os

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
ATTEMP_TIME = 3

def get_embedding(input_content:str, attemp_time:int=ATTEMP_TIME) -> list[float]:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=API_KEY)
    for attemp in range(attemp_time+1):
        try:
            embedding = client.embeddings.create(
                model = "perplexity/pplx-embed-v1-0.6b",
                input = input_content,
                encoding_format = "float"
            )
            return embedding.data[0].embedding
        except Exception as e:
            if attemp == attemp_time:
                raise RuntimeError(f"[Request Info] Embedding failed after {attemp_time} times. {e}")
            print(f"[Request Info]: Request failed, retry the {attemp+1} time in 1 seconds...")
            time.sleep(1)