import streamlit as st
import os
import sys
from models.slm import (
    SLM_MODELS, 
    is_model_downloaded, 
    download_slm_model, 
    download_llama_binaries, 
    check_llama_cpp_library, 
    get_models_dir, 
    get_llama_bin_dir,
    terminate_existing_llama_server
)
from models.llm import is_api_key_configured, get_available_models

st.set_page_config(page_title="Settings - Hybrid AI Assistant", layout="wide")

# Custom CSS for Premium Design
st.markdown("""
<style>
    .reportview-container, .main {
        background: #0f1115;
        color: #e5e9f0;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #1b1e24;
        border: 1px solid #2e3440 !important;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
    }
    .status-badge {
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 12px;
        display: inline-block;
    }
    .status-ok {
        background-color: #2e7d32;
        color: #e8f5e9;
    }
    .status-warning {
        background-color: #c62828;
        color: #ffebee;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚙️ Assistant Settings & Configuration")
st.markdown("Configure your Local Small Language Model (SLM), Cloud LLM API credentials, and Auto Mode routing logic.")
st.markdown("")

# Initialize session state configuration if they don't exist
if "slm_model" not in st.session_state:
    st.session_state["slm_model"] = list(SLM_MODELS.keys())[0]
if "llm_model" not in st.session_state:
    st.session_state["llm_model"] = "gemini-1.5-flash"
if "gemini_api_key" not in st.session_state:
    from models.llm import DEFAULT_API_KEY
    st.session_state["gemini_api_key"] = os.environ.get("GEMINI_API_KEY", DEFAULT_API_KEY)
if "local_temp" not in st.session_state:
    st.session_state["local_temp"] = 0.7
if "local_max_tokens" not in st.session_state:
    st.session_state["local_max_tokens"] = 512
if "cloud_temp" not in st.session_state:
    st.session_state["cloud_temp"] = 0.7
if "cloud_max_tokens" not in st.session_state:
    st.session_state["cloud_max_tokens"] = 1000
if "auto_word_threshold" not in st.session_state:
    st.session_state["auto_word_threshold"] = 50
if "auto_require_web" not in st.session_state:
    st.session_state["auto_require_web"] = True

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.header("🎛️ Local SLM Configuration")
        
        # Model Selection
        selected_slm = st.selectbox(
            "Choose Local SLM", 
            options=list(SLM_MODELS.keys()),
            index=list(SLM_MODELS.keys()).index(st.session_state["slm_model"]) if st.session_state["slm_model"] in SLM_MODELS else 0,
            help="Select which small model to run locally."
        )
        st.session_state["slm_model"] = selected_slm
        
        # Model info
        model_info = SLM_MODELS[selected_slm]
        st.info(f"**Model Repo:** `{model_info['repo_id']}`\n\n**Description:** {model_info['description']}\n\n**Context Size:** {model_info['context_window']} tokens")
        
        # Download state
        downloaded = is_model_downloaded(selected_slm)
        if downloaded:
            st.success("✅ Model file is downloaded and ready to use.")
        else:
            st.warning("⚠️ Model is not downloaded yet. You must download it to run offline.")
            
            # Download button
            if st.button(f"📥 Download {selected_slm.split(' ')[0]}", use_container_width=True):
                progress_bar = st.progress(0.0)
                status_text = st.empty()
                try:
                    download_slm_model(selected_slm, progress_bar, status_text)
                    st.success("Model downloaded successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Download failed: {e}")
                    
        st.markdown("---")
        st.subheader("Model Parameters")
        st.session_state["local_temp"] = st.slider("SLM Temperature", min_value=0.0, max_value=1.5, value=st.session_state["local_temp"], step=0.1, help="Higher values mean more creative, lower means more deterministic.")
        st.session_state["local_max_tokens"] = st.number_input("SLM Max Tokens", min_value=32, max_value=2048, value=st.session_state["local_max_tokens"], step=64)

with col2:
    with st.container(border=True):
        st.header("☁️ Cloud LLM Configuration")
        
        # Model Selection
        llm_options = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp", "gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash-8b", "gemini-flash-latest", "gemini-pro-latest"]
        if st.session_state["llm_model"] not in llm_options:
            st.session_state["llm_model"] = "gemini-1.5-flash"
            
        selected_llm = st.selectbox(
            "Choose Cloud LLM",
            options=llm_options,
            index=llm_options.index(st.session_state["llm_model"])
        )
        st.session_state["llm_model"] = selected_llm
        
        # API Key Input
        api_key_input = st.text_input("Gemini API Key", value=st.session_state["gemini_api_key"], type="password", help="Enter your Gemini API key from Google AI Studio.")
        
        if api_key_input:
            st.session_state["gemini_api_key"] = api_key_input
            # Save key in environment so LLM functions can read it
            os.environ["GEMINI_API_KEY"] = api_key_input
            st.success("✅ API key stored in session.")
        elif os.environ.get("GEMINI_API_KEY"):
            st.success("✅ API key found in system environment.")
        else:
            st.warning("⚠️ No Gemini API Key configured. Cloud LLM features will be disabled.")

        if st.session_state["gemini_api_key"] or os.environ.get("GEMINI_API_KEY"):
            if st.button("🔍 Diagnose API Key & List Available Models", use_container_width=True):
                with st.spinner("Querying Google Gemini API..."):
                    available_models = get_available_models()
                    if available_models:
                        st.success(f"Successfully authenticated! Available models for your API key:\n" + "\n".join([f"- `{m}`" for m in available_models]))
                    else:
                        st.error("Authentication failed or key has no access to any model. Please check if your API key is correct/valid or if it's still propagating on Google's side.")
            
        st.markdown("---")
        st.subheader("Model Parameters")
        st.session_state["cloud_temp"] = st.slider("LLM Temperature", min_value=0.0, max_value=1.5, value=st.session_state["cloud_temp"], step=0.1)
        st.session_state["cloud_max_tokens"] = st.number_input("LLM Max Tokens", min_value=64, max_value=8192, value=st.session_state["cloud_max_tokens"], step=128)

st.markdown("")
with st.container(border=True):
    st.header("🧠 Intelligent Auto Mode Routing Rules")
    st.markdown("Auto mode dynamically decides whether to use the Local SLM (offline, free, fast) or the Cloud LLM (online, expensive, powerful).")
    
    auto_col1, auto_col2 = st.columns(2)
    with auto_col1:
        st.session_state["auto_word_threshold"] = st.number_input(
            "Routing Threshold (Word Count)", 
            min_value=10, 
            max_value=500, 
            value=st.session_state["auto_word_threshold"],
            help="If the query has fewer words than this threshold, it routes to Local SLM. Otherwise, it routes to Cloud LLM."
        )
    with auto_col2:
        st.session_state["auto_require_web"] = st.checkbox(
            "Route internet-dependent questions to LLM", 
            value=st.session_state["auto_require_web"],
            help="If the query contains search-related keywords like 'news', 'weather', 'latest', 'today', 'search', it automatically routes to Cloud LLM."
        )

    st.info("""
    💡 **Auto Mode Routing Flow:**
    1. Check if the user query requests real-time/latest information ➔ Cloud LLM.
    2. Check if a PDF file is uploaded ➔ Cloud LLM (due to document size/context limits).
    3. Check the word count of the query:
       - `< threshold` (Short queries, e.g. "What is Python?") ➔ **Local SLM**
       - `>= threshold` (Long queries, complex reasoning) ➔ **Cloud LLM**
    """)

st.markdown("")
# System Diagnostics Card
with st.container(border=True):
    st.header("🔍 System Diagnostic Dashboard")
    diag_col1, diag_col2, diag_col3 = st.columns(3)

    has_lib = check_llama_cpp_library()
    has_bin = os.path.exists(os.path.join(get_llama_bin_dir(), "llama-server.exe"))

    with diag_col1:
        st.subheader("Software Libraries")
        if has_lib:
            st.markdown('`llama-cpp-python` installation: <span class="status-badge status-ok">ACTIVE</span>', unsafe_allow_html=True)
        else:
            st.markdown('`llama-cpp-python` installation: <span class="status-badge status-warning">NOT INSTALLED</span>', unsafe_allow_html=True)
        st.write("Using python library allows loading models directly in streamlit python process memory.")

    with diag_col2:
        st.subheader("llama.cpp Windows Binary")
        if has_bin:
            st.markdown('`llama-server.exe` binary: <span class="status-badge status-ok">AVAILABLE</span>', unsafe_allow_html=True)
        else:
            st.markdown('`llama-server.exe` binary: <span class="status-badge status-warning">MISSING</span>', unsafe_allow_html=True)
            
        if not has_lib and not has_bin:
            st.write("Since the `llama-cpp-python` library is not compiled yet, you can download precompiled Windows binaries below.")
            if st.button("📥 Download llama.cpp Binaries", use_container_width=True):
                p_bar = st.progress(0.0)
                s_txt = st.empty()
                if download_llama_binaries(p_bar, s_txt):
                    st.success("llama.cpp binaries downloaded!")
                    st.rerun()
        else:
            if st.button("🔄 Restart Local Llama Server", use_container_width=True):
                terminate_existing_llama_server()
                st.success("Local llama-server instances reset.")

    with diag_col3:
        st.subheader("Offline/Simulated Mode")
        st.write("If you don't download local binaries or models, the system will run in **Simulated Local Mode**.")
        st.write("This allows testing the app layout and features without waiting for downloads!")
        st.write(f"**Model Folder:** `{get_models_dir()}`")

