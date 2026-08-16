import streamlit as st
import os
import tempfile
from pathlib import Path
from document_processor import DocumentProcessor
from vector_store import VectorStore
from qa_engine import QAEngine

# --- Page configuration ---
st.set_page_config(page_title="Multi‑Topic PDF/Word Q&A", layout="wide")
st.title("📄 Multi‑Topic PDF/Word Q&A with Gemini")

# --- Session state initialisation ---
if "topics" not in st.session_state:
    st.session_state.topics = {}          # topic_name -> VectorStore
if "topic_chunks" not in st.session_state:
    st.session_state.topic_chunks = {}    # topic_name -> list of DocumentChunk
if "current_topic" not in st.session_state:
    st.session_state.current_topic = None
if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = ""

# Try to load API key from Streamlit secrets
if "GEMINI_API_KEY" in st.secrets:
    st.session_state.gemini_api_key = st.secrets["GEMINI_API_KEY"]
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Settings")

    # API Key input (overrides secrets if provided)
    api_key = st.text_input(
        "Gemini API Key",
        type="password",
        value=st.session_state.gemini_api_key
    )
    if api_key:
        st.session_state.gemini_api_key = api_key
        os.environ["GEMINI_API_KEY"] = api_key

    # Model selection (Gemini models)
    model = st.selectbox(
        "Model",
        ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"],
        index=0
    )

    chunk_size = st.slider(
        "Chunk size (characters)",
        min_value=500,
        max_value=2000,
        value=1000,
        step=100
    )
    top_k = st.slider(
        "Top K chunks to retrieve",
        min_value=2,
        max_value=10,
        value=5
    )

    st.markdown("---")
    st.subheader("📂 Topics")

    # Create new topic
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

    # Select existing topic
    topic_names = list(st.session_state.topics.keys())
    if topic_names:
        current = st.session_state.current_topic
        if current not in topic_names:
            current = topic_names[0]
        selected = st.selectbox(
            "Select topic",
            topic_names,
            index=topic_names.index(current)
        )
        if selected != st.session_state.current_topic:
            st.session_state.current_topic = selected
            st.rerun()
    else:
        st.info("No topics yet. Create one above.")

    # Clear all topics
    if st.button("🗑️ Clear all topics"):
        st.session_state.topics = {}
        st.session_state.topic_chunks = {}
        st.session_state.current_topic = None
        st.rerun()

# --- Main area ---
if st.session_state.current_topic is not None:
    current_topic = st.session_state.current_topic
    st.subheader(f"📌 Current Topic: **{current_topic}**")

    # Check OCR availability
    processor = DocumentProcessor()
    if not processor.ocr_available:
        st.warning("⚠️ Tesseract OCR is not installed. Scanned images will be skipped.")
    else:
        st.info("✅ Tesseract OCR is available – images inside PDFs will be transcribed.")

    # File uploader (multiple files)
    uploaded_files = st.file_uploader(
        "Upload PDF or Word files (max 1000 MB total)",
        type=["pdf", "docx"],
        accept_multiple_files=True
    )

    if uploaded_files and st.button("📤 Process uploaded files"):
        all_chunks = []
        for uploaded_file in uploaded_files:
            # Save uploaded file to a temporary location
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=Path(uploaded_file.name).suffix
            ) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name

            # Extract text using DocumentProcessor
            chunks = processor.process_file(tmp_path)
            all_chunks.extend(chunks)
            os.unlink(tmp_path)  # clean up temp file

        if all_chunks:
            # Append new chunks to the current topic's list
            if current_topic not in st.session_state.topic_chunks:
                st.session_state.topic_chunks[current_topic] = []
            st.session_state.topic_chunks[current_topic].extend(all_chunks)

            # Rebuild the vector store index
            vector_store = st.session_state.topics[current_topic]
            vector_store.build_index(
                st.session_state.topic_chunks[current_topic],
                chunk_size=chunk_size
            )
            st.success(
                f"Processed {len(uploaded_files)} file(s), "
                f"total {len(st.session_state.topic_chunks[current_topic])} chunks indexed."
            )
        else:
            st.warning(
                "No text extracted from uploaded files. "
                "They may be empty or scanned with OCR unavailable."
            )

    # --- Question answering ---
    question = st.text_input("💬 Ask a question about the documents in this topic:")
    if question:
        vector_store = st.session_state.topics.get(current_topic)
        if vector_store is None:
            st.error("No vector store for this topic. Upload documents first.")
        else:
            # Check if Gemini API key is set
            if not os.environ.get("GEMINI_API_KEY"):
                st.error(
                    "❌ GEMINI_API_KEY is not set. "
                    "Please enter your API key in the sidebar or set it as a secret."
                )
            else:
                with st.spinner("Generating answer..."):
                    try:
                        # Initialize QA engine with the selected model
                        qa_engine = QAEngine(model=model)
                        answer, sources = qa_engine.answer(
                            question,
                            vector_store,
                            top_k=top_k
                        )

                        # Display the answer
                        if answer.startswith("Error calling Gemini API:"):
                            st.error(answer)
                        else:
                            st.markdown("### 💡 Answer")
                            st.write(answer)

                            # Show sources with file & page info
                            with st.expander("📚 Sources (with location)"):
                                for i, src in enumerate(sources):
                                    st.write(
                                        f"**Source {i+1}:** *{src['source']}*, page {src['page']}"
                                    )
                                    st.write(f"`{src['text'][:300]}...`")
                    except Exception as e:
                        st.error(f"An unexpected error occurred: {str(e)}")
else:
    st.info("👈 Please create or select a topic from the sidebar to get started.")

# --- Footer ---
st.markdown("---")
st.caption(
    "Built with Streamlit, ChromaDB, Sentence‑Transformers, and Google Gemini. "
    "OCR powered by Tesseract."
)
