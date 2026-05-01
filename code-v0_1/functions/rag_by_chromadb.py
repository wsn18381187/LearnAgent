import chromadb
import uuid

DB_PATH = "chromaDB"
COLLECTION_NAME = "chat_history"

class ChatHistoryManager:
    def __init__(self, db_path=DB_PATH, collection_name=COLLECTION_NAME):
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_record(self, 
                   text_content:str, 
                   embedding:list[float], 
                   record_id:str=None, 
                   session_id:str="default"):
        if not record_id:
            record_id = str(uuid.uuid4())
        
        metadata = {
            "session_id":session_id
        }

        self.collection.add(
            documents=[text_content],
            embeddings=[embedding],
            metadatas=[metadata],
            ids=[record_id]
        )
    
    def search_similar_history(self, 
                               query_embedding:list[float], 
                               top_n:int=3, 
                               session_id:str=None):
        where_filter = {"session_id":session_id} if session_id else None
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_n,
            where=where_filter
        )
        return results