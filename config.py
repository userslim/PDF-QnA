"""配置文件 - 支持本地 Ollama 和云端 API (OpenAI/Groq)"""
import os
from typing import Optional


class Config:
    """应用配置"""
    
    # LLM 模式: "ollama" (本地) / "openai" / "groq" (云端)
    LLM_MODE = os.getenv("LLM_MODE", "ollama")
    
    # Ollama 配置（本地模式）
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    
    # OpenAI 配置（云端模式）
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Groq 配置（云端模式，免费层）
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    
    # 向量数据库
    VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./chroma_db")
    
    # 文件存储
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
    SESSION_DIR = os.getenv("SESSION_DIR", "./sessions")
    EXPORT_DIR = os.getenv("EXPORT_DIR", "./exports")
    
    # OCR 配置
    ENABLE_OCR = os.getenv("ENABLE_OCR", "true").lower() == "true"
    
    # 应用信息
    APP_NAME = "PDF 文档问答助手"
    APP_VERSION = "1.0.0"
    
    @classmethod
    def is_cloud_deployment(cls) -> bool:
        """检测是否为云端部署"""
        return cls.LLM_MODE in ["openai", "groq"]


def get_config() -> Config:
    """获取配置"""
    return Config()