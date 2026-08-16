# 📚 PDF 文档问答助手

基于 AI 的文档问答应用，支持多文件上传、多会话管理、OCR 识别、引用来源和 PPT/PDF 导出。

## ✨ 功能特性

- 📤 **多文件上传**：支持 PDF、Word 文档
- 🔍 **OCR 识别**：自动识别 PDF 中的图片文字
- 💬 **智能问答**：基于本地或云端 LLM 生成准确回答
- 📑 **引用来源**：回答标注原文位置（文档名 + 页码）
- 📊 **多会话管理**：不同主题独立管理
- 💾 **导出功能**：支持 PPT 和 PDF 导出
- 🔒 **数据隐私**：可完全本地运行，文档不上传

## 🏗️ 技术架构

```
Streamlit (前端)
    ↓
LangChain (RAG 框架)
    ↓
ChromaDB (向量数据库)
    ↓
Ollama / OpenAI (LLM)
```

## 🚀 快速开始

### 方案 1：本地运行（推荐，完全免费）

#### 前置要求
- Python 3.11+
- Ollama + Llama 3.1 8B 模型

#### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/pdf-qa-app.git
cd pdf-qa-app

# 2. 安装依赖
pip install -r requirements.txt

# 3. 确认 Ollama 正在运行
ollama serve

# 4. 启动应用
streamlit run app.py
```

应用将在 http://localhost:8501 启动

### 方案 2：部署到 Streamlit Cloud（云端访问）

#### 部署步骤

1. **上传代码到 GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/your-username/pdf-qa-app.git
   git push -u origin main
   ```

2. **访问 [share.streamlit.io](https://share.streamlit.io)**

3. **点击 "New app"**

4. **填写配置**：
   - Repository: `your-username/pdf-qa-app`
   - Branch: `main`
   - Main file path: `app.py`

5. **配置 Secrets（高级设置）**：
   
   **选项 A：使用 Groq（推荐，免费层）**
   ```toml
   LLM_MODE = "groq"
   GROQ_API_KEY = "gsk_..."
   GROQ_MODEL = "llama-3.1-8b-instant"
   ```
   
   **选项 B：使用 OpenAI**
   ```toml
   LLM_MODE = "openai"
   OPENAI_API_KEY = "sk-..."
   OPENAI_MODEL = "gpt-4o-mini"
   ```

6. **点击 Deploy**

部署完成后，你将获得一个公网 URL，可以在任何设备访问。

## 🔧 配置说明

### 本地模式（默认）
应用使用本地 Ollama，无需 API Key，完全免费。

### 云端模式
设置 `LLM_MODE=openai` 并配置 `OPENAI_API_KEY`。

## 📦 项目结构

```
pdf_qa_app/
├── app.py                  # Streamlit 主界面
├── document_processor.py   # PDF/Word/OCR 处理
├── vector_store.py         # ChromaDB 向量数据库
├── qa_engine.py            # LLM 问答引擎（Ollama/OpenAI）
├── session_manager.py      # 会话管理
├── export.py               # PPT/PDF 导出
├── config.py               # 配置文件
├── requirements.txt        # Python 依赖
├── packages.txt            # 系统依赖（用于 OCR）
├── .gitignore              # Git 忽略文件
└── README.md               # 本文件
```

## 🛠️ 依赖说明

- **Streamlit**：Web 界面
- **LangChain**：RAG 框架
- **ChromaDB**：向量数据库
- **Ollama**：本地 LLM 推理
- **PyMuPDF + pdfplumber**：PDF 解析
- **python-docx**：Word 文档解析
- **PaddleOCR**：图片文字识别（可选）
- **python-pptx + reportlab**：PPT/PDF 生成

## 📝 使用流程

1. **创建会话**：在左侧栏输入名称创建新会话
2. **上传文档**：支持多个 PDF/Word 文件
3. **处理文档**：自动解析、OCR、向量化
4. **提问**：在主界面输入问题
5. **查看答案**：AI 基于文档内容回答，标注来源
6. **导出**：将问答记录导出为 PPT 或 PDF

## ⚠️ 注意事项

- **本地运行**：OCR（PaddleOCR）首次使用时会下载模型，可能需要几分钟
- **云端部署**：Streamlit Cloud 免费层资源有限，OCR 可能因超时而失败
- **数据存储**：云端部署每次重启会清空数据，建议下载重要问答
- **隐私保护**：本地模式下所有数据仅存储在你电脑，不会上传到云端

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！