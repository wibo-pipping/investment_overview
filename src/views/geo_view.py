import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.templates import TARGET_GEO

def render_geo_analysis(current_geo):
    """Renders the entire geographic gap analysis UI."""
    geo_gap_data = []
    for region, target in TARGET_GEO.items():
        actual = current_geo.get(region, 0.0)
        gap = actual - target
        geo_gap_data.append({
            "Region": region, 
            "Actual %": round(actual, 2), 
            "Target %": target, 
            "Gap": round(gap, 2)
        })
    
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
        colors = ['#EF553B' if val < 0 else '#00CC96' for val in geo_gap_df['Gap']]
        fig_geo_gap = go.Figure(go.Bar(x=geo_gap_df['Region'], y=geo_gap_df['Gap'], marker_color=colors))
        fig_geo_gap.update_layout(title="Your Strategic Blindspots (Negative = Underweight)")
        st.plotly_chart(fig_geo_gap, use_container_width=True)