import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer
import faiss
from document_processor import DocumentChunk


class VectorStore:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.chunks = []  # store original chunks with metadata

    def build_index(self, chunks: List[DocumentChunk], chunk_size: int = 1000):
        """Split chunks into smaller pieces, embed, and build FAISS index."""
        self.chunks = []
        all_texts = []
        
        for chunk in chunks:
            # Split long text into overlapping segments
            text = chunk.text
            for i in range(0, len(text), chunk_size):
                segment = text[i:i+chunk_size]
                if segment.strip():
                    # Create a new chunk object with same metadata
                    new_chunk = DocumentChunk(
                        text=segment,
                        source=chunk.source,
                        page=chunk.page,
                        chunk_id=f"{chunk.chunk_id}_{i}"
                    )
                    self.chunks.append(new_chunk)
                    all_texts.append(segment)
        
        if not all_texts:
            return
        
        # Generate embeddings
        embeddings = self.model.encode(all_texts, show_progress_bar=False)
        embeddings = np.array(embeddings).astype('float32')
        
        # Build FAISS index
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(embeddings)

    def retrieve(self, query: str, top_k: int = 5) -> List[DocumentChunk]:
        """Retrieve top-k most similar chunks."""
        if self.index is None or self.index.ntotal == 0:
            return []
        
        query_embedding = self.model.encode([query]).astype('float32')
        distances, indices = self.index.search(query_embedding, top_k)
        
        # Get unique chunks (by chunk_id) to avoid duplicates
        seen = set()
        results = []
        for idx in indices[0]:
            if idx < len(self.chunks):
                chunk = self.chunks[idx]
                if chunk.chunk_id not in seen:
                    seen.add(chunk.chunk_id)
                    results.append(chunk)
        return results
