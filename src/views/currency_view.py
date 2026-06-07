import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def render_currency_analysis(current_geo):
    """Renders the underlying currency vulnerability risk matrix UI."""
    st.subheader("💱 True Underlying Currency Exposure")
    st.markdown(
        "This breakdown estimates the currency of the *underlying assets* you own, "
        "not the denomination currency used to buy the fund from your broker."
    )
    
    currency_data = {
        'US Dollar (USD)': current_geo.get('North America', 0.0),
        'Euro & British Pound (EUR/GBP)': current_geo.get('Europe', 0.0),
        'Japanese Yen & Asian (JPY/HKD)': current_geo.get('Asia/Pacific', 0.0),
        'Emerging Market Currencies': current_geo.get('Emerging Markets', 0.0),
    }
    
    allocated_geo = sum(currency_data.values())
    if allocated_geo < 100.0 and allocated_geo > 0:
        currency_data['Other / Fixed Income'] = 100.0 - allocated_geo

    curr_df = pd.DataFrame([
        {"Currency Basket": k, "Your Exposure %": round(v, 2)} 
        for k, v in currency_data.items() if v > 0
    ])
    
    curr_c1, curr_c2 = st.columns([1, 1])
    
    with curr_c1:
        fig_curr = go.Figure(data=[go.Pie(
            labels=curr_df['Currency Basket'], 
            values=curr_df['Your Exposure %'], 
            hole=.4,
            marker=dict(colors=['#636EFA', '#EF553B', '#00CC96', '#AB63FA'])
        )])
        fig_curr.update_layout(title="Portfolio Currency Weights")
        st.plotly_chart(fig_curr, use_container_width=True)
        
    with curr_c2:
        st.markdown("### ⚠️ Currency Risk Analysis")
        usd_risk = currency_data.get('US Dollar (USD)', 0.0)
        
        if usd_risk > 65.0:
            st.warning(f"**High USD Concentration ({round(usd_risk, 1)}%)**: Value is heavily tied to USD performance.")
        else:
            st.success(f"**Diversified Currency Spread**: USD exposure is at {round(usd_risk, 1)}%.")
            
        st.info("**Strategic Search Idea:** Search for funds with 'Eur-Hedged' descriptors to lower FX volatility.")