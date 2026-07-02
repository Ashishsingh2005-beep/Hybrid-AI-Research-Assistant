import streamlit as st
import os

st.set_page_config(page_title="Home - Hybrid AI Assistant", layout="wide")

# Custom CSS for gorgeous design
st.markdown("""
<style>
    .hero-title {
        font-size: 48px;
        font-weight: 800;
        background: linear-gradient(135deg, #8fbcbb 0%, #88c0d0 50%, #b48ead 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }
    .hero-subtitle {
        font-size: 20px;
        color: #d8dee9;
        margin-bottom: 30px;
    }
    .arch-card {
        background-color: #1b1e24;
        border: 1px solid #2e3440;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 25px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    .pill {
        background-color: #3b4252;
        color: #e5e9f0;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        display: inline-block;
        margin-right: 8px;
        margin-bottom: 8px;
    }
    .arrow {
        text-align: center;
        font-size: 24px;
        color: #88c0d0;
        margin: 10px 0;
    }
    .nav-btn {
        display: inline-block;
        background: linear-gradient(135deg, #4c566a 0%, #3b4252 100%);
        color: #eceff4;
        padding: 10px 20px;
        border-radius: 6px;
        text-decoration: none;
        font-weight: bold;
        transition: transform 0.2s;
    }
    .nav-btn:hover {
        transform: translateY(-2px);
        color: #88c0d0;
    }
</style>
""", unsafe_allow_html=True)

# Main Hero
st.markdown('<div class="hero-title">Hybrid AI Research Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">An intelligent assistant leveraging Local Small Language Models (SLMs) and Cloud Large Language Models (LLMs)</div>', unsafe_allow_html=True)

st.markdown("---")

col1, col2 = st.columns([3, 2])

with col1:
    st.markdown('<div class="arch-card">', unsafe_allow_html=True)
    st.header("📐 Architecture Overview")
    st.write("This application demonstrates a **hybrid AI design pattern**. It intelligently routes queries to the most cost-effective and capable engine:")
    
    # Textual diagram representation
    st.code("""
                  ┌──────────────────────┐
                  │       User Query     │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  Intelligent Router  │
                  └─────┬──────────┬─────┘
                        │          │
         (Short/Simple) │          │ (Long/Complex/PDF)
                        ▼          ▼
                  ┌──────────┐┌──────────┐
                  │Local SLM ││Cloud LLM │
                  │ (Offline)││ (Online) │
                  └─────┬────┘└────┬─────┘
                        │          │
                        ▼          ▼
                  ┌──────────────────────┐
                  │    Final Response    │
                  └──────────────────────┘
    """, language="text")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="arch-card">', unsafe_allow_html=True)
    st.header("🚀 Quick Navigation")
    st.write("Explore the different features of the assistant:")
    
    col_nav1, col_nav2, col_nav3 = st.columns(3)
    with col_nav1:
        st.subheader("💬 Chat Assistant")
        st.write("Ask questions, upload research papers, and chat offline with the model.")
        st.markdown("[Go to Chat ➔](/chat)", unsafe_allow_html=True)
    with col_nav2:
        st.subheader("⚖️ Compare Answers")
        st.write("Compare the Local SLM and Cloud LLM responses side-by-side.")
        st.markdown("[Go to Compare ➔](/compare)", unsafe_allow_html=True)
    with col_nav3:
        st.subheader("⚙️ Settings")
        st.write("Configure model parameters, download files, and manage your API keys.")
        st.markdown("[Go to Settings ➔](/settings)", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="arch-card">', unsafe_allow_html=True)
    st.subheader("💻 Local SLM (Offline Edge)")
    st.write("Runs entirely on your local machine using quantized GGUF models. Ideal for:")
    st.markdown('<span class="pill">Simple Questions</span>', unsafe_allow_html=True)
    st.markdown('<span class="pill">Grammar Check</span>', unsafe_allow_html=True)
    st.markdown('<span class="pill">Code Autocomplete</span>', unsafe_allow_html=True)
    st.markdown('<span class="pill">Offline Work</span>', unsafe_allow_html=True)
    st.markdown('<span class="pill">Zero Token Cost</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="arch-card">', unsafe_allow_html=True)
    st.subheader("☁️ Cloud LLM (Gemini API)")
    st.write("Runs on Google Cloud infra. Ideal for:")
    st.markdown('<span class="pill">Deep Analysis</span>', unsafe_allow_html=True)
    st.markdown('<span class="pill">Large Context PDFs</span>', unsafe_allow_html=True)
    st.markdown('<span class="pill">Complex Reasoning</span>', unsafe_allow_html=True)
    st.markdown('<span class="pill">Multi-document Comparison</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="arch-card">', unsafe_allow_html=True)
    st.subheader("🧠 Router (Auto Mode)")
    st.write("Intelligent routing logic determines the correct model using criteria such as:")
    st.write("- **Query word count:** routes short queries to SLM.")
    st.write("- **PDF Upload:** routes research paper queries to LLM.")
    st.write("- **Internet necessity:** routes searches to LLM.")
    st.markdown('</div>', unsafe_allow_html=True)

st.info("💡 **Getting Started:** Visit the **Settings** page in the sidebar to download a local model (like SmolLM2-135M) or enter your Gemini API key, then start chatting!")
