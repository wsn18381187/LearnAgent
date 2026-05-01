import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("TAVILY_API_KEY")
ATTEMPT_TIME = 4

def search_web(query: str) -> str:
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": API_KEY,
        "query": query,
        "max_results": 5
    }
    for attemp in range(ATTEMPT_TIME+1):
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            res = response.json()
            results = []
            for r in res.get("results", []):
                results.append(f"{r['title']}: {r['content']}")

            return "\n".join(results) if results else "No related result found."
        except Exception as e:
            if attemp == ATTEMPT_TIME:
                raise RuntimeError(f"Search fail after {ATTEMPT_TIME} times of retries.")
            print(f"[Request Info] Search failed, retry the {attemp+1} time after a while...")
            time.sleep(3)

SEARCH_WEB_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "search_web",
        "description": "Search the web for up-to-date information.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Keywords or key content that need to be searched online."
                }
            },
            "required": ["query"],
        },
    },
}