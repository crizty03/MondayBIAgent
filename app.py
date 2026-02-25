import streamlit as st
import requests
import json
import os

st.set_page_config(page_title="Monday.com Founder BI", page_icon="📈", layout="centered")

st.markdown("""
<style>
    /* Premium Dark Theme Overrides */
    .stApp {
        background-color: #0E1117;
    }
    
    h1, h2, h3, h4 {
        color: #F0F2F6 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
    }
    
    .stChatMessage {
        background-color: transparent !important;
        padding: 1rem 0 !important;
        border-bottom: 1px solid #1E232F;
    }
    
    .stChatMessage [data-testid="stMarkdownContainer"] {
        color: #C9D1D9 !important;
        font-size: 1.05rem;
        line-height: 1.6;
    }
    
    /* Elegant Info Cards */
    div.stAlert > div {
        background-color: #1a1e27 !important;
        border: 1px solid #2d3340;
        border-radius: 8px;
        color: #E2E8F0 !important;
        padding: 1rem !important;
    }
    
    /* Warning/Error styling */
    div[data-baseweb="notification"] {
        border-radius: 6px;
    }
    
    /* Clean Metric containers */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #3b82f6 !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.95rem !important;
        color: #8b949e !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Sector Breakdown Table */
    .sector-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
    }
    .sector-table th, .sector-table td {
        padding: 8px;
        text-align: left;
        border-bottom: 1px solid #2d3340;
        color: #C9D1D9;
    }
    .sector-table th {
        color: #8b949e;
        font-weight: 500;
        text-transform: uppercase;
        font-size: 0.85rem;
    }
    
</style>
""", unsafe_allow_html=True)

API_URL = os.environ.get("FASTAPI_URL", "http://localhost:8000") + "/api/chat"

st.title("📈 Founder BI Agent")
st.markdown("<p style='color: #8b949e; font-size: 1.1rem; margin-bottom: 2rem;'>Real-time executive insights powered by Monday.com and Gemini.</p>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

def display_message(role, msg_type, content, index=0):
    with st.chat_message(role):
        if msg_type == "report":
            st.markdown(f"<h2 style='color: #fff; margin-bottom: 20px;'>{content['title']}</h2>", unsafe_allow_html=True)
            
            # Use columns and metrics for a dashboard feel
            st.markdown("### 💰 Financial Health")
            
            try:
                # Parse the strings back to numbers if needed, or extract from raw data if available. 
                # Since report_generator sends formatted strings, we'll display them beautifully.
                rev_text = content['revenue_summary'].split('|')[0].replace('Closed Revenue: ', '').strip()
                win_rate = content['revenue_summary'].split('|')[1].replace('Win Rate: ', '').strip() if '|' in content['revenue_summary'] else 'N/A'
                pipe_text = content['pipeline_health'].replace('Open Pipeline: ', '').strip()
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Closed Revenue", rev_text)
                m2.metric("Open Pipeline", pipe_text)
                m3.metric("Win Rate", win_rate)
            except Exception:
                st.info(content['revenue_summary'])
                st.info(content['pipeline_health'])

            st.markdown("---")
            
            c1, c2 = st.columns([1.5, 1])
            with c1:
                st.markdown("### 🏢 Sector Breakdown")
                sectors = content.get('sector_breakdown', {})
                if sectors:
                    table_html = "<table class='sector-table'><tr><th>Sector</th><th>Revenue Generated</th></tr>"
                    # Sort by highest revenue
                    sorted_sectors = sorted(sectors.items(), key=lambda x: x[1], reverse=True)
                    for s_name, s_val in sorted_sectors:
                        name = s_name if s_name.strip() else "Uncategorized"
                        table_html += f"<tr><td>{name}</td><td>${s_val:,.2f}</td></tr>"
                    table_html += "</table>"
                    st.markdown(table_html, unsafe_allow_html=True)
                else:
                    st.write("No sector data available.")
                    
            with c2:
                st.markdown("### ⚙ Operations")
                try:
                    active = content['operational_status'].split('|')[0].replace('Active Projects: ', '').strip()
                    delayed = content['operational_status'].split('|')[1].replace('Delayed Projects: ', '').strip()
                    st.metric("Running Projects", active)
                    st.metric("Delayed Ops", delayed, delta="- Attention Required" if int(delayed) > 0 else "On Track", delta_color="inverse")
                except:
                    st.info(content['operational_status'])
                    
                st.markdown("### 🚨 Risks")
                for flag in content['risk_flags']:
                    if "No critical" in flag:
                        st.success(flag)
                    else:
                        st.error(flag)

            st.markdown("---")
            report_md = f"""# {content['title']}
## Revenue Summary
{content['revenue_summary']}

## Pipeline Health
{content['pipeline_health']}

## Operational Status
{content['operational_status']}

## Risk Flags
""" + "\n".join([f"- {flag}" for flag in content['risk_flags']])
            st.download_button("📩 Download PDF/Markdown", report_md, file_name="leadership_update.md", mime="text/markdown", key=f"download_report_{index}")
                
            if content.get('data_quality_warnings') and content['data_quality_warnings'][0] != "Data quality is within acceptable bounds.":
                 st.markdown("#### ⚠ Data Quality Warnings")
                 for w in content['data_quality_warnings']:
                     st.warning(w)
        else:
            st.markdown(content)

for i, msg in enumerate(st.session_state.messages):
    display_message(msg["role"], msg["type"], msg["content"], i)

if prompt := st.chat_input("Ask a question (e.g., 'Prepare leadership update')..."):
    st.session_state.messages.append({"role": "user", "content": prompt, "type": "text"})
    display_message("user", "text", prompt, len(st.session_state.messages) - 1)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing data from Monday.com..."):
            try:
                response = requests.post(API_URL, json={"query": prompt}, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    res_type = data.get("type", "text")
                    res_content = data.get("response", "Error interpreting data.")
                    
                    st.session_state.messages.append({"role": "assistant", "content": res_content, "type": res_type})
                    st.rerun()
                else:
                    st.error(f"Backend error: {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to connect to backend at {API_URL}: {e}")
