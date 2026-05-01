from functions.rag_by_chromadb import ChatHistoryManager
from functions.get_embedding import get_embedding
from pathlib import Path
import json

history_manager = ChatHistoryManager()

def auto_history_embedding(file_path:str, chunk_len:int=3):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    session_id = Path(file_path).stem
    filtered_data = [item for item in data if item["role"] in ["user", "assistant"] and item.get("content")]
    if len(filtered_data) >= chunk_len*2:
        window_size = chunk_len*2
        max_start = len(filtered_data) - window_size
        for i in range(0, max_start+1, 2):
            text_content = ""
            for j in range(chunk_len):
                text_content += f"{filtered_data[i+j]['role']}:{filtered_data[i+j]['content']}\n"
            embedding = get_embedding(input_content=text_content)
            history_manager.add_record(
                text_content=text_content,
                embedding=embedding,
                session_id=session_id
            )
    else:
        text_content = ""
        for i in range(len(filtered_data)):
            text_content += f"{filtered_data[i]['role']}:{filtered_data[i]['content']}\n"
        embedding = get_embedding(input_content=text_content)
        history_manager.add_record(
            text_content=text_content,
            embedding=embedding,
            session_id=session_id
        )