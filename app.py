import streamlit as st

# Engine Imports
from src.analytics import fetch_raw_portfolio_data, process_portfolio_metrics

# View Module UI Components Imports
from src.views.geo_view import render_geo_analysis
from src.views.sector_view import render_sector_analysis
from src.views.currency_view import render_currency_analysis

# Base App Setup
st.set_page_config(layout="wide", page_title="Private Portfolio Spread Analyzer")
st.title("🛡️ Portfolio Spread & Gap Analyzer")
st.markdown("---")

# Data Orchestration
@st.cache_data(ttl=3600)
def get_cached_dashboard_data():
    raw_df = fetch_raw_portfolio_data()
    return process_portfolio_metrics(raw_df)

try:
    portfolio_df, current_geo, current_sector = get_cached_dashboard_data()
except FileNotFoundError:
    st.error("Could not find 'portfolio.csv'. Please check your root directory.")
    st.stop()

# Header Presentation Layer
col1, col2 = st.columns([4, 3])
with col1:
    st.subheader("📋 Active Assets Monitored")
    st.dataframe(portfolio_df, use_container_width=True, hide_index=True)
with col2:
    st.subheader("💡 Strategic Gap Diagnostics")
    st.info("The charts below highlight where your portfolio deviates from an All-World baseline.")

st.markdown("---")

# Main Tab Routing Engine
tab1, tab2, tab3 = st.tabs([
    "🌍 Geographic Gap Analysis", 
    "🏭 Sector Gap Analysis", 
    "💱 Currency Risk Profile"
])

with tab1:
    render_geo_analysis(current_geo)

with tab2:
    render_sector_analysis(current_sector)

with tab3:
    render_currency_analysis(current_geo)