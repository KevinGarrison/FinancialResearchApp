from dataclasses import dataclass, field
import requests
from datetime import datetime
import pytz
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import os
import uuid
import re
from bs4 import BeautifulSoup
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
    "Vanguard Total Stock Market ETF": "VTI",
    "SPDR Dow Jones Industrial Average ETF Trust": "DIA"
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
    # 🎯 Fetch company data from U.S. Securities and Exchange Commission
    def fetch_company_data_sec(self):
        USER_AGENT_SEC = os.getenv('USER_AGENT_SEC')
        headers = {'User-Agent': USER_AGENT_SEC}
        company_tickers = requests.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers=headers
        )
        company_data = pd.DataFrame(company_tickers.json()).T
        return company_data
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
    def parse_sec_filing(self, text):
        """
        Parses an SEC .txt filing and returns a list of documents with type, filename, raw HTML, and cleaned text.
        """
        documents = re.findall(r"<DOCUMENT>(.*?)</DOCUMENT>", text, flags=re.DOTALL)
        parsed_docs = []

        for doc in documents:
            doc_type = re.search(r"<TYPE>(.*?)\s", doc)
            filename = re.search(r"<FILENAME>(.*?)\s", doc)
            html_match = re.search(r"<TEXT>(.*)", doc, flags=re.DOTALL)

            parsed_docs.append({
                "type": doc_type.group(1) if doc_type else None,
                "filename": filename.group(1) if filename else None,
                "raw_html": html_match.group(1) if html_match else None,
                "clean_text": BeautifulSoup(html_match.group(1), "html.parser").get_text(separator="\n") if html_match else ""
            })

        return parsed_docs
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

        spacer_cols = st.columns([1.5, 1, 1, 1, 1.5])
        with spacer_cols[1]:
            if st.button("📈 Shares"):
                st.session_state.page = "shares"
        with spacer_cols[2]:
            if st.button("🪙 Crypto"):
                st.session_state.page = "crypto"
        with spacer_cols[3]:
            if st.button("🏢 Company"):
                st.session_state.page = "details"


    def show_shares_dashboard(self):
        st.markdown("<h2 style='text-align: center;'>📈 Shares & Funds Dashboard</h2>", unsafe_allow_html=True)
        fund = st.selectbox(label='Choose:', options=list(self.all_etf_funds_dict.keys()))
        #api = self.get_api_keys()
        #data = self.get_market_data_alpha_advantage(api_key=api)
        data = self.fetch_fund_data_yf(fund_name=fund)
        self.plot_time_series(data=data['price_history'])
        # --- Home button ---
        if st.button("🏠 Home"):
            st.session_state.page = "home"
    

    def show_crypto_dashboard(self):
        st.markdown("<h2 style='text-align: center;'>🪙 Crypto Dashboard</h2>", unsafe_allow_html=True)


        # --- Home button ---
        if st.button("🏠 Home"):
            st.session_state.page = "home"


    def show_company_details_dashboard(self):
        st.markdown("<h2 style='text-align: center;'>🏢 Company Details Dashboard</h2>", unsafe_allow_html=True)
        USER_AGENT_SEC = os.getenv('USER_AGENT_SEC')
        headers = {'User-Agent': USER_AGENT_SEC}
        company_data = self.fetch_company_data_sec()
        company_data['cik_str'] = company_data['cik_str'].astype(str).apply(lambda x: x.zfill(10))
        options = company_data['title'].tolist()
        selected_company = st.selectbox("Choose a company", options)
        st.markdown("<p style='text-align: center; font-style: italic;'>(hover over the keys for a brief description)</p>", unsafe_allow_html=True)
        cik = company_data.loc[company_data['title'] == selected_company, 'cik_str'].values[0]
        filingMetaData = requests.get(
            f'https://data.sec.gov/submissions/CIK{cik}.json',
            headers=headers
        )
        filing_dict = filingMetaData.json()

        important_keys = [
            "name", "tickers", "exchanges", "sicDescription",
            "description", "website", "fiscalYearEnd"
        ]

        secondary_keys = [
            "stateOfIncorporation", "stateOfIncorporationDescription",
            "insiderTransactionForOwnerExists", "insiderTransactionForIssuerExists",
            "category", "addresses"
        ]
        

        # Filter dictionaries
        first_meta_data_dict = {k: (v if v else "N/A") for k, v in filing_dict.items() if k in important_keys}
        secondary_meta_data_dict = {k: (v if v else "N/A") for k, v in filing_dict.items() if k in secondary_keys}
        recent_filings = pd.DataFrame(filing_dict['filings']['recent'])
        cols = ['accessionNumber', 'reportDate', 'form', 'cik']
        
        important_forms = ['10-K', '10-Q', '8-K', 'S-1', 'S-3', 'DEF 14A', '20-F', '6-K', '4', '13D', '13G']

        for form_type in important_forms:
            filtered = recent_filings[recent_filings['core_type'] == form_type]
            if not filtered.empty:
                filtered = filtered.copy()
                filtered['cik'] = cik
                session_key = f'{form_type}'
                st.session_state[session_key] = filtered[cols].reset_index(drop=True).head(1)
        #st.write(filtered)
        
        # Explanatory tooltips for each field
        field_tooltips = {
            "sicDescription": "Standard Industrial Classification – describes the company's industry.",
            "name": "The official legal name of the company.",
            "tickers": "Ticker symbols used to identify the company's publicly traded stock.",
            "exchanges": "Stock exchanges where the company's shares are listed.",
            "description": "A brief summary of the company's business operations.",
            "website": "Official company website.",
            "fiscalYearEnd": "The end date of the company's fiscal year. Format: MMDD.",
            "insiderTransactionForOwnerExists": (
                "Shows whether insiders (like executives or directors) have bought/sold stock recently. "
                "Example: A CFO buying 5,000 shares."
            ),
            "insiderTransactionForIssuerExists": (
                "Indicates if the company itself has traded its own shares. "
                "Example: A stock buyback program."
            ),
            "ein": "Employer Identification Number – a federal tax ID used by the IRS.",
            "category": (
                "Filing status under SEC rules. 'Large Accelerated Filer' means $700M+ public float "
                "and stricter reporting timelines."
            ),
            "stateOfIncorporation": "U.S. state (or country) where the company is legally registered.",
            "stateOfIncorporationDescription": "Full name or abbreviation of the state/country of incorporation.",
            "addresses": "Mailing and business addresses associated with the company."
        }


        st.subheader("📌 Primary Company Information")
        for key, value in first_meta_data_dict.items():
            if isinstance(value, list):
                value = ", ".join(value)
            tooltip = field_tooltips.get(key, "")
            label = f'<abbr title="{tooltip}"><strong>{key}:</strong></abbr>' if tooltip else f"<strong>{key}:</strong>"
            st.markdown(f"{label} {value}", unsafe_allow_html=True)


        st.subheader("ℹ️ Secondary Company Information")
        for key, value in secondary_meta_data_dict.items():
            if isinstance(value, list):
                value = ", ".join(value)
            # Special formatting for nested address dict
            if key == "addresses" and isinstance(value, dict):
                for addr_type, addr in value.items():
                    street = addr.get("street1", "")
                    city = addr.get("city", "")
                    state = addr.get("stateOrCountry", "")
                    zip_code = addr.get("zipCode", "")
                    st.markdown(f"**📍 {addr_type.capitalize()} Address:** {street}, {city}, {state} {zip_code}")
            else:
                tooltip = field_tooltips.get(key, "")
                label = f'<abbr title="{tooltip}"><strong>{key}:</strong></abbr>' if tooltip else f"<strong>{key}:</strong>"
                st.markdown(f"{label} {value}", unsafe_allow_html=True)

        spacer_cols = st.columns([2, 1, 1, 2])
        with spacer_cols[1]:
            if st.button("🏠 Home"):
                st.session_state.page = "home"
        with spacer_cols[2]:
            if st.button("📄 Filings"):
                st.session_state.page = "filings"   
                
                 
    def show_company_filings_dashboard(self):
        st.markdown("<h2 style='text-align: center;'>📄 Company Filings Dashboard</h2>", unsafe_allow_html=True)
        USER_AGENT_SEC = os.getenv('USER_AGENT_SEC')
        headers = {'User-Agent': USER_AGENT_SEC}
        important_forms = ['10-K', '10-Q', '8-K', 'S-1', 'S-3', 'DEF 14A', '20-F', '6-K', '4', '13D', '13G']
        filing_type = st.selectbox(label='Choose:', options=important_forms)
        cik = st.session_state[filing_type]['cik'][0]
        accession = st.session_state[filing_type]['accessionNumber'][0].replace("-", "")
        st.write(cik)
        st.write(accession)
        url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/index.json"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            st.write('https://www.sec.gov' + data['directory']['name'] + '/' + data['directory']['item'][2]['name'])
        base_url = 'https://www.sec.gov' + data['directory']['name'] + '/' + data['directory']['item'][2]['name']
        response_2 = requests.get(base_url, headers=headers)
        if response_2.status_code == 200:
            text = response_2.text
            docs = self.parse_sec_filing(text)
            filing = docs[0]['clean_text']
            st.write(len(docs))
            st.write(filing)