import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.templates import TARGET_SECTORS

def render_sector_analysis(current_sector):
    """Renders the entire sector gap analysis UI."""
    sector_gap_data = []
    for sector, target in TARGET_SECTORS.items():
        actual = current_sector.get(sector, 0.0)
        gap = actual - target
        sector_gap_data.append({
            "Sector": sector, 
            "Actual %": round(actual, 2), 
            "Target %": target, 
            "Gap": round(gap, 2)
        })
        
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