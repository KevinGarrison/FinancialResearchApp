from dataclasses import dataclass, field
import requests
from datetime import datetime
import pytz
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import os
import uuid
import yfinance as yf

# ETF and Mutual Fund mappings
etf_funds = {
    "Vanguard Total Bond Market ETF": "BND",
    "iShares MSCI EAFE ETF": "EFA",
    "Vanguard FTSE Developed Markets ETF": "VEA",
    "Vanguard FTSE Emerging Markets ETF": "VWO",
    "Vanguard Total International Stock ETF": "VXUS",
    "Vanguard Total World Stock ETF": "VT",
    "Schwab U.S. Broad Market ETF": "SCHB",
    "iShares Core MSCI World ETF": "URTH",
    "Vanguard FTSE All-World ex-US ETF": "VEU",
    "iShares MSCI Emerging Markets ETF": "IEMG",
    "Invesco QQQ Trust": "QQQ",
    "Vanguard S&P 500 ETF": "VOO",
    "SPDR S&P 500 ETF Trust": "SPY",
    "iShares Core S&P 500 ETF": "IVV",
    "Vanguard Total Stock Market ETF": "VTI"
}


@dataclass
class FinDataFetcher:
    all_etf_funds_dict: dict = field(default_factory=lambda: etf_funds)
#-----------------------------------------------------------------------------#
    # --- Financial Clock ---
    def get_time_for_timezones(self):
        """
        Returns a dictionary of current time for major financial timezones.
        """
        timezones = {
            "New York 🇺🇸": "US/Eastern",
            "London 🇬🇧": "Europe/London",
            "Frankfurt 🇩🇪": "Europe/Berlin",
            "Tokyo 🇯🇵": "Asia/Tokyo",
            "Hong Kong 🇭🇰": "Asia/Hong_Kong",
            "Sydney 🇦🇺": "Australia/Sydney"
        }

        now_times = {}

        for city, tz_name in timezones.items():
            tz = pytz.timezone(tz_name)
            now = datetime.now(tz)
            formatted_time = now.strftime("%H:%M:%S")
            formatted_date = now.strftime("%A, %b %d")
            now_times[city] = {
                "time": formatted_time,
                "date": formatted_date
            }

        return now_times
    
#-----------------------------------------------------------------------------#
    def get_api_keys(self):
        keys = {}
        alphavantage_api_key = os.getenv('ALPHAVANTAGE_API_KEY', None)
        keys['ALPHAVANTAGE_API_KEY'] = alphavantage_api_key
        return keys
        
#-----------------------------------------------------------------------------#
    def get_market_data_alpha_advantage(self, api_key, stock='IBM', granularity='Monthly'):
        match granularity:
            case 'Monthly':
                function = 'TIME_SERIES_MONTHLY'
            
        try:
            #url = f'https://www.alphavantage.co/query?function={function}&symbol={stock}&apikey={api_key}'
            #r = requests.get(url)
            #data = r.json()
            data = {
                "2025-03-14": {"4. close": "248.3500"},
                "2025-02-28": {"4. close": "252.4400"},
                "2025-01-31": {"4. close": "255.7000"}
            }
            # # Convert to DataFrame
            #df = pd.DataFrame.from_dict(data['4. close'], orient='index')
            df = pd.DataFrame({
                date: float(values["4. close"])
                for date, values in data.items()
            }, index=["4. close"]).T
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()

            # # Convert all columns to appropriate data types
            for col in df.columns:
                df[col] = pd.to_numeric(df[col])
            return df       
        except Exception as e:
            st.write('Error: ', e)
#-----------------------------------------------------------------------------#
    def plot_time_series(self, data):
        fig = go.Figure()
        fig.add_trace(go.Scatter(
        x=data.index,
        y=data,
        mode='lines+markers',
        name='Close Price'
        ))
        st.plotly_chart(figure_or_data=fig)
#-----------------------------------------------------------------------------#
    # 🎯 Fetch historical price data from yfinance
    def fetch_fund_data_yf(self, fund_name, period="10y", interval="1mo"):
        ticker = self.all_etf_funds_dict.get(fund_name)
        if not ticker:
            raise ValueError(f"Fund '{fund_name}' not found.")
        
        yf_ticker = yf.Ticker(ticker)
        hist = yf_ticker.history(period=period, interval=interval)
        info = yf_ticker.info
        #st.write(info)
        st.write(info.get("longBusinessSummary"))
        st.write()
        st.write('Open:', info.get('open'))
        st.write('Low:', info.get('dayLow'))
        st.write('High:', info.get('dayHigh'))
        st.write('Volume:', info.get('volume'))
        return {
            "ticker": ticker,
            "name": info.get("longName", fund_name),
            "expense_ratio": info.get("expenseRatio"),
            "price_history": hist.get("Close")
        }
            
#-----------------------------------------------------------------------------#
    # --- Page Rendering ---#
    def show_home(self):
        st.markdown("<h1 style='text-align: center;'>🚀 Financial Research Tool</h1>", unsafe_allow_html=True)
        st.markdown("---")

        current_timezones = st.session_state.tool.get_time_for_timezones()
        cols = st.columns(3)

        for idx, (city, info) in enumerate(current_timezones.items()):
            with cols[idx % 3]:
                st.markdown(f"### {city}")
                st.markdown(f"🕓 Time: <span style='color:green;'>{info['time']}</span>", unsafe_allow_html=True)
                st.markdown(f"📅 Date: <span style='color:green;'>{info['date']}</span>", unsafe_allow_html=True)
                st.markdown("---")

        spacer_cols = st.columns([2, 1, 1, 2])
        with spacer_cols[1]:
            if st.button("📈 Shares"):
                st.session_state.page = "shares"
        with spacer_cols[2]:
            if st.button("🪙 Crypto"):
                st.session_state.page = "crypto"


    def show_shares_dashboard(self):
        st.markdown("<h2 style='text-align: center;'>📈 Shares & Funds Dashboard</h2>", unsafe_allow_html=True)
        fund = st.selectbox(label='Choose:', options=list(self.all_etf_funds_dict.keys()))
        #api = self.get_api_keys()
        #data = self.get_market_data_alpha_advantage(api_key=api)
        data = self.fetch_fund_data_yf(fund_name=fund)
        self.plot_time_series(data=data['price_history'])
        if st.button("🏠 Home"):
            st.session_state.page = "home"
    

    def show_crypto_dashboard(self):
        st.markdown("<h2 style='text-align: center;'>🪙 Crypto Dashboard</h2>", unsafe_allow_html=True)


        # --- Home button ---
        if st.button("🏠 Home"):
            st.session_state.page = "home"


        
        

