import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
import datetime
import plotly.graph_objects as go

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
def fetch_stock_data(ticker, start_date, end_date, interval='30m'):
    """
    Fetch historical stock data for the given ticker.
    
    Args:
        ticker (str): Stock ticker symbol (e.g., AAPL for Apple).
        start_date (datetime): Start date for data fetching.
        end_date (datetime): End date for data fetching.
        interval (str): Time interval for data (default is '30m').
    
    Returns:
        pd.DataFrame: Dataframe containing stock data.
    """
    data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
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

# Create a plot with all Mag 7 companies stacked together
def plot_stacked_companies(mag7_data):
    """
    Plot all Mag 7 companies' stock prices stacked together in one plot using Plotly.
    
    Args:
        mag7_data (dict): Dictionary containing stock data for each Mag 7 company.
    
    Returns:
        Plotly figure: A stacked line chart for the Mag 7 companies.
    """
    fig = go.Figure()
    
    for company, data in mag7_data.items():
        fig.add_trace(go.Scatter(x=data.index, y=data['Adj Close'], mode='lines', name=company))
    
    fig.update_layout(
        title="Mag 7 Companies' Stock Prices (Last 10 Days, Stacked)",
        xaxis_title='Date',
        yaxis_title='Adjusted Close Price',
        hovermode='x unified'
    )
    
    return fig

# Streamlit app layout
st.title('Mag 7 Stock Data Comparison')
st.sidebar.header('Settings')

# Get user input for the date range (last 10 days)
end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=10)

st.sidebar.write(f"Date range: {start_date} to {end_date}")

# Time range for filtering
etf_start_time = datetime.time(9, 0)    # ETF from 09:00 to 17:30 CEST
etf_end_time = datetime.time(17, 30)

company_start_time = datetime.time(15, 30)  # Companies from 15:30 to 22:00 CEST
company_end_time = datetime.time(22, 0)

# Fetch ETF data for Mag 7 ETF (QQQ in this case)
st.header(f"Mag 7 ETF Performance: {mag7_etf}")
etf_data = fetch_stock_data(mag7_etf, start_date, end_date)
etf_filtered_data = filter_data_by_time_range(etf_data, etf_start_time, etf_end_time)

# Plot ETF data
st.subheader(f"{mag7_etf} ETF (9:00 to 17:30 CEST)")
fig_etf = go.Figure()
fig_etf.add_trace(go.Scatter(x=etf_filtered_data.index, y=etf_filtered_data['Adj Close'], mode='lines', name=mag7_etf))
fig_etf.update_layout(
    title=f"{mag7_etf} ETF Adjusted Close (9:00 to 17:30 CEST)",
    xaxis_title='Date',
    yaxis_title='Adjusted Close Price',
    hovermode='x unified'
)
st.plotly_chart(fig_etf)

# Fetch and filter data for Mag 7 companies (from 15:30 to 22:00 CEST)
st.header("Mag 7 Company Performance (15:30 to 22:00 CEST)")
mag7_data = {}

for company, ticker in mag7.items():
    data = fetch_stock_data(ticker, start_date, end_date)
    filtered_data = filter_data_by_time_range(data, company_start_time, company_end_time)
    mag7_data[company] = filtered_data

# Plot all Mag 7 companies together
fig_stacked = plot_stacked_companies(mag7_data)
st.plotly_chart(fig_stacked)