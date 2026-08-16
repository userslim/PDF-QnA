"""PDF 文档问答应用 - 主界面"""
import streamlit as st
import os
import uuid
from pathlib import Path
from datetime import datetime

from document_processor import DocumentProcessor
from vector_store import VectorStore
from qa_engine import QAEngine
from session_manager import SessionManager
from export import ExportManager

# 页面配置
st.set_page_config(
    page_title="PDF 文档问答助手",
    page_icon="📚",
    layout="wide"
)

# 初始化组件
@st.cache_resource
def init_components():
    """初始化所有组件（仅执行一次）"""
    try:
        processor = DocumentProcessor()
    except Exception as e:
        st.error(f"文档处理器初始化失败: {e}")
        st.info("应用可能部分功能不可用")
        # 创建一个不加载 OCR 的备用实例
        processor = DocumentProcessor.__new__(DocumentProcessor)
        processor.ocr_engine = None
        processor._ocr_loaded = False
    
    try:
        vector_store = VectorStore()
    except Exception as e:
        st.error(f"向量数据库初始化失败: {e}")
        vector_store = None
    
    try:
        qa_engine = QAEngine()
    except Exception as e:
        st.error(f"问答引擎初始化失败: {e}")
        qa_engine = None
    
    try:
        session_manager = SessionManager()
    except Exception as e:
        st.error(f"会话管理器初始化失败: {e}")
        session_manager = None
    
    try:
        export_manager = ExportManager()
    except Exception as e:
        st.error(f"导出管理器初始化失败: {e}")
        export_manager = None
    
    return processor, vector_store, qa_engine, session_manager, export_manager

processor, vector_store, qa_engine, session_manager, export_manager = init_components()

# 侧边栏 - 会话管理
with st.sidebar:
    st.title("📚 文档问答助手")
    st.markdown("---")
    
    # 显示当前 LLM 模式
    mode_display = {
        'ollama': '🖥️ 本地 Ollama',
        'openai': '☁️ OpenAI',
        'groq': '⚡ Groq (免费层)'
    }.get(qa_engine.mode, qa_engine.mode)
    
    st.sidebar.info(f"**LLM 模式**: {mode_display}")
    
    # 检查连接
    if qa_engine.check_connection():
        st.sidebar.success("✓ LLM 服务已连接")
    else:
        if qa_engine.mode == 'ollama':
            st.sidebar.error("✗ Ollama 未运行")
            st.sidebar.info("请启动 Ollama: `ollama serve`")
        else:
            st.sidebar.error("✗ API Key 未配置")
            st.sidebar.info("请在 Secrets 中配置 API Key")
    
    st.markdown("---")
    
    # 创建新会话
    st.subheader("🆕 新建会话")
    new_session_name = st.text_input("会话名称", placeholder="例如：建筑规范研究")
    
    if st.button("创建会话", use_container_width=True):
        if new_session_name:
            new_id = str(uuid.uuid4())
            vector_store.create_session(new_id, new_session_name)
            session_manager.save_session_info(new_id, new_session_name)
            st.session_state.current_session = new_id
            st.success(f"已创建: {new_session_name}")
            st.rerun()
    
    st.markdown("---")
    
    # 现有会话列表
    st.subheader("📁 我的会话")
    sessions = session_manager.list_all_sessions()
    
    if sessions:
        for session in sessions:
            session_id = session['id']
            session_name = session.get('name', session_id[:8])
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(
                    f"📄 {session_name}",
                    key=f"select_{session_id}",
                    use_container_width=True
                ):
                    st.session_state.current_session = session_id
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"delete_{session_id}"):
                    vector_store.delete_session(session_id)
                    session_manager.delete_session(session_id)
                    if st.session_state.get('current_session') == session_id:
                        st.session_state.current_session = None
                    st.rerun()
    else:
        st.info("暂无会话，请创建新会话")

# 主界面
if 'current_session' not in st.session_state or not st.session_state.current_session:
    st.title("📚 欢迎使用文档问答助手")
    st.markdown("""
    ### 功能特性
    - 📤 **多文件上传**：支持 PDF、Word 文档
    - 🔍 **OCR 识别**：自动识别 PDF 中的图片文字
    - 💬 **智能问答**：基于文档内容生成准确回答
    - 📑 **引用来源**：回答标注原文位置
    - 📊 **多会话管理**：不同主题独立管理
    - 💾 **导出功能**：支持 PPT 和 PDF 导出
    
    ### 开始使用
    1. 在左侧创建新会话
    2. 上传 PDF/Word 文件
    3. 等待处理完成
    4. 在下方输入问题
    5. 查看 AI 回答和参考来源
    """)
else:
    # 当前会话
    session_id = st.session_state.current_session
    session_info = session_manager.load_session_info(session_id)
    session_name = session_info.get('name', '未命名') if session_info else '未命名'
    
    st.title(f"📄 {session_name}")
    
    # 文件上传区
    st.subheader("📤 上传文档")
    uploaded_files = st.file_uploader(
        "支持 PDF、Word 文件，可上传多个",
        type=['pdf', 'docx', 'doc'],
        accept_multiple_files=True,
        key=f"upload_{session_id}"
    )
    
    if uploaded_files:
        if st.button("🚀 处理文件", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 保存上传的文件
            upload_dir = Path("./uploads") / session_id
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            file_paths = []
            for i, uploaded_file in enumerate(uploaded_files):
                file_path = upload_dir / uploaded_file.name
                with open(file_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                file_paths.append(str(file_path))
                
                progress = (i + 1) / (len(uploaded_files) * 2)
                progress_bar.progress(progress)
                status_text.text(f"已保存: {uploaded_file.name}")
            
            # 处理文件
            status_text.text("正在解析文档...")
            chunks = processor.process_multiple_files(file_paths)
            
            progress_bar.progress(0.7)
            status_text.text(f"已解析 {len(chunks)} 个文档块，正在建立索引...")
            
            # 添加到向量数据库
            if chunks:
                vector_store.add_documents(session_id, chunks)
                # 更新会话信息
                file_names = [os.path.basename(p) for p in file_paths]
                session_manager.save_session_info(
                    session_id, 
                    session_name, 
                    file_names + session_info.get('files', [])
                )
            
            progress_bar.progress(1.0)
            status_text.text("✅ 处理完成！")
            
            # 获取会话统计
            info = vector_store.get_session_info(session_id)
            st.success(f"✅ 已添加 {len(chunks)} 个文档块到会话")
            st.rerun()
    
    # 显示已上传的文件
    if session_info and session_info.get('files'):
        with st.expander("📂 已上传的文件", expanded=False):
            for file_name in set(session_info['files']):
                st.text(f"📄 {file_name}")
            
            # 会话统计
            info = vector_store.get_session_info(session_id)
            st.markdown(f"**文档块总数**: {info['document_count']}")
    
    st.markdown("---")
    
    # 问答区
    st.subheader("💬 提问")
    
    # 显示问答历史
    qa_history = session_manager.load_qa_history(session_id)
    
    if qa_history:
        st.markdown("### 📜 历史问答")
        for i, qa in enumerate(qa_history, 1):
            with st.expander(f"Q{i}: {qa['question']}", expanded=False):
                st.markdown(f"**回答：**\n\n{qa['answer']}")
                if qa.get('sources'):
                    st.markdown("**参考来源：**")
                    for j, src in enumerate(qa['sources'][:3], 1):
                        st.markdown(f"- [{j}] {src['source']} - 页码 {src['page']}")
        
        st.markdown("---")
        
        # 导出按钮
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("📊 导出 PPT", use_container_width=True):
                output_path = f"./exports/{session_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pptx"
                os.makedirs("./exports", exist_ok=True)
                export_manager.export_to_ppt(session_name, qa_history, output_path)
                with open(output_path, 'rb') as f:
                    st.download_button(
                        "⬇️ 下载 PPT",
                        f,
                        file_name=os.path.basename(output_path),
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                    )
        
        with col2:
            if st.button("📄 导出 PDF", use_container_width=True):
                output_path = f"./exports/{session_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                os.makedirs("./exports", exist_ok=True)
                export_manager.export_to_pdf(session_name, qa_history, output_path)
                with open(output_path, 'rb') as f:
                    st.download_button(
                        "⬇️ 下载 PDF",
                        f,
                        file_name=os.path.basename(output_path),
                        mime="application/pdf"
                    )
    
    # 输入新问题
    question = st.text_area(
        "输入您的问题",
        placeholder="例如：这份文档的主要观点是什么？",
        height=100,
        key=f"question_{session_id}"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🚀 提问", use_container_width=True):
            if question.strip():
                # 检查会话是否有文档
                info = vector_store.get_session_info(session_id)
                if info['document_count'] == 0:
                    st.warning("⚠️ 请先上传并处理文档")
                else:
                    with st.spinner("🔍 正在搜索相关内容..."):
                        # 搜索相关文档块
                        chunks = vector_store.search(session_id, question, n_results=3)
                        
                        with st.spinner("🤖 AI 正在生成回答..."):
                            # 生成回答
                            result = qa_engine.answer_question(question, chunks)
                            
                            # 保存到历史
                            qa_history.append({
                                'question': question,
                                'answer': result['answer'],
                                'sources': result['sources'],
                                'timestamp': datetime.now().isoformat()
                            })
                            session_manager.save_qa_history(session_id, qa_history)
                            
                            # 显示回答
                            st.markdown("### 💡 回答")
                            st.markdown(result['answer'])
                            
                            if result['sources']:
                                st.markdown("### 📚 参考来源")
                                for i, source in enumerate(result['sources'], 1):
                                    st.markdown(f"**[{i}]** {source['source']} - 页码 {source['page']}")
                                    with st.expander(f"查看原文片段 {i}"):
                                        st.text(source['text'])
                            
                            st.rerun()
            else:
                st.warning("请输入问题")

# 页脚
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>🔒 完全本地运行 · 数据不上传 · 免费使用</p>
    <p>Powered by Ollama + LangChain + Streamlit</p>
</div>
""", unsafe_allow_html=True)