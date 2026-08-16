"""会话管理 - 存储和管理用户的问答历史"""
import json
import os
from pathlib import Path
from typing import List, Dict
from datetime import datetime


class SessionManager:
    """管理会话元数据和问答历史"""
    
    def __init__(self, sessions_dir: str = "./sessions"):
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)
    
    def save_session_info(self, session_id: str, name: str, files: List[str] = None):
        """保存会话基本信息"""
        info_path = self.sessions_dir / f"{session_id}.json"
        info = {
            'id': session_id,
            'name': name,
            'created_at': datetime.now().isoformat(),
            'files': files or []
        }
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
    
    def load_session_info(self, session_id: str) -> Dict:
        """加载会话信息"""
        info_path = self.sessions_dir / f"{session_id}.json"
        if info_path.exists():
            with open(info_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def save_qa_history(self, session_id: str, qa_list: List[Dict]):
        """保存问答历史"""
        history_path = self.sessions_dir / f"{session_id}_history.json"
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(qa_list, f, ensure_ascii=False, indent=2)
    
    def load_qa_history(self, session_id: str) -> List[Dict]:
        """加载问答历史"""
        history_path = self.sessions_dir / f"{session_id}_history.json"
        if history_path.exists():
            with open(history_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def delete_session(self, session_id: str):
        """删除会话所有文件"""
        for pattern in [f"{session_id}.json", f"{session_id}_history.json"]:
            path = self.sessions_dir / pattern
            if path.exists():
                path.unlink()
    
    def list_all_sessions(self) -> List[Dict]:
        """列出所有会话"""
        sessions = []
        for info_file in self.sessions_dir.glob("*.json"):
            if not info_file.name.endswith("_history.json"):
                with open(info_file, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                    sessions.append(info)
        return sorted(sessions, key=lambda x: x.get('created_at', ''), reverse=True)


if __name__ == "__main__":
    sm = SessionManager()
    print("会话管理器初始化成功")