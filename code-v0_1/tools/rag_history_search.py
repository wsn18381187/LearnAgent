from functions.rag_by_chromadb import ChatHistoryManager
from functions.get_embedding import get_embedding
from functions.auto_configuration import weaker_model_configuration
from functions.get_model_response import get_model_response

history_manager = ChatHistoryManager()

CONFIG = weaker_model_configuration()
BASE_URL, API_KEY, MODEL_NAME, EXTRA_BODY = CONFIG[0], CONFIG[1], CONFIG[2], CONFIG[3]

COMPRESS_SYSTEM_PROMPT = """
# Role
You are a "Memory Extraction Specialist." Your goal is to analyze retrieved historical conversation snippets and extract specific facts, user preferences, or past decisions relevant to a search query.

# Context
The provided snippets are retrieved via vector search and may contain:
1. Redundancy: Multiple snippets repeating the same information.
2. Noise: Irrelevant small talk or outdated instructions.
3. Fragmentation: Missing context due to chunking.

# Instructions
1. **Relevance First**: Extract ONLY information directly related to the [Search Query]. Ignore everything else.
2. **Deduplicate & Consolidate**: If multiple snippets mention the same fact, merge them into a single concise point. Do not list duplicates.
3. **Conflict Resolution**: If snippets contain conflicting information (e.g., the user changed their mind), prioritize the most recent information based on timestamps or logical flow, and note the change if necessary.
4. **Objective Summary**: Write in the third person. Use a neutral, factual tone. Do not add your own interpretations or "hallucinate" details not present in the text.
5. **Precision**: Keep specific values, configurations, dates, and names exactly as they appear in the history.

# Output Format
- If relevant info is found: Use a concise bullet-point list (" - ").
- If NO relevant info is found: Reply ONLY with "No relevant historical records found."
- DO NOT use conversational fillers like "Based on the history..." or "I found the following...".

# Example Output
- User prefers Python 3.10 for backend development.
- Project deadline was set to 2024-12-01 in previous discussions.
- User previously rejected the AWS Lambda approach due to cold start concerns.
"""

COMPRESS_USER_PROMPT = """
[Start of Search Query]
{query}
[End of Search Query]

[Start of Retrieved Conversation Snippets]
{retrieved_conversation}
[End of Retrieved Conversation Snippets]

Based on the provided snippets, extract and summarize all information relevant to the search query. Follow the system instructions strictly.
"""

def rag_history_search(query:str) -> str:
    query_embedding = get_embedding(query)
    search_result = history_manager.search_similar_history(
        query_embedding=query_embedding,
        top_n=5
    )
    if search_result and search_result['documents']:
        print(f"[System] Found {len(search_result['documents'])} related chat history.")
        compress_result = get_model_response(model_name=MODEL_NAME,
                                             base_url=BASE_URL,
                                             api_key=API_KEY,
                                             user_prompt=COMPRESS_USER_PROMPT.format(
                                                 query=query,
                                                 retrieved_conversation=str(search_result['documents'])
                                             ),
                                             system_prompt=COMPRESS_SYSTEM_PROMPT,
                                             extra_body=EXTRA_BODY).content
        print(f"[System] Found related chat history: {compress_result}")
        return compress_result
    else:
        print("[System] No related chat history found.")
        return "No related chat history found."

RAG_HISTORY_SEARCH_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "rag_history_search",
        "description": "Search information in past conversations that may be related to the current conversation.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Keywords or key information from the current conversation that may need to be searched from the history of conversations."
                }
            },
            "required": ["query"],
        },
    },
}