import os

# API keys (load from environment or secrets)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
DEFAULT_MODEL = "mixtral-8x7b-32768"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # from sentence-transformers
CHUNK_SIZE = 1000
TOP_K = 5
