# In the sidebar, replace the model selector with:
model = st.selectbox(
    "Model",
    ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"],
    index=0
)

# For API key, set both environment variables to avoid confusion:
if api_key:
    st.session_state.gemini_api_key = api_key
    os.environ["GEMINI_API_KEY"] = api_key
    # Also clear Groq env var if present
    os.environ.pop("GROQ_API_KEY", None)

# Load from secrets if present:
if "GEMINI_API_KEY" in st.secrets:
    st.session_state.gemini_api_key = st.secrets["GEMINI_API_KEY"]
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
