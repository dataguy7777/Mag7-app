import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
import datetime

# Define the companies
mag7 = {
    'Apple': 'AAPL',
    'Microsoft': 'MSFT',
    'Alphabet': 'GOOGL',
    'Amazon': 'AMZN',
    'Meta': 'META',
    'Tesla': 'TSLA',
    'Nvidia': 'NVDA'
}

mag7_etf = 'QQQ'  # Example ETF representing the Mag 7 companies

# Function to fetch data from Yahoo Finance
def fetch_stock_data(ticker, start_date, end_date):
    """
    Fetch historical stock data for the given ticker.
    
    Args:
        ticker (str): Stock ticker symbol (e.g., AAPL for Apple).
        start_date (datetime): Start date for data fetching.
        end_date (datetime): End date for data fetching.
    
    Returns:
        pd.DataFrame: Dataframe containing stock data.
    """
    data = yf.download(ticker, start=start_date, end=end_date, interval='30m')
    return data

# Convert to CEST and filter data for the specified time range
def filter_data_by_time_range(data, start_time, end_time):
    """
    Filter data for a specific time range after converting to CEST timezone.
    
    Args:
        data (pd.DataFrame): The input stock data.
        start_time (datetime.time): Start time (e.g., 17:30).
        end_time (datetime.time): End time (e.g., 22:00).
    
    Returns:
        pd.DataFrame: Filtered dataframe.
    """
    cest = pytz.timezone('Europe/Berlin')
    data.index = data.index.tz_localize('UTC').tz_convert(cest)
    # Filter by the given time range
    data_filtered = data.between_time(start_time.strftime('%H:%M'), end_time.strftime('%H:%M'))
    return data_filtered

# Display the comparison
def compare_mag7_to_etf(mag7_data, etf_data):
    """
    Compare the performance of the Mag 7 companies against the ETF.
    
    Args:
        mag7_data (dict): Dictionary containing stock data of Mag 7 companies.
        etf_data (pd.DataFrame): ETF stock data.
    
    Returns:
        None
    """
    st.subheader('Mag 7 Company Performance vs. ETF')
    st.line_chart(etf_data['Adj Close'], width=0, height=200, use_container_width=True)
    
    for company, data in mag7_data.items():
        st.line_chart(data['Adj Close'], width=0, height=200, use_container_width=True)

# Streamlit app layout
st.title('Mag 7 Stock Data Comparison')
st.sidebar.header('Select Date Range')

# Get user input for the date range
start_date = st.sidebar.date_input('Start Date', datetime.date.today() - datetime.timedelta(days=5))
end_date = st.sidebar.date_input('End Date', datetime.date.today())

# Time range for filtering
start_time = datetime.time(17, 30)
end_time = datetime.time(22, 0)

# Fetch ETF data
st.header(f"Comparing with ETF: {mag7_etf}")
etf_data = fetch_stock_data(mag7_etf, start_date, end_date)
etf_filtered_data = filter_data_by_time_range(etf_data, start_time, end_time)
st.line_chart(etf_filtered_data['Adj Close'])

# Fetch data for Mag 7 companies and filter
st.header("Mag 7 Company Performance")
mag7_data = {}

for company, ticker in mag7.items():
    data = fetch_stock_data(ticker, start_date, end_date)
    filtered_data = filter_data_by_time_range(data, start_time, end_time)
    mag7_data[company] = filtered_data
    
    # Displaying individual company data
    st.subheader(company)
    st.line_chart(filtered_data['Adj Close'])

# Compare all Mag 7 companies to the ETF
compare_mag7_to_etf(mag7_data, etf_filtered_data)