import chromadb
import uuid

class ChatHistoryManager:
    def __init__(self, db_path="chromadbtest/db", collection_name="testdb"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_record(self, text_content:str, embedding: list[float], record_id:str=None, session_id:str="default"):
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
        return record_id
    
    def search_similar_history(self, query_embedding: list[float], top_n:int=3, session_id:str=None):
        where_filter = {"session_id":session_id} if session_id else None
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results = top_n,
            where=where_filter
        )
        return results

if __name__ == "__main__":
    # 实例化管理器（会自动在当前目录下创建文件夹存放数据库）
    history_manager = ChatHistoryManager()
    
    # 假设这是你从 OpenAI API 或者其他模型获取到的 embedding 向量（仅作演示，实际长度通常为 1536 等）
    mock_embedding_1 =[0.1, 0.2, 0.3, 0.4, 0.5]
    mock_embedding_2 =[0.9, 0.8, 0.7, 0.6, 0.5]
    mock_embedding_query =[0.15, 0.22, 0.28, 0.41, 0.49] 
    
    # --- 添加对话历史记录 ---
    history_manager.add_record(
        text_content="请问北京明天的天气怎么样？",
        embedding=mock_embedding_1,
        #role="user",
        session_id="session_001"
    )
    
    history_manager.add_record(
        text_content="北京明天晴天，气温15到25度。",
        embedding=mock_embedding_2,
        #role="assistant",
        session_id="session_001"
    )
    print("历史记录添加成功！\n")
    
    # --- 根据 embedding 搜索 Top 2 历史记录 ---
    print("正在搜索相关历史记录...")
    search_results = history_manager.search_similar_history(
        query_embedding=mock_embedding_query,
        top_n=2
    )
    
    # --- 解析检索结果 ---
    # ChromaDB 的查询结果返回的是一个包含列表的字典，需要遍历提取（因为你可以一次传入多个 query_embedding）
    if search_results and search_results['documents']:
        # [0] 是因为我们只传了一个 query_embedding
        documents = search_results['documents'][0]
        metadatas = search_results['metadatas'][0]
        distances = search_results['distances'][0] # 距离越小通常越相关（默认 L2 距离）
        
        print(f"搜索到 {len(documents)} 条相关记录：")
        for i in range(len(documents)):
            print(f"[{i+1}] 相似度距离: {distances[i]:.4f}")
            # 这里的 metadatas[i]['role'] 和 documents[i] 就可以直接被你用其他函数拼装成 OpenAI 的字典格式
            #print(f"    Role: {metadatas[i]['role']}") 
            print(f"    Content: {documents[i]}")
            print("-" * 30)