"""向量数据库管理 - 使用 ChromaDB"""
import os
import uuid
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings


class VectorStore:
    """向量数据库封装，支持多会话管理"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """初始化向量数据库"""
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embedding_function = self._init_embedding()
    
    def _init_embedding(self):
        """使用本地 embedding 模型（避免 API 费用）"""
        from chromadb.utils import embedding_functions
        # 使用默认的 sentence-transformers 模型
        return embedding_functions.DefaultEmbeddingFunction()
    
    def create_session(self, session_id: str, session_name: str = None) -> str:
        """创建新会话"""
        if session_name is None:
            session_name = f"会话-{session_id[:8]}"
        
        # 为每个会话创建独立的 collection
        try:
            self.client.create_collection(
                name=session_id,
                metadata={"session_name": session_name}
            )
        except ValueError:
            # 已存在
            pass
        
        return session_id
    
    def add_documents(self, session_id: str, chunks: List) -> int:
        """向会话添加文档块"""
        collection = self.client.get_collection(session_id)
        
        # 准备数据
        documents = [chunk.text for chunk in chunks]
        metadatas = [
            {
                "source": chunk.source,
                "page": str(chunk.page) if chunk.page else "N/A",
                "chunk_id": chunk.chunk_id
            }
            for chunk in chunks
        ]
        ids = [chunk.chunk_id for chunk in chunks]
        
        # 添加到 collection
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        return len(documents)
    
    def search(self, session_id: str, query: str, n_results: int = 3) -> List[Dict]:
        """搜索相关文档块"""
        try:
            collection = self.client.get_collection(session_id)
            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # 格式化结果
            formatted_results = []
            if results['documents'] and len(results['documents']) > 0:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        'text': doc,
                        'source': results['metadatas'][0][i].get('source', 'N/A'),
                        'page': results['metadatas'][0][i].get('page', 'N/A'),
                        'chunk_id': results['metadatas'][0][i].get('chunk_id', ''),
                        'distance': results['distances'][0][i] if 'distances' in results else None
                    })
            
            return formatted_results
        except Exception as e:
            print(f"搜索失败: {e}")
            return []
    
    def list_sessions(self) -> List[Dict]:
        """列出所有会话"""
        collections = self.client.list_collections()
        sessions = []
        for col in collections:
            metadata = col.metadata or {}
            sessions.append({
                'id': col.name,
                'name': metadata.get('session_name', col.name[:8])
            })
        return sessions
    
    def delete_session(self, session_id: str):
        """删除会话"""
        try:
            self.client.delete_collection(session_id)
        except Exception as e:
            print(f"删除失败: {e}")
    
    def get_session_info(self, session_id: str) -> Dict:
        """获取会话信息"""
        try:
            collection = self.client.get_collection(session_id)
            count = collection.count()
            metadata = collection.metadata or {}
            return {
                'id': session_id,
                'name': metadata.get('session_name', session_id[:8]),
                'document_count': count
            }
        except Exception as e:
            return {'id': session_id, 'name': session_id[:8], 'document_count': 0}


if __name__ == "__main__":
    # 测试
    vs = VectorStore()
    print("向量数据库初始化成功")