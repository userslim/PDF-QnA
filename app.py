import streamlit as st
import os
import tempfile
from pathlib import Path
from document_processor import DocumentProcessor
from vector_store import VectorStore
from qa_engine import QAEngine

st.set_page_config(page_title="Multi‑Topic PDF/Word Q&A", layout="wide")
st.title("📄 Multi‑Topic PDF/Word Q&A with Groq")

# --- Session state init ---
if "topics" not in st.session_state:
    st.session_state.topics = {}
if "topic_chunks" not in st.session_state:
    st.session_state.topic_chunks = {}
if "current_topic" not in st.session_state:
    st.session_state.current_topic = None
if "groq_api_key" not in st.session_state:
    st.session_state.groq_api_key = ""

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input("Groq API Key", type="password",
                            value=st.session_state.groq_api_key)
    if api_key:
        st.session_state.groq_api_key = api_key
        os.environ["GROQ_API_KEY"] = api_key

    model = st.selectbox("Model", ["mixtral-8x7b-32768", "llama2-70b-4096"], index=0)
    chunk_size = st.slider("Chunk size (characters)", 500, 2000, 1000)
    top_k = st.slider("Top K chunks to retrieve", 2, 10, 5)

    st.markdown("---")
    st.subheader("📂 Topics")

    new_topic = st.text_input("New topic name")
    if st.button("➕ Create Topic"):
        if new_topic and new_topic not in st.session_state.topics:
            st.session_state.topics[new_topic] = VectorStore(new_topic)
            st.session_state.topic_chunks[new_topic] = []
            st.session_state.current_topic = new_topic
            st.success(f"Topic '{new_topic}' created!")
            st.rerun()
        elif new_topic in st.session_state.topics:
            st.warning("Topic already exists.")
        else:
            st.warning("Enter a topic name.")

    topic_names = list(st.session_state.topics.keys())
    if topic_names:
        current = st.session_state.current_topic
        if current not in topic_names:
            current = topic_names[0]
        selected = st.selectbox("Select topic", topic_names, index=topic_names.index(current))
        if selected != st.session_state.current_topic:
            st.session_state.current_topic = selected
            st.rerun()
    else:
        st.info("No topics yet. Create one above.")

    if st.button("🗑️ Clear all topics"):
        st.session_state.topics = {}
        st.session_state.topic_chunks = {}
        st.session_state.current_topic = None
        st.rerun()

# --- Main area ---
if st.session_state.current_topic is not None:
    current_topic = st.session_state.current_topic
    st.subheader(f"📌 Current Topic: **{current_topic}**")

    uploaded_files = st.file_uploader(
        "Upload PDF or Word files (max 1000 MB total)",
        type=["pdf", "docx"],
        accept_multiple_files=True
    )

    if uploaded_files and st.button("📤 Process uploaded files"):
        processor = DocumentProcessor()
        all_chunks = []
        for uploaded_file in uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            chunks = processor.process_file(tmp_path)
            all_chunks.extend(chunks)
            os.unlink(tmp_path)

        if all_chunks:
            if current_topic not in st.session_state.topic_chunks:
                st.session_state.topic_chunks[current_topic] = []
            st.session_state.topic_chunks[current_topic].extend(all_chunks)

            vector_store = st.session_state.topics[current_topic]
            vector_store.build_index(
                st.session_state.topic_chunks[current_topic],
                chunk_size=chunk_size
            )
            st.success(
                f"Processed {len(uploaded_files)} files, "
                f"total {len(st.session_state.topic_chunks[current_topic])} chunks indexed."
            )
        else:
            st.warning("No text extracted from uploaded files. (OCR may be disabled)")

    # Question
    question = st.text_input("💬 Ask a question about the documents in this topic:")
    if question:
        vector_store = st.session_state.topics.get(current_topic)
        if vector_store is None:
            st.error("No vector store for this topic. Upload documents first.")
        else:
            with st.spinner("Generating answer..."):
                qa_engine = QAEngine(model=model)
                answer, sources = qa_engine.answer(
                    question,
                    vector_store,
                    top_k=top_k
                )
                st.markdown("### 💡 Answer")
                st.write(answer)

                with st.expander("📚 Sources (with location)"):
                    for i, src in enumerate(sources):
                        st.write(f"**Source {i+1}:** *{src['source']}*, page {src['page']}")
                        st.write(f"`{src['text'][:300]}...`")
else:
    st.info("👈 Please create or select a topic from the sidebar to get started.")
