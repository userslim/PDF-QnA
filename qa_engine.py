import os
from groq import Groq
from vector_store import VectorStore

class QAEngine:
    def __init__(self, model: str = "mixtral-8x7b-32768"):
        self.model = model
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    def answer(self, question: str, vector_store: VectorStore, top_k: int = 5):
        retrieved = vector_store.retrieve(question, top_k=top_k)
        if not retrieved:
            return "No relevant content found.", []

        # Build context with page/source references
        context_parts = []
        for item in retrieved:
            ref = f"[{item['source']}, page {item['page']}]"
            context_parts.append(f"{ref}\n{item['text']}")
        context = "\n\n".join(context_parts)

        prompt = f"""You are a helpful assistant. Use the following context to answer the question concisely.
If the answer is not in the context, say "I don't have enough information."

Context:
{context}

Question: {question}

Answer:"""

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
        # Return the answer and the full retrieved items (with metadata)
        return answer, retrieved
