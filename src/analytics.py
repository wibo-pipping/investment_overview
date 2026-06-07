import pandas as pd
import yfinance as yf
from yahooquery import Ticker as YQ_Ticker

def resolve_isin_to_ticker(identifier):
    """Resolves ISIN codes to active Yahoo exchange tickers dynamically."""
    clean_id = str(identifier).strip()
    if len(clean_id) == 12 and clean_id[:2].isalpha():
        try:
            search_results = yf.Search(clean_id, max_results=5).quotes
            if search_results:
                for result in search_results:
                    if result.get('quoteType') in ['ETF', 'EQUITY', 'MUTUALFUND']:
                        return result.get('symbol')
                return search_results[0].get('symbol')
        except Exception:
            pass
    return clean_id

def fetch_raw_portfolio_data(csv_path="portfolio.csv"):
    return pd.read_csv(csv_path)

def process_portfolio_metrics(df):
    """
    Mathematical and data engine.
    Uses yahooquery to extract reliable, deep structural asset metrics for European ETFs.
    """
    geo_allocations = {}
    sector_allocations = {}
    total_portfolio_value = 0.0
    portfolio_rows = []

    for _, row in df.iterrows():
        raw_identifier = str(row['Ticker']).strip()
        ticker_str = resolve_isin_to_ticker(raw_identifier)
        shares = float(row['Shares'])
        asset_type = str(row['Asset_Type']).strip()

        # 1. Use yahooquery for metadata breakdown maps
        yq = YQ_Ticker(ticker_str)
        
        # 2. Extract asset description name cleanly
        try:
            quote_type = yq.quote_type.get(ticker_str, {})
            asset_name = quote_type.get('longName') or quote_type.get('shortName') or f"Asset Profile ({ticker_str})"
        except Exception:
            asset_name = f"Asset Profile ({ticker_str})"
        
        # 3. Pull live price defensively via yfinance (fast_info is still fastest for current valuations)
        try:
            yf_ticker = yf.Ticker(ticker_str)
            price = yf_ticker.fast_info.get('lastPrice', 1.0)
        except Exception:
            price = 1.0

        position_value = price * shares
        total_portfolio_value += position_value

        geo_data = {}
        sector_data = {}

        # 4. Extract underlying distribution metrics using yahooquery backend modules
        if asset_type.upper() == 'ETF':
            try:
                # Pull deep fund allocation dictionaries
                yq_sectors = yq.fund_sector_weightings
                if isinstance(yq_sectors, pd.DataFrame) and not yq_sectors.empty:
                    # yahooquery outputs a clean index/value DataFrame structure
                    # Transposing it to a flat mapping dictionary: {'technology': 24.5}
                    sector_data = yq_sectors.to_dict().get(ticker_str, {})
                else:
                    sector_data = yq.fund_holding_info.get(ticker_str, {}).get('sectorWeightings', {})
            except Exception:
                sector_data = {}

            try:
                # Pull deep regional asset exposure maps
                holding_info = yq.fund_holding_info.get(ticker_str, {})
                # Look inside the categorical regional dictionary breakdown arrays
                geo_data = holding_info.get('regionalExposure', {}) or holding_info.get('geographicAllocation', {})
            except Exception:
                geo_data = {}

            # Clear out raw lower-case naming configurations and convert fractions to percent values
            sector_data = {str(k).replace('_', ' ').title(): float(v)*100 if float(v) <= 1.0 else float(v) for k, v in sector_data.items() if v is not None}
            geo_data = {str(k).replace('_', ' ').title(): float(v)*100 if float(v) <= 1.0 else float(v) for k, v in geo_data.items() if v is not None}

            # Absolute generic fail-safes only if an ETF completely hides its tracking holdings list
            if not geo_data: 
                geo_data = {'North America': 65.0, 'Europe': 20.0, 'Asia/Pacific': 15.0} 
            if not sector_data: 
                sector_data = {'Technology': 20.0, 'Financial Services': 15.0, 'Healthcare': 15.0}

        elif asset_type.upper() == 'STOCK':
            try:
                profile = yq.asset_profile.get(ticker_str, {})
                sector = profile.get('sector', 'Technology').replace('_', ' ').title()
                country = profile.get('country', 'United States')
            except Exception:
                sector, country = 'Technology', 'United States'
                
            region = 'North America' if country in ['United States', 'Canada'] else 'Europe'
            geo_data = {region: 100.0}
            sector_data = {sector: 100.0}

        # 5. Compile portfolio weights
        for k, v in geo_data.items():
            geo_allocations[k] = geo_allocations.get(k, 0.0) + (v * (position_value / 100))
        
        for k, v in sector_data.items():
            sector_allocations[k] = sector_allocations.get(k, 0.0) + (v * (position_value / 100))

        portfolio_rows.append({
            "Ticker": raw_identifier,
            "Name": asset_name,
            "Type": asset_type,
            "Value": round(position_value, 2)
        })

    if total_portfolio_value == 0:
        return pd.DataFrame(portfolio_rows), {}, {}

    final_geo = {k: (v / total_portfolio_value) * 100 for k, v in geo_allocations.items()}
    final_sector = {k: (v / total_portfolio_value) * 100 for k, v in sector_allocations.items()}
    
    return pd.DataFrame(portfolio_rows), final_geo, final_sector