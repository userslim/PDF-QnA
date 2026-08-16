import os
import google.generativeai as genai
from vector_store import VectorStore

class QAEngine:
    def __init__(self, model: str = "gemini-1.5-flash"):
        """
        Initialize Gemini client.
        Available models: 'gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash-exp'
        """
        self.model_name = model
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Please provide your API key in the sidebar or set it as a secret."
            )
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    def answer(self, question: str, vector_store: VectorStore, top_k: int = 5):
        retrieved = vector_store.retrieve(question, top_k=top_k)
        if not retrieved:
            return "No relevant content found.", []

        # Build context with source references
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

        try:
            # Generate response using Gemini
            response = self.model.generate_content(prompt)
            answer = response.text.strip()
            return answer, retrieved
        except Exception as e:
            return f"Error calling Gemini API: {str(e)}", []
