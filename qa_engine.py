"""问答引擎 - 支持本地 Ollama 和云端 OpenAI"""
import os
import requests
import json
from typing import List, Dict, Optional
from config import get_config


class QAEngine:
    """问答引擎，支持多种 LLM 后端 (Ollama/OpenAI/Groq)"""
    
    def __init__(self):
        self.config = get_config()
        self.mode = self.config.LLM_MODE
        
        if self.mode == "ollama":
            self.base_url = self.config.OLLAMA_BASE_URL
            self.model = self.config.OLLAMA_MODEL
            self.api_url = f"{self.base_url}/v1/chat/completions"
        elif self.mode == "openai":
            self.api_key = self._get_api_key("openai")
            self.model = self.config.OPENAI_MODEL
            self.api_url = "https://api.openai.com/v1/chat/completions"
        elif self.mode == "groq":
            self.api_key = self._get_api_key("groq")
            self.model = self.config.GROQ_MODEL
            self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        else:
            raise ValueError(f"不支持的 LLM 模式: {self.mode}")
    
    def _get_api_key(self, provider: str) -> str:
        """从 Streamlit Secrets 或环境变量获取 API Key"""
        # 尝试 Streamlit Secrets
        try:
            import streamlit as st
            if hasattr(st, 'secrets'):
                if provider == "openai" and 'OPENAI_API_KEY' in st.secrets:
                    return st.secrets['OPENAI_API_KEY']
                if provider == "groq" and 'GROQ_API_KEY' in st.secrets:
                    return st.secrets['GROQ_API_KEY']
        except:
            pass
        
        # 尝试环境变量
        if provider == "openai":
            key = os.getenv("OPENAI_API_KEY")
        elif provider == "groq":
            key = os.getenv("GROQ_API_KEY")
        else:
            key = None
        
        if key:
            return key
        
        raise ValueError(f"未配置 {provider.upper()} API Key")
    
    def check_connection(self) -> bool:
        """检查 LLM 服务是否可用"""
        if self.mode == "ollama":
            try:
                response = requests.get(f"{self.base_url}/api/tags", timeout=3)
                return response.status_code == 200
            except:
                return False
        elif self.mode in ["openai", "groq"]:
            return bool(self.api_key)
        return False
    
    def answer_question(
        self,
        question: str,
        context_chunks: List[Dict],
        language: str = "zh"
    ) -> Dict:
        """基于上下文回答问题"""
        if not context_chunks:
            return {
                'answer': '抱歉，没有找到相关文档内容。请确认已上传文件。',
                'sources': []
            }
        
        context_text = "\n\n".join([
            f"[文档 {i+1}] 来源: {chunk['source']}, 页码: {chunk['page']}\n{chunk['text']}"
            for i, chunk in enumerate(context_chunks)
        ])
        
        system_prompt = """你是一个专业的文档分析助手。请根据用户提供的文档内容回答问题。

要求：
1. 只使用提供的文档内容回答，不要编造信息
2. 回答要清晰、准确、有条理
3. 在回答中标注信息来源（哪个文档、哪一页）
4. 如果文档中没有相关信息，明确告知用户
5. 用用户提问的语言回答"""
        
        if language == "en":
            system_prompt = """You are a professional document analysis assistant. Answer questions based on the provided documents.

Requirements:
1. Only use the provided documents, do not make up information
2. Be clear, accurate, and organized
3. Cite sources (which document, which page)
4. If no relevant info, tell the user clearly
5. Answer in the user's language"""
        
        user_prompt = f"""参考以下文档内容：

{context_text}

用户问题：{question}

请提供详细的回答，并在适当的地方标注信息来源。"""
        
        # 根据模式调用不同 API
        if self.mode == "ollama":
            return self._call_ollama(system_prompt, user_prompt, context_chunks)
        elif self.mode in ["openai", "groq"]:
            return self._call_cloud_api(system_prompt, user_prompt, context_chunks)
    
    def _call_ollama(self, system_prompt: str, user_prompt: str, context_chunks: List[Dict]) -> Dict:
        """调用 Ollama API"""
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content']
                return {'answer': answer, 'sources': context_chunks}
            else:
                return {
                    'answer': f'⚠️ Ollama 调用失败: {response.status_code}\n\n请确认 Ollama 正在运行：\n```\nollama serve\n```',
                    'sources': context_chunks
                }
        except requests.exceptions.ConnectionError:
            return {
                'answer': '⚠️ 无法连接到 Ollama 服务\n\n请在终端运行：\n```\nollama serve\n```',
                'sources': context_chunks
            }
        except Exception as e:
            return {
                'answer': f'⚠️ 错误: {str(e)}',
                'sources': context_chunks
            }
    
    def _call_cloud_api(self, system_prompt: str, user_prompt: str, context_chunks: List[Dict]) -> Dict:
        """调用云端 API（OpenAI 或 Groq，都使用 OpenAI 兼容格式）"""
        provider_name = "Groq" if self.mode == "groq" else "OpenAI"
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content']
                return {'answer': answer, 'sources': context_chunks}
            else:
                return {
                    'answer': f'⚠️ {provider_name} API 错误: {response.status_code} - {response.text[:200]}',
                    'sources': context_chunks
                }
        except Exception as e:
            return {
                'answer': f'⚠️ 错误: {str(e)}',
                'sources': context_chunks
            }
    
    def summarize_documents(self, context_chunks: List[Dict], language: str = "zh") -> Dict:
        """总结文档内容"""
        if not context_chunks:
            return {'summary': '没有可总结的内容。', 'sources': []}
        
        context_text = "\n\n".join([
            f"[文档 {i+1}] 来源: {chunk['source']}, 页码: {chunk['page']}\n{chunk['text']}"
            for i, chunk in enumerate(context_chunks)
        ])
        
        system_prompt = "你是一个专业的文档总结助手。请基于用户提供的内容生成清晰、有条理的总结，包含主要观点和关键信息。"
        
        user_prompt = f"""请总结以下文档内容：

{context_text}

要求：
1. 提取主要观点和关键信息
2. 使用结构化的格式（分点或分段）
3. 标注信息来源（文档名和页码）
4. 总结长度适中，保留重要细节"""
        
        if self.mode == "ollama":
            return self._call_ollama_summarize(system_prompt, user_prompt, context_chunks)
        else:
            return self._call_cloud_api_summarize(system_prompt, user_prompt, context_chunks)
    
    def _call_ollama_summarize(self, system_prompt, user_prompt, context_chunks):
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 3000
                },
                timeout=120
            )
            if response.status_code == 200:
                summary = response.json()['choices'][0]['message']['content']
                return {'summary': summary, 'sources': context_chunks}
            return {'summary': f'API 调用失败: {response.status_code}', 'sources': context_chunks}
        except Exception as e:
            return {'summary': f'错误: {str(e)}', 'sources': context_chunks}
    
    def _call_cloud_api_summarize(self, system_prompt, user_prompt, context_chunks):
        provider_name = "Groq" if self.mode == "groq" else "OpenAI"
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 3000
                },
                timeout=60
            )
            if response.status_code == 200:
                summary = response.json()['choices'][0]['message']['content']
                return {'summary': summary, 'sources': context_chunks}
            return {'summary': f'{provider_name} API 错误: {response.status_code}', 'sources': context_chunks}
        except Exception as e:
            return {'summary': f'错误: {str(e)}', 'sources': context_chunks}


if __name__ == "__main__":
    engine = QAEngine()
    print(f"LLM 模式: {engine.mode}")
    print(f"连接状态: {'✓ 正常' if engine.check_connection() else '✗ 失败'}")