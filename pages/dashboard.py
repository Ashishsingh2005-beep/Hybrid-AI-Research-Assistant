import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.memory import ConversationMemory
from utils.system_monitor import get_system_resources
from datetime import datetime
import random

st.set_page_config(page_title="Analytics Dashboard - Hybrid AI Assistant", layout="wide")

st.markdown("""
<style>
    .metric-box {
        background-color: #1b1e24;
        border: 1px solid #2e3440;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-box-title {
        font-size: 13px;
        color: #d8dee9;
        text-transform: uppercase;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .metric-box-value {
        font-size: 32px;
        font-weight: bold;
        color: #88c0d0;
    }
    .metric-box-sub {
        font-size: 11px;
        color: #a3be8c;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 ROI & Cost Savings Dashboard")
st.markdown("Monitor performance, token throughput, resource footprint, and estimate cost savings from Local SLM routing.")

# Load metrics
metrics = ConversationMemory.get_all_persistent_metrics()

# Handle simulated metrics generation for testing
if not metrics:
    st.info("💡 **No real-world metrics logged yet.** Click the button below to generate 50 mock queries to see how this interactive dashboard visualizes your savings.")
    if st.button("📈 Populate Demo Analytics Data"):
        # Generate 50 mock records
        demo_metrics = []
        models_list = ["SmolLM2-135M-Instruct (145MB)", "Qwen2.5-0.5B-Instruct (398MB)", "Phi-3-Mini-4K-Instruct (2.2GB)", "gemini-2.5-flash", "gemini-1.5-pro"]
        
        start_ts = datetime.now().timestamp() - (50 * 3600) # over the last 2 days
        
        for i in range(50):
            model = random.choice(models_list)
            is_slm = "gemini" not in model.lower()
            
            input_toks = random.randint(15, 120) if is_slm else random.randint(150, 4000)
            output_toks = random.randint(30, 256) if is_slm else random.randint(100, 1000)
            
            resp_time = random.uniform(0.2, 2.5) if is_slm else random.uniform(1.2, 5.0)
            if "Phi-3" in model:
                resp_time = random.uniform(1.5, 4.5)
                
            cpu = random.uniform(30.0, 85.0) if is_slm else random.uniform(5.0, 15.0)
            ram = random.uniform(45.0, 75.0) if is_slm else random.uniform(40.0, 50.0)
            
            # pricing estimation
            rate_in = 0.075 / 1000000
            rate_out = 0.30 / 1000000
            if "pro" in model:
                rate_in = 1.25 / 1000000
                rate_out = 5.00 / 1000000
                
            cost = 0.0 if is_slm else (input_toks * rate_in + output_toks * rate_out)
            
            ts = datetime.fromtimestamp(start_ts + (i * 3600)).isoformat()
            
            demo_metrics.append({
                "model": model,
                "response_time": resp_time,
                "input_tokens": input_toks,
                "output_tokens": output_toks,
                "cost": cost,
                "cpu_percent": cpu,
                "ram_percent": ram,
                "timestamp": ts
            })
            
        # Write to file
        for item in demo_metrics:
            mem = ConversationMemory()
            mem._save_metric_to_persistent_file(item)
        st.success("Successfully generated demo data!")
        st.rerun()

# If we have metrics, build dashboard
if metrics:
    df = pd.DataFrame(metrics)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["is_slm"] = df["model"].apply(lambda x: "gemini" not in x.lower())
    
    # Calculate savings
    # Savings calculation: for every SLM query, calculate what it WOULD have cost on gemini-2.5-flash
    flash_rate_in = 0.075 / 1_000_000
    flash_rate_out = 0.30 / 1_000_000
    
    def calc_saved(row):
        if row["is_slm"]:
            # what it would cost on Gemini Flash
            return (row["input_tokens"] * flash_rate_in) + (row["output_tokens"] * flash_rate_out)
        return 0.0
        
    df["cost_saved"] = df.apply(calc_saved, axis=1)
    
    # Cumulative stats
    total_requests = len(df)
    total_tokens = df["input_tokens"].sum() + df["output_tokens"].sum()
    total_cost_actual = df["cost"].sum()
    total_cost_saved = df["cost_saved"].sum()
    
    # Layout 1: KPIs
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    
    with col_kpi1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-box-title">Total Requests</div>
            <div class="metric-box-value">{total_requests}</div>
            <div class="metric-box-sub">Offline SLM + Cloud LLM</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_kpi2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-box-title">Tokens Processed</div>
            <div class="metric-box-value">{total_tokens:,}</div>
            <div class="metric-box-sub">{df['input_tokens'].sum():,} in | {df['output_tokens'].sum():,} out</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_kpi3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-box-title">Actual API Spend</div>
            <div class="metric-box-value">${total_cost_actual:.4f}</div>
            <div class="metric-box-sub">Cloud LLM Costs</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_kpi4:
        st.markdown(f"""
        <div class="metric-box" style="border-color: #a3be8c;">
            <div class="metric-box-title" style="color: #a3be8c;">Estimated Savings (ROI)</div>
            <div class="metric-box-value" style="color: #a3be8c;">${total_cost_saved:.4f}</div>
            <div class="metric-box-sub" style="color: #d8dee9;">By running Local models</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    # Layout 2: Charts
    col_ch1, col_ch2 = st.columns(2)
    
    with col_ch1:
        st.subheader("🤖 Request Routing Split")
        # Split between local SLM and Cloud LLM
        routing_counts = df["is_slm"].value_counts().reset_index()
        routing_counts.columns = ["Engine Type", "Count"]
        routing_counts["Engine Type"] = routing_counts["Engine Type"].map({True: "Local SLM (Free)", False: "Cloud LLM (Paid)"})
        
        fig_pie = px.pie(
            routing_counts, 
            values="Count", 
            names="Engine Type",
            color="Engine Type",
            color_discrete_map={"Local SLM (Free)": "#8fbcbb", "Cloud LLM (Paid)": "#bf616a"},
            hole=0.4
        )
        fig_pie.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#e5e9f0',
            margin=dict(t=10, b=10, l=10, r=10)
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col_ch2:
        st.subheader("💰 Accumulated Cost Savings Over Time")
        # Compute cumulative savings
        df_sorted = df.sort_values("timestamp")
        df_sorted["cumulative_savings"] = df_sorted["cost_saved"].cumsum()
        df_sorted["cumulative_spend"] = df_sorted["cost"].cumsum()
        
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=df_sorted["timestamp"], 
            y=df_sorted["cumulative_savings"],
            mode='lines+markers',
            name='Cumulative Savings ($)',
            line=dict(color='#a3be8c', width=3),
            marker=dict(size=6)
        ))
        fig_line.add_trace(go.Scatter(
            x=df_sorted["timestamp"], 
            y=df_sorted["cumulative_spend"],
            mode='lines',
            name='Cumulative API Spend ($)',
            line=dict(color='#bf616a', width=2, dash='dash')
        ))
        fig_line.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#e5e9f0',
            xaxis=dict(gridcolor='#2e3440'),
            yaxis=dict(gridcolor='#2e3440'),
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_line, use_container_width=True)

    col_ch3, col_ch4 = st.columns(2)
    
    with col_ch3:
        st.subheader("⏱️ Average Latency by Model")
        model_latency = df.groupby("model")["response_time"].mean().reset_index()
        model_latency = model_latency.sort_values("response_time")
        
        fig_lat = px.bar(
            model_latency,
            x="model",
            y="response_time",
            labels={"model": "Model Name", "response_time": "Avg Latency (sec)"},
            color="response_time",
            color_continuous_scale="Viridis"
        )
        fig_lat.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#e5e9f0',
            xaxis=dict(gridcolor='#2e3440'),
            yaxis=dict(gridcolor='#2e3440'),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_lat, use_container_width=True)
        
    with col_ch4:
        st.subheader("🧠 System Resource Usage during Run")
        # Peak resources
        res_df = df[df["is_slm"]].copy()
        if not res_df.empty:
            model_resources = res_df.groupby("model")[["cpu_percent", "ram_percent"]].mean().reset_index()
            
            fig_res = go.Figure()
            fig_res.add_trace(go.Bar(
                x=model_resources["model"],
                y=model_resources["cpu_percent"],
                name="Average CPU %",
                marker_color='#88c0d0'
            ))
            fig_res.add_trace(go.Bar(
                x=model_resources["model"],
                y=model_resources["ram_percent"],
                name="Average RAM %",
                marker_color='#b48ead'
            ))
            fig_res.update_layout(
                barmode='group',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#e5e9f0',
                xaxis=dict(gridcolor='#2e3440'),
                yaxis=dict(gridcolor='#2e3440')
            )
            st.plotly_chart(fig_res, use_container_width=True)
        else:
            st.write("No Local SLM queries executed yet to show resource logs.")

    st.markdown("---")
    
    # Reset button
    st.subheader("⚙️ Maintenance")
    if st.button("🗑️ Reset & Clear Analytics Database"):
        ConversationMemory.clear_all_persistent_metrics()
        st.success("Analytics logs successfully cleared.")
        st.rerun()

# Always show current resource state in sidebar
resources = get_system_resources()
with st.sidebar:
    st.markdown("---")
    st.header("🖥️ System Status")
    st.metric("Global CPU Usage", f"{resources['cpu_percent']:.1f}%")
    st.progress(resources['cpu_percent'] / 100.0)
    
    st.metric("Global RAM Usage", f"{resources['ram_percent']:.1f}%", f"{resources['ram_available_gb']:.1f} GB Free")
    st.progress(resources['ram_percent'] / 100.0)
    
    st.caption(f"App Process Memory: {resources['process_ram_gb']:.2f} GB")
