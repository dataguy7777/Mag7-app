# utils.py

import logging
import pandas as pd
import pytz
from datetime import datetime
import streamlit as st
import io

# Setup logging
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s:%(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

# Fetch stock data with caching
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_stock_data(ticker, start_date, end_date, interval='1d'):
    try:
        # Example using yfinance, replace with actual data fetching logic
        import yfinance as yf
        data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
        return data
    except Exception as e:
        logging.error(f"Error fetching data for {ticker}: {e}")
        return None

# Process data with timezone handling
def process_data_all_times(data, target_timezone='Europe/Berlin'):
    if data is None or data.empty:
        logging.warning("No data to process")
        return pd.DataFrame()
    try:
        tz = pytz.timezone(target_timezone)
    except pytz.UnknownTimeZoneError:
        logging.error(f"Unknown timezone: {target_timezone}")
        return pd.DataFrame()
    try:
        if data.index.tz is None:
            data = data.tz_localize('UTC').tz_convert(tz)
        else:
            data = data.tz_convert(tz)
        return data
    except Exception as e:
        logging.error(f"Error processing timezone for data: {e}")
        return pd.DataFrame()

# Calculate weighted portfolio dynamically
@st.cache_data(ttl=1800, show_spinner=False)
def calculate_weighted_portfolio(mag7_data):
    available_companies = [company for company, data in mag7_data.items() if not data.empty]
    num_companies = len(available_companies)
    if num_companies == 0:
        logging.error("No data available to calculate weighted portfolio.")
        return pd.DataFrame()
    weight = 1 / num_companies
    portfolio = pd.DataFrame()
    for company in available_companies:
        portfolio = portfolio.add(mag7_data[company]['Adj Close'] * weight, fill_value=0)
    portfolio = portfolio.to_frame(name='Weighted Portfolio')
    return portfolio

# Convert DataFrame to Excel
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=True)
    processed_data = output.getvalue()
    return processed_data

# Create combined DataFrame
def create_dataframe(data_dict):
    if not data_dict:
        return pd.DataFrame()
    combined_df = pd.concat(data_dict.values(), axis=1)
    return combined_df