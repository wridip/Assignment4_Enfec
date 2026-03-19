import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="RAG App with Caching", layout="wide")

API_BASE_URL = "http://localhost:8000/api"

st.title("🤖 RAG System with Llama 3 & Caching")

tabs = st.tabs(["💬 Chat", "📊 Metrics Dashboard"])

# Chat Tab
with tabs[0]:
    st.header("Ask a question about Company Policies")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "meta" in message:
                st.caption(message["meta"])

    if prompt := st.chat_input("What would you like to know?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                response = requests.post(f"{API_BASE_URL}/ask", json={"question": prompt})
                if response.status_code == 200:
                    data = response.json()
                    answer = data["answer"]
                    st.markdown(answer)
                    
                    cache_status = "Cache Hit" if data["cache_used"] else "Cache Miss"
                    cache_type = f" ({data['cache_type']})" if "cache_type" in data else ""
                    meta = f"⏱️ {data['response_time']}ms | 💾 {cache_status}{cache_type}"
                    
                    if "sources" in data:
                        meta += f" | 📄 Sources: {', '.join(data['sources'])}"
                    
                    st.caption(meta)
                    st.session_state.messages.append({"role": "assistant", "content": answer, "meta": meta})
                else:
                    st.error(f"Error: {response.status_code}")
            except Exception as e:
                st.error(f"Failed to connect to backend: {e}")

# Metrics Tab
with tabs[1]:
    st.header("System Performance")
    
    if st.button("Refresh Metrics"):
        try:
            res = requests.get(f"{API_BASE_URL}/metrics")
            if res.status_code == 200:
                m = res.json()
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Queries", m["total_queries"])
                col2.metric("Cache Hit Rate", f"{m['hit_rate']}%")
                col3.metric("Avg Response Time", f"{m['avg_response_time']}ms")
                col4.metric("Hits / Misses", f"{m['hits']} / {m['misses']}")
                
                # Charts
                c1, c2 = st.columns(2)
                
                # Hit/Miss Pie Chart
                fig_pie = px.pie(
                    values=[m["hits"], m["misses"]], 
                    names=["Hits", "Misses"],
                    title="Cache Efficiency",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                c1.plotly_chart(fig_pie)
                
                # Cache Types Bar Chart
                fig_bar = px.bar(
                    x=["KV Hits", "Semantic Hits"],
                    y=[m["kv_hits"], m["semantic_hits"]],
                    title="Cache Type Distribution",
                    labels={'x': 'Type', 'y': 'Count'}
                )
                c2.plotly_chart(fig_bar)
                
            else:
                st.error("Failed to fetch metrics")
        except Exception as e:
            st.error(f"Error fetching metrics: {e}")
    else:
        st.info("Click 'Refresh Metrics' to see current performance data.")
