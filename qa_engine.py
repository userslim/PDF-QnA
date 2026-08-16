import os
from groq import Groq
from vector_store import VectorStore


class QAEngine:
    def __init__(self, model: str = "mixtral-8x7b-32768"):
        self.model = model
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    def answer(self, question: str, vector_store: VectorStore, top_k: int = 5):
        """Retrieve relevant chunks and generate an answer."""
        # Retrieve
        chunks = vector_store.retrieve(question, top_k=top_k)
        if not chunks:
            return "No relevant content found in the document.", []
        
        # Build context
        context = "\n\n".join([chunk.text for chunk in chunks])
        sources = [chunk.text for chunk in chunks]
        
        # Build prompt
        prompt = f"""You are a helpful assistant. Use the following context to answer the question concisely.
If the answer is not in the context, say "I don't have enough information."

Context:
{context}

Question: {question}

Answer:"""
        
        # Call Groq
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a document Q&A assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=512,
        )
        answer = response.choices[0].message.content
        return answer, sources
