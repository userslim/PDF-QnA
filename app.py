import streamlit as st
import os
import tempfile
from pathlib import Path
from document_processor import DocumentProcessor
from vector_store import VectorStore
from qa_engine import QAEngine
from session_manager import SessionManager

st.set_page_config(page_title="PDF/Word Q&A", layout="wide")
st.title("📄 PDF/Word Q&A with Groq")

# Initialize session state
SessionManager.init_session()

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input("Groq API Key", type="password", 
                            value=st.session_state.get("groq_api_key", ""))
    if api_key:
        st.session_state.groq_api_key = api_key
        os.environ["GROQ_API_KEY"] = api_key
    model = st.selectbox("Model", ["mixtral-8x7b-32768", "llama2-70b-4096"], 
                         index=0)
    chunk_size = st.slider("Chunk size (characters)", 500, 2000, 1000)
    top_k = st.slider("Top K chunks to retrieve", 2, 10, 5)

    if st.button("Clear Session"):
        SessionManager.clear_session()
        st.rerun()

# Upload section
uploaded_file = st.file_uploader("Upload a PDF or Word document", 
                                 type=["pdf", "docx"])

if uploaded_file is not None:
    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name

    # Process document
    with st.spinner("Processing document..."):
        processor = DocumentProcessor()
        chunks = processor.process_file(tmp_path)
        st.success(f"Extracted {len(chunks)} chunks.")

        # Build vector store
        vector_store = VectorStore()
        vector_store.build_index(chunks, chunk_size=chunk_size)
        st.session_state.vector_store = vector_store
        st.session_state.file_name = uploaded_file.name
        st.session_state.chunks = chunks

    os.unlink(tmp_path)  # clean up

# Display document info
if st.session_state.get("vector_store") is not None:
    st.info(f"📄 Document: **{st.session_state.file_name}** – {len(st.session_state.chunks)} chunks loaded.")
    
    # Question input
    question = st.text_input("Ask a question about the document:")
    if question:
        with st.spinner("Generating answer..."):
            qa_engine = QAEngine(model=model)
            answer, sources = qa_engine.answer(
                question, 
                st.session_state.vector_store,
                top_k=top_k
            )
            st.markdown("### 💡 Answer")
            st.write(answer)
            with st.expander("📚 Sources"):
                for i, src in enumerate(sources):
                    st.write(f"**Source {i+1}:** {src[:500]}...")
else:
    st.info("Please upload a document to get started.")
