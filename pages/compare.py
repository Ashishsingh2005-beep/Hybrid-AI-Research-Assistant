import streamlit as st
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from models.slm import generate_local_slm_response, is_model_downloaded, SLM_MODELS
from models.llm import generate_llm_response, is_api_key_configured
from utils.prompt import get_comparison_prompt, get_system_prompt
from utils.search import search_web
from utils.system_monitor import ResourceTracker, get_system_resources

st.set_page_config(page_title="Compare - Hybrid AI Assistant", layout="wide")

st.markdown("""
<style>
    .compare-card {
        background-color: #1b1e24;
        border: 1px solid #2e3440;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .metric-table {
        margin-top: 15px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State Settings if not loaded
if "slm_model" not in st.session_state:
    st.session_state["slm_model"] = list(SLM_MODELS.keys())[0]
if "llm_model" not in st.session_state:
    st.session_state["llm_model"] = "gemini-2.5-flash"
if "local_temp" not in st.session_state:
    st.session_state["local_temp"] = 0.7
if "local_max_tokens" not in st.session_state:
    st.session_state["local_max_tokens"] = 512
if "cloud_temp" not in st.session_state:
    st.session_state["cloud_temp"] = 0.7
if "cloud_max_tokens" not in st.session_state:
    st.session_state["cloud_max_tokens"] = 1000

st.title("⚖️ Model Answer Comparison")
st.markdown("Evaluate Local SLM vs. Cloud LLM side-by-side to understand trade-offs in speed, quality, cost, and latency.")

# Sidebar status
with st.sidebar:
    st.header("🖥️ System Monitor")
    res = get_system_resources()
    st.markdown(f"**CPU Load:** {res['cpu_percent']:.1f}%")
    st.progress(res['cpu_percent'] / 100.0)
    st.markdown(f"**RAM Usage:** {res['ram_percent']:.1f}% ({res['ram_available_gb']:.1f} GB Free)")
    st.progress(res['ram_percent'] / 100.0)
    st.markdown("---")
    
    st.subheader("💡 Context Enhancers")
    web_search_compare = st.checkbox("Enable Live Web Search", value=False, help="Injects DuckDuckGo search snippets into both model prompts.")

# Input Query
query = st.text_area("Enter your test prompt/question here:", value="What is Python and how is it used in Artificial Intelligence?", height=80)

col_ctrl1, col_ctrl2 = st.columns(2)
with col_ctrl1:
    slm_choice = st.selectbox("Local SLM to compare", options=list(SLM_MODELS.keys()), index=list(SLM_MODELS.keys()).index(st.session_state["slm_model"]) if st.session_state["slm_model"] in SLM_MODELS else 0)
with col_ctrl2:
    avail = get_available_models(st.session_state.get("gemini_api_key"))
    llm_options = avail if avail else ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", "gemini-flash-latest", "gemini-1.5-flash", "gemini-1.5-pro"]
    if st.session_state["llm_model"] not in llm_options:
        st.session_state["llm_model"] = llm_options[0]
    llm_choice = st.selectbox(
        "Cloud LLM to compare", 
        options=llm_options, 
        index=llm_options.index(st.session_state["llm_model"])
    )


compare_button = st.button("⚖️ Generate & Compare Answers", type="primary", use_container_width=True)

# Comparison state persistence for export button
if "last_comparison" not in st.session_state:
    st.session_state["last_comparison"] = None

if compare_button:
    if not query.strip():
        st.error("Please enter a prompt first.")
    elif not is_api_key_configured():
        st.error("Gemini API key is not configured. Please go to Settings and enter your key first.")
    else:
        st.info("Generating answers from both models... Please wait.")
        
        # Web Search Context Injection (If enabled)
        web_context = ""
        if web_search_compare:
            with st.spinner("🔍 Web Search running..."):
                search_results = search_web(query)
                if search_results:
                    web_context = "### Web Search Snippets:\n"
                    for r in search_results:
                        web_context += f"- **{r['title']}**: {r['snippet']}\n"
                    st.success("Web context retrieved.")
        
        # 1. Local SLM Execution
        slm_start = time.time()
        slm_ans = ""
        slm_stats = {}
        
        # 2. Cloud LLM Execution
        llm_start = time.time()
        llm_ans = ""
        llm_stats = {}
        
        col_slm, col_llm = st.columns(2)
        
        with col_slm:
            st.subheader(f"💻 Local SLM ({slm_choice.split(' ')[0]})")
            slm_placeholder = st.empty()
            slm_placeholder.markdown("*Initializing local model...*")
            
            try:
                # Load model settings
                sys_p = get_system_prompt("slm")
                
                final_slm_prompt = query
                if web_context:
                    final_slm_prompt = f"{web_context}\n\nUse the web search results to answer: {query}"
                    
                formatted_p = f"System: {sys_p}\nQuery: {final_slm_prompt}\nAssistant:"
                
                # Fetch parameters from session
                temp_local = st.session_state["local_temp"]
                max_local = st.session_state["local_max_tokens"]
                
                # Track resources for local SLM
                tracker_slm = ResourceTracker()
                
                res_slm = generate_local_slm_response(
                    prompt=formatted_p,
                    model_name=slm_choice,
                    temperature=temp_local,
                    max_tokens=max_local,
                    stream=True
                )
                
                for chunk in res_slm["stream"]:
                    if isinstance(chunk, dict):
                        slm_stats = chunk
                    else:
                        slm_ans += chunk
                        slm_placeholder.markdown(slm_ans + "▌")
                slm_placeholder.markdown(slm_ans)
                
                # Get metrics
                metrics_slm = tracker_slm.get_metrics()
                slm_stats["cpu_percent"] = metrics_slm["cpu_peak_percent"]
                slm_stats["ram_percent"] = metrics_slm["ram_peak_percent"]
                
            except Exception as e:
                slm_placeholder.error(f"Error running Local SLM: {e}")
                slm_ans = f"Error: {e}"
                slm_stats = {"model": "N/A", "response_time": 0.1, "input_tokens": 0, "output_tokens": 0, "cost": 0.0, "cpu_percent": 0.0, "ram_percent": 0.0}
                
        with col_llm:
            st.subheader(f"☁️ Cloud LLM ({llm_choice})")
            llm_placeholder = st.empty()
            llm_placeholder.markdown("*Initializing cloud API...*")
            
            try:
                sys_p = get_system_prompt("llm")
                temp_cloud = st.session_state["cloud_temp"]
                max_cloud = st.session_state["cloud_max_tokens"]
                
                final_llm_prompt = query
                if web_context:
                    final_llm_prompt = f"{web_context}\n\nUse the web search results above to answer: {query}"
                
                # Track resources for Cloud LLM (network calls only, CPU usage should be lower)
                tracker_llm = ResourceTracker()
                
                res_llm = generate_llm_response(
                    prompt=final_llm_prompt,
                    system_prompt=sys_p,
                    model_name=llm_choice,
                    temperature=temp_cloud,
                    max_tokens=max_cloud,
                    stream=True
                )
                
                for chunk in res_llm["stream"]:
                    if isinstance(chunk, dict):
                        llm_stats = chunk
                    else:
                        llm_ans += chunk
                        llm_placeholder.markdown(llm_ans + "▌")
                llm_placeholder.markdown(llm_ans)
                
                # Get metrics
                metrics_llm = tracker_llm.get_metrics()
                llm_stats["cpu_percent"] = metrics_llm["cpu_peak_percent"]
                llm_stats["ram_percent"] = metrics_llm["ram_peak_percent"]
                
            except Exception as e:
                llm_placeholder.error(f"Error running Cloud LLM: {e}")
                llm_ans = f"Error: {e}"
                llm_stats = {"model": "N/A", "response_time": 0.1, "input_tokens": 0, "output_tokens": 0, "cost": 0.0, "cpu_percent": 0.0, "ram_percent": 0.0}
                
        # 3. Stats Comparison Dashboard
        st.markdown("---")
        st.header("📊 Performance Metrics Comparison")
        
        # Calculate tokens/sec
        slm_time = slm_stats.get("response_time", 1.0)
        slm_toks = slm_stats.get("output_tokens", 0)
        slm_speed = slm_toks / slm_time if slm_time > 0 else 0
        
        llm_time = llm_stats.get("response_time", 1.0)
        llm_toks = llm_stats.get("output_tokens", 0)
        llm_speed = llm_toks / llm_time if llm_time > 0 else 0
        
        metrics_data = {
            "Metric": ["Model Name", "Inference Time (sec)", "Output Tokens", "Generation Speed (tokens/sec)", "Estimated Cost (USD)", "Peak CPU Load %", "Peak RAM Usage %", "Location"],
            f"Local SLM ({slm_choice.split(' ')[0]})": [
                slm_stats.get("model", "Local SLM"),
                f"{slm_time:.3f}s",
                slm_toks,
                f"{slm_speed:.2f} t/s",
                "Free ($0.00)",
                f"{slm_stats.get('cpu_percent', 0.0):.1f}%",
                f"{slm_stats.get('ram_percent', 0.0):.1f}%",
                "On-Device (Offline)"
            ],
            f"Cloud LLM ({llm_choice})": [
                llm_stats.get("model", "Cloud LLM"),
                f"{llm_time:.3f}s",
                llm_toks,
                f"{llm_speed:.2f} t/s",
                f"${llm_stats.get('cost', 0.0):.6f}",
                f"{llm_stats.get('cpu_percent', 0.0):.1f}%",
                f"{llm_stats.get('ram_percent', 0.0):.1f}%",
                "Google Cloud API"
            ]
        }
        
        df = pd.DataFrame(metrics_data)
        st.table(df)
        
        # Plotting comparison charts
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("##### ⏱️ Latency (Lower is Better)")
            chart_df = pd.DataFrame({
                "Model": ["Local SLM", "Cloud LLM"],
                "Response Time (s)": [slm_time, llm_time]
            })
            fig = px.bar(chart_df, x="Model", y="Response Time (s)", color="Model", 
                         color_discrete_map={"Local SLM": "#81a1c1", "Cloud LLM": "#b48ead"})
            st.plotly_chart(fig, use_container_width=True)
            
        with chart_col2:
            st.markdown("##### ⚡ Speed (Higher is Better)")
            speed_df = pd.DataFrame({
                "Model": ["Local SLM", "Cloud LLM"],
                "Speed (tokens/sec)": [slm_speed, llm_speed]
            })
            fig2 = px.bar(speed_df, x="Model", y="Speed (tokens/sec)", color="Model",
                          color_discrete_map={"Local SLM": "#8fbcbb", "Cloud LLM": "#bf616a"})
            st.plotly_chart(fig2, use_container_width=True)
            
        # 4. LLM Automated Evaluation Report
        st.markdown("---")
        st.header("🧠 Automated AI Critique & Scorecard")
        
        eval_placeholder = st.empty()
        eval_placeholder.markdown("🤖 *Requesting cloud evaluator report comparing reasoning and accuracy trade-offs...*")
        
        full_eval = ""
        try:
            eval_prompt = get_comparison_prompt(query, slm_ans, llm_ans)
            res_eval = generate_llm_response(
                prompt=eval_prompt,
                system_prompt="You are an expert AI evaluator and prompt engineer.",
                model_name=llm_choice,
                temperature=0.2,
                max_tokens=1500,
                stream=True
            )
            
            for chunk in res_eval["stream"]:
                if not isinstance(chunk, dict):
                    full_eval += chunk
                    eval_placeholder.markdown(full_eval + "▌")
            eval_placeholder.markdown(full_eval)
            
        except Exception as e:
            full_eval = f"Failed to generate evaluator report: {e}"
            eval_placeholder.error(full_eval)

        # Save results in session state for export
        st.session_state["last_comparison"] = {
            "query": query,
            "slm_model": slm_choice,
            "slm_ans": slm_ans,
            "slm_stats": slm_stats,
            "llm_model": llm_choice,
            "llm_ans": llm_ans,
            "llm_stats": llm_stats,
            "eval_report": full_eval
        }

# Render export button if comparison is saved in state
if st.session_state["last_comparison"]:
    st.markdown("---")
    lc = st.session_state["last_comparison"]
    
    # Construct Markdown Report
    report_md = f"""# AI Model Comparison Report
**Generated on:** {time.strftime('%Y-%m-%d %H:%M:%S')}

## ❓ User Prompt
> {lc['query']}

---

## 💻 Local SLM: {lc['slm_model']}
### Response:
{lc['slm_ans']}

### Metrics:
- **Latency:** {lc['slm_stats'].get('response_time', 0.0):.3f}s
- **Output Tokens:** {lc['slm_stats'].get('output_tokens', 0)}
- **Peak CPU Load:** {lc['slm_stats'].get('cpu_percent', 0.0):.1f}%
- **Peak RAM Usage:** {lc['slm_stats'].get('ram_percent', 0.0):.1f}%
- **Cost:** Free

---

## ☁️ Cloud LLM: {lc['llm_model']}
### Response:
{lc['llm_ans']}

### Metrics:
- **Latency:** {lc['llm_stats'].get('response_time', 0.0):.3f}s
- **Output Tokens:** {lc['llm_stats'].get('output_tokens', 0)}
- **Peak CPU Load:** {lc['llm_stats'].get('cpu_percent', 0.0):.1f}%
- **Peak RAM Usage:** {lc['llm_stats'].get('ram_percent', 0.0):.1f}%
- **Cost:** ${lc['llm_stats'].get('cost', 0.0):.6f}

---

## 🧠 Evaluator Critique & Scorecard
{lc['eval_report']}
"""
    
    st.download_button(
        "📥 Download Comparison Report as Markdown",
        data=report_md,
        file_name=f"model_comparison_report_{int(time.time())}.md",
        use_container_width=True
    )
