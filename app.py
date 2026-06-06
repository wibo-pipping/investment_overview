import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Private Portfolio Spread Analyzer")
st.title("🛡️ Portfolio Spread & Gap Analyzer")
st.markdown("---")

# ==========================================
# 1. DEFINE GLOBAL BENCHMARK TEMPLATES
# ==========================================
# Standard global market caps (MSCI ACWI benchmarks)
TARGET_GEO = {
    'North America': 62.0,
    'Europe': 16.0,
    'Asia/Pacific': 12.0,
    'Emerging Markets': 10.0
}

TARGET_SECTORS = {
    'Technology': 24.0,
    'Financial Services': 15.0,
    'Healthcare': 12.0,
    'Consumer Cyclical': 11.0,
    'Industrials': 10.0,
    'Communication Services': 7.0,
    'Consumer Defensive': 6.0,
    'Energy': 5.0,
    'Basic Materials': 4.0,
    'Utilities': 3.0,
    'Real Estate': 3.0
}

# ==========================================
# 2. LOAD & FETCH DATA (LOCAL & PRIVATE)
# ==========================================
@st.cache_data(ttl=3600)
def load_and_fetch_data():
    try:
        df = pd.read_csv("portfolio.csv")
    except FileNotFoundError:
        st.error("Could not find 'portfolio.csv'. Please create it in this directory.")
        return None, None, None

    geo_allocations = {}
    sector_allocations = {}
    total_portfolio_value = 0.0
    
    # Temporary storage for calculated rows
    portfolio_rows = []

    for _, row in df.iterrows():
        ticker_str = str(row['Ticker']).strip()
        shares = float(row['Shares'])
        asset_type = str(row['Asset_Type']).strip()

        # Fetch public data without sending personal details
        ticker = yf.Ticker(ticker_str)
        
        # Get current price to calculate weight
        price = ticker.fast_info.get('lastPrice', None) or ticker.info.get('regularMarketPrice', 1.0)
        position_value = price * shares
        total_portfolio_value += position_value

        # Initialize holding structures
        geo_data = {}
        sector_data = {}

        if asset_type.upper() == 'ETF':
            # Extract ETF internal allocations if available
            fund_info = ticker.info
            # Note: yfinance structures vary; this handles common structures or falls back gracefully
            geo_data = fund_info.get('regionalExposure', {}) or fund_info.get('geographicAllocation', {})
            sector_data = fund_info.get('sectorWeightings', {}) or fund_info.get('sectorAllocation', {})
            
            # Simple fallback percentages if API format is nested/empty
            if not geo_data: geo_data = {'North America': 100.0} 
            if not sector_data: sector_data = {'Technology': 100.0}

        elif asset_type.upper() == 'STOCK':
            # Individual stock maps 100% to its own sector/region
            info = ticker.info
            sector = info.get('sector', 'Unknown Technology')
            country = info.get('country', 'United States')
            
            # Rough country to continent mapping for template comparison
            region = 'North America' if country in ['United States', 'Canada'] else 'Europe'
            geo_data = {region: 1.0}
            sector_data = {sector: 1.0}
            
        elif asset_type.upper() in ['BOND', 'OBLIGATION']:
            geo_data = {'Fixed Income / Global': 1.0}
            sector_data = {'Fixed Income': 1.0}

        # Convert fractional data (0.25) to percentage (25.0) if needed
        for k, v in geo_data.items():
            val = v * 100 if v <= 1.0 else v
            geo_allocations[k] = geo_allocations.get(k, 0.0) + (val * (position_value / 100))
        
        for k, v in sector_data.items():
            val = v * 100 if v <= 1.0 else v
            # Map yfinance naming conventions to standard template names
            clean_k = k.replace('_', ' ').title()
            sector_allocations[clean_k] = sector_allocations.get(clean_k, 0.0) + (val * (position_value / 100))

        portfolio_rows.append({
            "Ticker": ticker_str,
            "Type": asset_type,
            "Value": round(position_value, 2)
        })

    # Normalize allocations back to true percentages of the total portfolio
    final_geo = {k: (v / total_portfolio_value) * 100 for k, v in geo_allocations.items()}
    final_sector = {k: (v / total_portfolio_value) * 100 for k, v in sector_allocations.items()}
    
    return pd.DataFrame(portfolio_rows), final_geo, final_sector

portfolio_df, current_geo, current_sector = load_and_fetch_data()

# ==========================================
# 3. RENDER DASHBOARD UI
# ==========================================
if portfolio_df is not None:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📋 Active Assets Monitored")
        st.dataframe(portfolio_df, use_container_width=True, hide_index=True)
        st.caption("Your exact holdings are processed in-memory locally and are never saved online.")

    with col2:
        st.subheader("💡 Strategic Gap Diagnostics")
        st.info("The charts below highlight where your portfolio deviates from an All-World baseline. Look for negative values to identify missing criteria for your next ETF selection.")

    st.markdown("---")
    tab1, tab2 = st.tabs(["🌍 Geographic Gap Analysis", "🏭 Sector Gap Analysis"])

    # --- TAB 1: GEOGRAPHY ---
    with tab1:
        geo_gap_data = []
        for region, target in TARGET_GEO.items():
            actual = current_geo.get(region, 0.0)
            gap = actual - target
            geo_gap_data.append({"Region": region, "Actual %": round(actual, 2), "Target %": target, "Gap": round(gap, 2)})
        
        geo_gap_df = pd.DataFrame(geo_gap_data)
        
        c1, c2 = st.columns(2)
        with c1:
            fig_geo = go.Figure(data=[
                go.Bar(name='Your Portfolio', x=geo_gap_df['Region'], y=geo_gap_df['Actual %'], marker_color='#3366CC'),
                go.Bar(name='Global Template', x=geo_gap_df['Region'], y=geo_gap_df['Target %'], marker_color='#CCCCCC')
            ])
            fig_geo.update_layout(barmode='group', title="Allocation vs Global Target")
            st.plotly_chart(fig_geo, use_container_width=True)
            
        with c2:
            # Color bars red if underweight, green if overweight
            colors = ['#EF553B' if val < 0 else '#00CC96' for val in geo_gap_df['Gap']]
            fig_geo_gap = go.Figure(go.Bar(x=geo_gap_df['Region'], y=geo_gap_df['Gap'], marker_color=colors))
            fig_geo_gap.update_layout(title="Your Strategic Blindspots (Negative = Underweight)")
            st.plotly_chart(fig_geo_gap, use_container_width=True)

    # --- TAB 2: SECTORS ---
    with tab2:
        sector_gap_data = []
        for sector, target in TARGET_SECTORS.items():
            # Try matching variations in naming
            actual = current_sector.get(sector, 0.0)
            gap = actual - target
            sector_gap_data.append({"Sector": sector, "Actual %": round(actual, 2), "Target %": target, "Gap": round(gap, 2)})
            
        sector_gap_df = pd.DataFrame(sector_gap_data)
        
        c1, c2 = st.columns(2)
        with c1:
            fig_sec = go.Figure(data=[
                go.Bar(name='Your Portfolio', x=sector_gap_df['Sector'], y=sector_gap_df['Actual %'], marker_color='#109618'),
                go.Bar(name='Global Template', x=sector_gap_df['Sector'], y=sector_gap_df['Target %'], marker_color='#CCCCCC')
            ])
            fig_sec.update_layout(barmode='group', title="Sector Allocation vs Global Template")
            st.plotly_chart(fig_sec, use_container_width=True)
            
        with c2:
            colors = ['#EF553B' if val < 0 else '#00CC96' for val in sector_gap_df['Gap']]
            fig_sec_gap = go.Figure(go.Bar(x=sector_gap_df['Sector'], y=sector_gap_df['Gap'], marker_color=colors))
            fig_sec_gap.update_layout(title="Sector Gaps (Negative means you are missing exposure)")
            st.plotly_chart(fig_sec_gap, use_container_width=True)
            