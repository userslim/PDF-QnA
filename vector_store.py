import chromadb
from sentence_transformers import SentenceTransformer
from typing import List
from document_processor import DocumentChunk

class VectorStore:
    def __init__(self, topic_name: str, persist_dir: str = "./chroma_db"):
        self.topic = topic_name
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection_name = f"topic_{topic_name}"
        # Get or create collection
        try:
            self.collection = self.client.get_collection(self.collection_name)
        except:
            self.collection = self.client.create_collection(self.collection_name)
        self.chunk_ids = []

    def build_index(self, chunks: List[DocumentChunk], chunk_size: int = 1000):
        # Clear and rebuild
        try:
            self.client.delete_collection(self.collection_name)
        except:
            pass
        self.collection = self.client.create_collection(self.collection_name)

        all_texts = []
        metadatas = []
        ids = []
        for chunk in chunks:
            text = chunk.text
            for i in range(0, len(text), chunk_size):
                segment = text[i:i+chunk_size]
                if segment.strip():
                    unique_id = f"{chunk.chunk_id}_{i}"
                    all_texts.append(segment)
                    metadatas.append({
                        "source": chunk.source,
                        "page": str(chunk.page) if chunk.page else "unknown"
                    })
                    ids.append(unique_id)

        if not all_texts:
            return

        embeddings = self.model.encode(all_texts, show_progress_bar=False).tolist()
        self.collection.add(
            embeddings=embeddings,
            documents=all_texts,
            metadatas=metadatas,
            ids=ids
        )

    def retrieve(self, query: str, top_k: int = 5) -> List[DocumentChunk]:
        if self.collection is None:
            return []
        query_embedding = self.model.encode([query]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            include=["documents", "metadatas"]
        )
        retrieved = []
        seen = set()
        docs = results['documents'][0] if results['documents'] else []
        metas = results['metadatas'][0] if results['metadatas'] else []
        for doc, meta in zip(docs, metas):
            key = f"{meta['source']}_{meta['page']}"
            if key not in seen:
                seen.add(key)
                chunk = DocumentChunk(
                    text=doc,
                    source=meta['source'],
                    page=int(meta['page']) if meta['page'].isdigit() else None,
                    chunk_id=key
                )
                retrieved.append(chunk)
        return retrieved
