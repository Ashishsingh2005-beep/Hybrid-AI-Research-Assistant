import streamlit as st
import time
import os
from utils.memory import ConversationMemory
from utils.prompt import get_system_prompt, get_summarization_prompt
from pdf.extractor import extract_text_from_pdf, get_pdf_metadata
from models.slm import generate_local_slm_response, is_model_downloaded, SLM_MODELS
from models.llm import generate_llm_response, is_api_key_configured
from utils.rag import chunk_text, SimpleRetriever
from utils.search import search_web
from utils.system_monitor import ResourceTracker, get_system_resources

st.set_page_config(page_title="Chat - Hybrid AI Assistant", layout="wide")

# Custom Styles
st.markdown("""
<style>
    .metric-card {
        background-color: #1b1e24;
        border: 1px solid #2e3440;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
        text-align: center;
    }
    .metric-value {
        font-size: 20px;
        font-weight: bold;
        color: #88c0d0;
    }
    .metric-label {
        font-size: 11px;
        color: #d8dee9;
        text-transform: uppercase;
        margin-top: 4px;
    }
    .routing-info {
        background-color: #2e3440;
        border-left: 4px solid #81a1c1;
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 15px;
        font-size: 13px;
    }
    .search-context-box {
        background-color: #232831;
        border: 1px solid #3b4252;
        border-radius: 6px;
        padding: 10px;
        font-size: 12px;
        margin-bottom: 10px;
        color: #e5e9f0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State Variables if they don't exist
if "slm_model" not in st.session_state:
    st.session_state["slm_model"] = list(SLM_MODELS.keys())[0]
if "llm_model" not in st.session_state:
    st.session_state["llm_model"] = "gemini-1.5-flash"
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

# Initialize memory
memory = ConversationMemory()

# Page header
st.title("💬 Hybrid AI Chat Assistant")
st.markdown("Interact with offline Local SLMs and cloud-based LLMs in a single unified interface.")

# Route queries for Auto mode
def determine_routing(query: str, pdf_active: bool) -> tuple[str, str]:
    if pdf_active:
        return "LLM", "PDF context is uploaded. Document analysis requires LLM's larger context window and power."
    
    # Check internet-required keywords
    internet_keywords = ["weather", "news", "recent", "search", "latest", "today", "current", "stock price", "price of"]
    if st.session_state["auto_require_web"]:
        for kw in internet_keywords:
            if kw in query.lower():
                return "LLM", f"Query refers to '{kw}' which may need real-time data or search (Cloud LLM)."
                
    # Check word count
    words = len(query.split())
    threshold = st.session_state["auto_word_threshold"]
    if words >= threshold:
        return "LLM", f"Query contains {words} words (threshold is {threshold}). Routing to Cloud LLM."
    else:
        return "SLM", f"Query contains {words} words (threshold is {threshold}). Routing to Local SLM."

# Sidebar configuration
with st.sidebar:
    st.header("📁 Chat Sessions")
    
    # Save current session
    with st.expander("Save Current Chat", expanded=False):
        session_name_input = st.text_input("Session Name", placeholder="My Research Topic")
        if st.button("💾 Save Session", use_container_width=True):
            if session_name_input.strip():
                memory.save_session(session_name_input.strip())
                st.success(f"Saved: {session_name_input}")
                st.rerun()
            else:
                st.error("Please enter a name")
                
    # Load past session
    saved_sessions = memory.list_sessions()
    if saved_sessions:
        session_options = {s["title"]: s["filename"] for s in saved_sessions}
        selected_session_title = st.selectbox("Load Chat History", options=list(session_options.keys()))
        
        col_load1, col_load2 = st.columns(2)
        with col_load1:
            if st.button("📥 Load Selected", use_container_width=True):
                filename = session_options[selected_session_title]
                if memory.load_session(filename):
                    st.success("Session loaded!")
                    st.rerun()
        with col_load2:
            if st.button("🗑️ Delete Selected", use_container_width=True):
                filename = session_options[selected_session_title]
                memory.delete_session(filename)
                st.success("Deleted!")
                st.rerun()
                
    if st.button("➕ Start New Chat", type="primary", use_container_width=True):
        memory.clear()
        st.success("Cleared conversation history!")
        st.rerun()

    st.markdown("---")
    
    st.header("🤖 Model Settings")
    model_mode = st.radio(
        "Routing Mode",
        options=["Local SLM Only", "Cloud LLM Only", "Intelligent Auto"],
        index=2,
        help="Select which AI engine handles your questions."
    )
    
    # Model Dropdowns
    if model_mode in ["Local SLM Only", "Intelligent Auto"]:
        selected_slm = st.selectbox(
            "Active Local SLM",
            options=list(SLM_MODELS.keys()),
            index=list(SLM_MODELS.keys()).index(st.session_state["slm_model"])
        )
        st.session_state["slm_model"] = selected_slm
        
    if model_mode in ["Cloud LLM Only", "Intelligent Auto"]:
        llm_options = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp", "gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash-8b", "gemini-flash-latest", "gemini-pro-latest"]
        if st.session_state["llm_model"] not in llm_options:
            st.session_state["llm_model"] = "gemini-1.5-flash"
        selected_llm = st.selectbox(
            "Active Cloud LLM",
            options=llm_options,
            index=llm_options.index(st.session_state["llm_model"])
        )
        st.session_state["llm_model"] = selected_llm
        
    st.markdown("---")
    
    # RAG & Web Search Toggles
    st.subheader("🛠️ Context Enhancers")
    rag_enabled = st.checkbox("Enable Local RAG (TF-IDF)", value=True, help="Splits PDFs into small chunks and searches them. Recommended for Local SLM.")
    web_search_enabled = st.checkbox("Enable Live Web Search", value=False, help="Runs a DuckDuckGo search on the query and injects the context.")
    
    st.markdown("---")
    
    # PDF Upload Panel
    st.subheader("📄 Research PDF Context")
    uploaded_pdf = st.file_uploader("Upload research PDF", type=["pdf"])
    
    pdf_text = ""
    pdf_meta = None
    if uploaded_pdf:
        # Cache PDF extraction in session state
        if "loaded_pdf_name" not in st.session_state or st.session_state["loaded_pdf_name"] != uploaded_pdf.name:
            with st.spinner("Extracting PDF text..."):
                extracted = extract_text_from_pdf(uploaded_pdf)
                st.session_state["loaded_pdf_text"] = extracted
                st.session_state["loaded_pdf_name"] = uploaded_pdf.name
                st.session_state["loaded_pdf_meta"] = get_pdf_metadata(uploaded_pdf)
                
                # Precompute RAG retriever
                chunks = chunk_text(extracted)
                st.session_state["loaded_pdf_retriever"] = SimpleRetriever(chunks)
                
        pdf_text = st.session_state["loaded_pdf_text"]
        pdf_meta = st.session_state["loaded_pdf_meta"]
        
        st.success(f"Loaded: {uploaded_pdf.name}")
        st.markdown(f"**Pages:** {pdf_meta.get('pages', 0)} | **Tokens (~):** {len(pdf_text)//4}")
        
        pdf_action = st.radio("PDF Action", ["None", "Summarize Document", "Ask Chat about PDF"])
        
        if pdf_action == "Summarize Document" and st.button("Generate Summary"):
            st.session_state["pdf_summarizing"] = True
            
    else:
        pdf_action = "None"
        
    st.markdown("---")
    
    # Prompt Playground / Advanced Parameters
    st.subheader("⚙️ Prompt Playground")
    with st.expander("Model Parameters", expanded=False):
        if model_mode == "Local SLM Only" or model_mode == "Intelligent Auto":
            st.markdown("**Local SLM Parameters**")
            local_temp = st.slider("SLM Temperature", 0.0, 1.5, st.session_state["local_temp"], 0.1, key="chat_local_temp")
            local_max = st.number_input("SLM Max Tokens", 64, 2048, st.session_state["local_max_tokens"], 64, key="chat_local_max")
        if model_mode == "Cloud LLM Only" or model_mode == "Intelligent Auto":
            st.markdown("**Cloud LLM Parameters**")
            cloud_temp = st.slider("LLM Temperature", 0.0, 1.5, st.session_state["cloud_temp"], 0.1, key="chat_cloud_temp")
            cloud_max = st.number_input("LLM Max Tokens", 64, 8192, st.session_state["cloud_max_tokens"], 128, key="chat_cloud_max")
            
    # System Monitor
    st.subheader("🖥️ Host System Load")
    res = get_system_resources()
    st.markdown(f"**CPU Load:** {res['cpu_percent']:.1f}%")
    st.progress(res['cpu_percent'] / 100.0)
    st.markdown(f"**RAM Usage:** {res['ram_percent']:.1f}% ({res['ram_available_gb']:.1f} GB Free)")
    st.progress(res['ram_percent'] / 100.0)
    
    st.markdown("---")
    
    # Statistics Panel
    st.subheader("📊 Performance Statistics")
    last_stats = memory.get_last_stats()
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{last_stats.get('response_time', 0.0):.2f}s</div>
            <div class="metric-label">Resp Time</div>
        </div>
        """, unsafe_allow_html=True)
    with col_s2:
        cost = last_stats.get('cost', 0.0)
        cost_str = f"${cost:.5f}" if cost > 0 else "Free"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{cost_str}</div>
            <div class="metric-label">Cost</div>
        </div>
        """, unsafe_allow_html=True)
        
    col_s3, col_s4 = st.columns(2)
    with col_s3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{last_stats.get('input_tokens', 0)}</div>
            <div class="metric-label">In Tokens</div>
        </div>
        """, unsafe_allow_html=True)
    with col_s4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{last_stats.get('output_tokens', 0)}</div>
            <div class="metric-label">Out Tokens</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown(f"**Current Engine:** `{last_stats.get('model', 'N/A')}`")

# Document summarization trigger
if st.session_state.get("pdf_summarizing", False):
    st.session_state["pdf_summarizing"] = False
    if not is_api_key_configured():
        st.error("Please configure your Gemini API Key in the Settings page to summarize PDFs.")
    else:
        with st.chat_message("assistant"):
            summary_placeholder = st.empty()
            summary_placeholder.markdown("🔍 Generating summary using Cloud LLM...")
            
            prompt = get_summarization_prompt(pdf_text, 150)
            
            tracker = ResourceTracker()
            res = generate_llm_response(
                prompt=prompt,
                system_prompt="You are an expert academic summarizer.",
                model_name=st.session_state["llm_model"],
                temperature=0.3,
                max_tokens=500,
                stream=True
            )
            
            full_summary = ""
            stats = {}
            for chunk in res["stream"]:
                if isinstance(chunk, dict):
                    stats = chunk
                else:
                    full_summary += chunk
                    summary_placeholder.markdown(full_summary + "▌")
            summary_placeholder.markdown(full_summary)
            
            # Incorporate system monitor metrics
            res_metrics = tracker.get_metrics()
            stats["cpu_percent"] = res_metrics["cpu_peak_percent"]
            stats["ram_percent"] = res_metrics["ram_peak_percent"]
            
            # Save message
            memory.add_message("assistant", f"### Document Summary:\n{full_summary}", stats)
            st.rerun()

# Display chat messages
messages = memory.get_messages()
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Export and Download Area
if messages:
    st.markdown("---")
    export_content = "# Hybrid AI Assistant Chat Export\n\n"
    for msg in messages:
        role = "### " + msg["role"].upper()
        export_content += f"{role}\n{msg['content']}\n\n"
    st.download_button("📤 Export Conversation as Markdown", data=export_content, file_name=f"chat_export_{int(time.time())}.md", use_container_width=True)

# User Input
if user_input := st.chat_input("Ask a question..."):
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    memory.add_message("user", user_input)
    
    # 1. Web Search Context Injection (If Enabled)
    web_context = ""
    if web_search_enabled:
        with st.spinner("🔍 Querying web results..."):
            search_results = search_web(user_input)
            if search_results:
                web_context = "### Web Search Snippets:\n"
                for res in search_results:
                    web_context += f"- **{res['title']}**: {res['snippet']}\n"
                
                # Show search context box in the UI
                with st.expander("🔍 Retrived Web Context", expanded=False):
                    st.markdown(web_context)

    # 2. Routing decision
    routed_engine = "SLM"
    routing_reason = "Manual override: Local SLM Selected"
    
    pdf_active = (pdf_action == "Ask Chat about PDF" and pdf_text != "")
    
    if model_mode == "Cloud LLM Only":
        routed_engine = "LLM"
        routing_reason = "Manual override: Cloud LLM Selected"
    elif model_mode == "Intelligent Auto":
        routed_engine, routing_reason = determine_routing(user_input, pdf_active)
        
    st.markdown(f'<div class="routing-info">🧠 <b>Routing Decision:</b> {routing_reason} ➔ <b>Running {routed_engine}</b></div>', unsafe_allow_html=True)
    
    # Initialize resource tracker
    tracker = ResourceTracker()
    
    # Execute generation based on routed model
    if routed_engine == "LLM":
        if not is_api_key_configured():
            with st.chat_message("assistant"):
                st.error("Gemini API Key is not set. Please go to the Settings page to enter your API key, or use 'Local SLM Only'.")
        else:
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                response_placeholder.markdown("🤖 *Cloud LLM is generating...*")
                
                # Format prompt, inject PDF context if enabled (with RAG option)
                final_prompt = user_input
                if pdf_active:
                    if rag_enabled and "loaded_pdf_retriever" in st.session_state:
                        retriever = st.session_state["loaded_pdf_retriever"]
                        # Retrieve top 8 chunks for LLM
                        relevant_chunks = retriever.retrieve(user_input, top_k=8)
                        pdf_context = "\n\n".join([c[0] for c in relevant_chunks])
                        st.info(f"RAG: Retrieved 8 relevant chunks (~{len(pdf_context)//4} tokens) from PDF.")
                    else:
                        pdf_context = pdf_text[:12000]
                        
                    final_prompt = (
                        f"Answer the user's question based strictly on the uploaded PDF document text. "
                        f"If the answer cannot be found in the PDF, state that clearly.\n\n"
                        f"PDF Context:\n\"\"\"\n{pdf_context}\n\"\"\"\n\n"
                        f"User Question: {user_input}"
                    )
                
                # Inject web context if web search is enabled
                if web_context:
                    final_prompt = f"{web_context}\n\nUse the web search results above to answer the user query: {final_prompt}"
                
                # Fetch parameters from playground
                temp = st.session_state.get("chat_cloud_temp", st.session_state["cloud_temp"])
                max_t = st.session_state.get("chat_cloud_max", st.session_state["cloud_max_tokens"])
                
                sys_prompt = get_system_prompt("llm")
                
                res = generate_llm_response(
                    prompt=final_prompt,
                    system_prompt=sys_prompt,
                    model_name=st.session_state["llm_model"],
                    temperature=temp,
                    max_tokens=max_t,
                    stream=True
                )
                
                full_res = ""
                stats = {}
                for chunk in res["stream"]:
                    if isinstance(chunk, dict):
                        stats = chunk
                    else:
                        full_res += chunk
                        response_placeholder.markdown(full_res + "▌")
                response_placeholder.markdown(full_res)
                
                # Gather resources used during generation
                res_metrics = tracker.get_metrics()
                stats["cpu_percent"] = res_metrics["cpu_peak_percent"]
                stats["ram_percent"] = res_metrics["ram_peak_percent"]
                
                memory.add_message("assistant", full_res, stats)
                st.rerun()
                
    else: # Local SLM
        slm_model = st.session_state["slm_model"]
        if not is_model_downloaded(slm_model):
            with st.chat_message("assistant"):
                st.warning(f"The local model `{slm_model}` is not downloaded yet. Go to Settings page to download it, or use simulated mode.")
                
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            response_placeholder.markdown("💻 *Local SLM is generating...*")
            
            final_prompt = user_input
            if pdf_active:
                if rag_enabled and "loaded_pdf_retriever" in st.session_state:
                    retriever = st.session_state["loaded_pdf_retriever"]
                    # Retrieve top 3 chunks for SLM (to fit within local context)
                    relevant_chunks = retriever.retrieve(user_input, top_k=3)
                    pdf_context = "\n\n".join([c[0] for c in relevant_chunks])
                    st.info(f"RAG: Retrieved 3 relevant chunks (~{len(pdf_context)//4} tokens) from PDF.")
                else:
                    pdf_context = pdf_text[:3000]
                    
                # Local models have smaller context windows (e.g. 2048), so we take a smaller snippet
                final_prompt = (
                    f"You are evaluating a PDF. Context:\n\"\"\"\n{pdf_context}\n\"\"\"\n\n"
                    f"Question: {user_input}\nAnswer:"
                )
                
            # Inject web context if web search is enabled
            if web_context:
                final_prompt = f"{web_context}\n\nUse the web search results to answer: {final_prompt}"
                
            temp = st.session_state.get("chat_local_temp", st.session_state["local_temp"])
            max_t = st.session_state.get("chat_local_max", st.session_state["local_max_tokens"])
            
            # Format chat with system prompt
            sys_prompt = get_system_prompt("slm")
            formatted_prompt = f"System: {sys_prompt}\nQuery: {final_prompt}\nAssistant:"
            
            try:
                res = generate_local_slm_response(
                    prompt=formatted_prompt,
                    model_name=slm_model,
                    temperature=temp,
                    max_tokens=max_t,
                    stream=True
                )
                
                full_res = ""
                stats = {}
                for chunk in res["stream"]:
                    if isinstance(chunk, dict):
                        stats = chunk
                    else:
                        full_res += chunk
                        response_placeholder.markdown(full_res + "▌")
                response_placeholder.markdown(full_res)
                
                # Gather resources used during generation
                res_metrics = tracker.get_metrics()
                stats["cpu_percent"] = res_metrics["cpu_peak_percent"]
                stats["ram_percent"] = res_metrics["ram_peak_percent"]
                
                memory.add_message("assistant", full_res, stats)
                st.rerun()
            except Exception as e:
                st.error(f"Error running local SLM: {e}")
