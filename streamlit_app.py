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

mags_etf = 'MAGS'  # Ticker for the Mag 7 ETF
leveraged_5x_etf = 'XS2779861249'  # Ticker for the leveraged 5x Mag 7 ETF

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
    # Check if data is not empty
    if data.empty:
        return pd.DataFrame()  # Return empty dataframe if no data is present
    
    cest = pytz.timezone('Europe/Berlin')
    
    # Check if the index is already localized
    if data.index.tz is None:
        data.index = data.index.tz_localize('UTC').tz_convert(cest)
    
    # Filter by the given time range
    data_filtered = data.between_time(start_time.strftime('%H:%M'), end_time.strftime('%H:%M'))
    return data_filtered

# Create a weighted portfolio of Mag 7 companies
def calculate_weighted_portfolio(mag7_data):
    """
    Calculate the weighted portfolio where each company has a weight of 1/7.
    
    Args:
        mag7_data (dict): Dictionary containing stock data for each Mag 7 company.
    
    Returns:
        pd.DataFrame: Weighted portfolio of Mag 7 companies.
    """
    # Assign equal weights (1/7) to each company
    weights = 1 / len(mag7_data)
    
    portfolio = pd.DataFrame()
    for company, data in mag7_data.items():
        portfolio[company] = data['Adj Close'] * weights
    
    portfolio['Weighted Portfolio'] = portfolio.sum(axis=1)
    return portfolio[['Weighted Portfolio']]

# Plot all Mag 7 companies and include MAGS ETF, Weighted Portfolio, and Leveraged ETF
def plot_mag7_with_leveraged_etf(mag7_data, weighted_portfolio, mags_filtered_data, leveraged_5x_data):
    """
    Plot all Mag 7 companies' stock prices, along with the Weighted Mag 7 Portfolio, MAGS ETF, and the Leveraged 5x ETF.
    
    Args:
        mag7_data (dict): Dictionary containing stock data for each Mag 7 company.
        weighted_portfolio (pd.DataFrame): DataFrame of the weighted portfolio.
        mags_filtered_data (pd.DataFrame): DataFrame of MAGS ETF data.
        leveraged_5x_data (pd.DataFrame): DataFrame of Leveraged 5x ETF data.
    
    Returns:
        Plotly figure: A line chart with all Mag 7 companies, the weighted portfolio, MAGS ETF, and Leveraged 5x ETF.
    """
    fig = go.Figure()
    
    # Plot Mag 7 companies
    for company, data in mag7_data.items():
        fig.add_trace(go.Scatter(x=data.index, y=data['Adj Close'], mode='lines', name=company))
    
    # Plot Weighted Portfolio
    fig.add_trace(go.Scatter(x=weighted_portfolio.index, y=weighted_portfolio['Weighted Portfolio'], mode='lines', name='Weighted Mag 7 Portfolio', line=dict(dash='dash')))
    
    # Plot MAGS ETF
    fig.add_trace(go.Scatter(x=mags_filtered_data.index, y=mags_filtered_data['Adj Close'], mode='lines', name='MAGS ETF', line=dict(dash='dot')))
    
    # Plot Leveraged 5x ETF
    fig.add_trace(go.Scatter(x=leveraged_5x_data.index, y=leveraged_5x_data['Adj Close'], mode='lines', name='Leveraged 5x Mag 7 ETF', line=dict(dash='dashdot')))
    
    # Update layout
    fig.update_layout(
        title="Mag 7 Companies, Weighted Portfolio, MAGS ETF, and Leveraged 5x ETF (15:30 to 22:00 CEST)",
        xaxis_title='Date',
        yaxis_title='Adjusted Close Price',
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),  # Legend below the graph
        xaxis_rangeslider_visible=False  # Disables range slider for cleaner view
    )
    
    return fig

# Streamlit app layout
st.title('Mag 7 Stock Data Comparison with MAGS ETF and Leveraged 5x ETF')
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

# Fetch MAGS ETF data
st.header(f"Comparing with MAGS ETF: {mags_etf}")
mags_data = fetch_stock_data(mags_etf, start_date, end_date)
mags_filtered_data = filter_data_by_time_range(mags_data, etf_start_time, etf_end_time)

# Fetch Leveraged 5x ETF data
st.header(f"Leveraged 5x ETF: {leveraged_5x_etf}")
leveraged_5x_data = fetch_stock_data(leveraged_5x_etf, start_date, end_date)
leveraged_5x_filtered_data = filter_data_by_time_range(leveraged_5x_data, etf_start_time, etf_end_time)

# Plot MAGS ETF data
st.subheader(f"{mags_etf} ETF (9:00 to 17:30 CEST)")
fig_mags = go.Figure()
fig_mags.add_trace(go.Scatter(x=mags_filtered_data.index, y=mags_filtered_data['Adj Close'], mode='lines', name=mags_etf))
fig_mags.update_layout(
    title=f"{mags_etf} ETF Adjusted Close (9:00 to 17:30 CEST)",