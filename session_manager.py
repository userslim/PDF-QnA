import streamlit as st

class SessionManager:
    @staticmethod
    def init_session():
        """Initialize session state variables."""
        if "vector_store" not in st.session_state:
            st.session_state.vector_store = None
        if "chunks" not in st.session_state:
            st.session_state.chunks = []
        if "file_name" not in st.session_state:
            st.session_state.file_name = None
        if "groq_api_key" not in st.session_state:
            st.session_state.groq_api_key = ""

    @staticmethod
    def clear_session():
        """Reset all session state."""
        st.session_state.vector_store = None
        st.session_state.chunks = []
        st.session_state.file_name = None
