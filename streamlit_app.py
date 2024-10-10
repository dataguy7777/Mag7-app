import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
import datetime
import plotly.graph_objects as go
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the Mag 7 companies
mag7 = {
    'Apple': 'AAPL',
    'Microsoft': 'MSFT',
    'Alphabet': 'GOOGL',
    'Amazon': 'AMZN',
    'Meta': 'META',
    'Tesla': 'TSLA',
    'Nvidia': 'NVDA'
}

# Define ETFs
mags_etf = 'MAGS'  # Ticker for the Mag 7 ETF
leveraged_5x_etf = 'MAG7.MI'  # Ticker for the leveraged 5x Mag 7 ETF from Milan Stock Exchange
qqq3_etf = 'QQQ3'  # Ticker for the QQQ3 Leveraged ETF

# List of all tickers to fetch
all_tickers = list(mag7.values()) + [mags_etf, leveraged_5x_etf, qqq3_etf]

# Function to fetch data from Yahoo Finance
def fetch_stock_data(ticker, start_date, end_date, interval='30m'):
    """
    Fetch historical stock data for the given ticker.

    Args:
        ticker (str): Stock ticker symbol (e.g., AAPL for Apple).
        start_date (datetime.date): Start date for data fetching.
        end_date (datetime.date): End date for data fetching.
        interval (str): Time interval for data (default is '30m').

    Returns:
        pd.DataFrame or None: Dataframe containing stock data, or None if fetch fails.
    """
    try:
        data = yf.download(ticker, start=start_date, end=end_date, interval=interval, progress=False)
        if data.empty:
            logging.error(f"No data fetched for ticker: {ticker}")
            return None
        logging.info(f"Successfully fetched data for ticker: {ticker}")
        return data
    except Exception as e:
        logging.error(f"Error fetching data for {ticker}: {e}")
        return None

# Convert to CEST and filter data for the specified time range
def filter_data_by_time_range(data, start_time, end_time):
    """
    Filter data for a specific time range after converting to CEST timezone.

    Args:
        data (pd.DataFrame): The input stock data.
        start_time (datetime.time): Start time (e.g., 09:00).
        end_time (datetime.time): End time (e.g., 17:30).

    Returns:
        pd.DataFrame: Filtered dataframe, or empty dataframe if input is None or empty.
    """
    if data is None or data.empty:
        return pd.DataFrame()  # Return empty dataframe if no data is present

    cest = pytz.timezone('Europe/Berlin')

    # Check if the index is already localized
    if data.index.tz is None:
        try:
            data.index = data.index.tz_localize('UTC').tz_convert(cest)
        except Exception as e:
            logging.error(f"Error localizing timezone for data: {e}")
            return pd.DataFrame()

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
        if not data.empty:
            portfolio[company] = data['Adj Close'] * weights
        else:
            logging.warning(f"Skipping {company} due to no data.")

    if not portfolio.empty:
        portfolio['Weighted Portfolio'] = portfolio.sum(axis=1)
        return portfolio[['Weighted Portfolio']]
    else:
        logging.error("No data available to calculate weighted portfolio.")
        return pd.DataFrame()

# Plot all Mag 7 companies and include MAGS ETF, Weighted Portfolio, Leveraged ETF, and QQQ3
def plot_mag7_with_leveraged_etf(mag7_data, weighted_portfolio, mags_filtered_data, leveraged_5x_data, qqq3_data):
    """
    Plot all Mag 7 companies' stock prices, along with the Weighted Mag 7 Portfolio, MAGS ETF, Leveraged 5x ETF, and QQQ3 Leveraged ETF.

    Args:
        mag7_data (dict): Dictionary containing stock data for each Mag 7 company.
        weighted_portfolio (pd.DataFrame): DataFrame of the weighted portfolio.
        mags_filtered_data (pd.DataFrame): DataFrame of MAGS ETF data.
        leveraged_5x_data (pd.DataFrame): DataFrame of Leveraged 5x ETF data.
        qqq3_data (pd.DataFrame): DataFrame of QQQ3 Leveraged ETF data.

    Returns:
        Plotly figure: A line chart with all Mag 7 companies, the weighted portfolio, MAGS ETF, Leveraged 5x ETF, and QQQ3 Leveraged ETF.
    """
    fig = go.Figure()

    # Plot Mag 7 companies
    for company, data in mag7_data.items():
        if not data.empty:
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data['Adj Close'],
                mode='lines',
                name=company
            ))
        else:
            st.warning(f"No data available for {company}, skipping in the plot.")

    # Plot Weighted Portfolio
    if not weighted_portfolio.empty:
        fig.add_trace(go.Scatter(
            x=weighted_portfolio.index,
            y=weighted_portfolio['Weighted Portfolio'],
            mode='lines',
            name='Weighted Mag 7 Portfolio',
            line=dict(dash='dash')
        ))
    else:
        st.warning("Weighted Mag 7 Portfolio could not be calculated due to missing data.")

    # Plot MAGS ETF
    if not mags_filtered_data.empty:
        fig.add_trace(go.Scatter(
            x=mags_filtered_data.index,
            y=mags_filtered_data['Adj Close'],
            mode='lines',
            name='MAGS ETF',
            line=dict(dash='dot')
        ))
    else:
        st.warning("MAGS ETF data is not available, skipping in the plot.")

    # Plot Leveraged 5x ETF
    if not leveraged_5x_data.empty:
        fig.add_trace(go.Scatter(
            x=leveraged_5x_data.index,
            y=leveraged_5x_data['Adj Close'],
            mode='lines',
            name='Leveraged 5x Mag 7 ETF',
            line=dict(dash='dashdot')
        ))
    else:
        st.warning("Leveraged 5x Mag 7 ETF data is not available, skipping in the plot.")

    # Plot QQQ3 Leveraged ETF
    if not qqq3_data.empty:
        fig.add_trace(go.Scatter(
            x=qqq3_data.index,
            y=qqq3_data['Adj Close'],
            mode='lines',
            name='QQQ3 Leveraged ETF',
            line=dict(dash='longdash')
        ))
    else:
        st.warning("QQQ3 Leveraged ETF data is not available, skipping in the plot.")

    # Update layout
    fig.update_layout(
        title="Mag 7 Companies, Weighted Portfolio, MAGS ETF, Leveraged 5x ETF, and QQQ3 Leveraged ETF (15:30 to 22:00 CEST)",
        xaxis_title='Date',
        yaxis_title='Adjusted Close Price',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5
        ),  # Legend below the graph
        xaxis_rangeslider_visible=False  # Disables range slider for cleaner view
    )

    return fig

# Plot all tickers scaled to 100
def plot_scaled_tickers(tickers_data):
    """
    Plot all tickers scaled to 100 at the beginning of the time series.

    Args:
        tickers_data (dict): Dictionary containing stock data for each ticker.

    Returns:
        Plotly figure: A line chart with all tickers scaled to 100.
    """
    fig = go.Figure()

    for ticker, data in tickers_data.items():
        if not data.empty:
            # Ensure data is sorted by date
            data = data.sort_index()
            # Find the first non-NaN value for scaling
            first_valid_index = data['Adj Close'].first_valid_index()
            if first_valid_index is not None:
                first_price = data.loc[first_valid_index, 'Adj Close']
                scaled_prices = (data['Adj Close'] / first_price) * 100
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=scaled_prices,
                    mode='lines',
                    name=ticker
                ))
            else:
                st.warning(f"No valid adjusted close prices for {ticker}, skipping in the scaled plot.")
        else:
            st.warning(f"No data available for {ticker}, skipping in the scaled plot.")

    # Update layout
    fig.update_layout(
        title="Scaled Performance of All Tickers (100 at Start)",
        xaxis_title='Date',
        yaxis_title='Scaled Adjusted Close Price',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5
        ),  # Legend below the graph
        xaxis_rangeslider_visible=False  # Disables range slider for cleaner view
    )

    return fig

# Streamlit app layout
st.title('Mag 7 Stock Data Comparison with MAGS ETF and Leveraged ETFs')
st.sidebar.header('Settings')

# Get user input for the date range
default_end_date = datetime.date.today()
default_start_date = default_end_date - datetime.timedelta(days=30)  # Default to last 30 days

start_date = st.sidebar.date_input('Start Date', default_start_date)
end_date = default_end_date  # End date is always today

if start_date > end_date:
    st.sidebar.error("Start date must be before or equal to end date.")

st.sidebar.write(f"Date range: {start_date} to {end_date}")

# Time ranges for filtering
etf_start_time = datetime.time(9, 0)        # ETFs from 09:00 to 17:30 CEST
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

# Fetch QQQ3 Leveraged ETF data
st.header(f"QQQ3 Leveraged ETF: {qqq3_etf}")
qqq3_data = fetch_stock_data(qqq3_etf, start_date, end_date)
qqq3_filtered_data = filter_data_by_time_range(qqq3_data, etf_start_time, etf_end_time)

# Plot MAGS ETF data
st.subheader(f"{mags_etf} ETF (9:00 to 17:30 CEST)")
if mags_data is None or mags_filtered_data.empty:
    st.warning(f"Data for {mags_etf} ETF could not be fetched.")
else:
    fig_mags = go.Figure()
    fig_mags.add_trace(go.Scatter(
        x=mags_filtered_data.index,
        y=mags_filtered_data['Adj Close'],
        mode='lines',
        name=mags_etf
    ))
    fig_mags.update_layout(
        title=f"{mags_etf} ETF Adjusted Close (9:00 to 17:30 CEST)",
        xaxis_title='Date',
        yaxis_title='Adjusted Close Price',
        hovermode='x unified',
        xaxis_rangeslider_visible=False  # Disables range slider for cleaner view
    )
    st.plotly_chart(fig_mags)

# Fetch and filter data for Mag 7 companies (from 15:30 to 22:00 CEST)
st.header("Mag 7 Company Performance (15:30 to 22:00 CEST)")
mag7_data = {}

for company, ticker in mag7.items():
    data = fetch_stock_data(ticker, start_date, end_date)
    if data is None:
        st.error(f"Failed to fetch data for {company} ({ticker}).")
        mag7_data[company] = pd.DataFrame()  # Assign empty DataFrame
    else:
        filtered_data = filter_data_by_time_range(data, company_start_time, company_end_time)
        if filtered_data.empty:
            st.warning(f"No data available for {company} ({ticker}) in the specified time range.")
        mag7_data[company] = filtered_data

# Calculate the weighted portfolio for the Mag 7 companies
weighted_portfolio = calculate_weighted_portfolio(mag7_data)

# Plot all Mag 7 companies, weighted portfolio, MAGS ETF, Leveraged 5x ETF, and QQQ3 Leveraged ETF
st.subheader("All Mag 7 Companies, Weighted Portfolio, MAGS ETF, Leveraged 5x ETF, and QQQ3 Leveraged ETF (15:30 to 22:00 CEST)")
fig_mag7_companies = plot_mag7_with_leveraged_etf(
    mag7_data,
    weighted_portfolio,
    mags_filtered_data,
    leveraged_5x_filtered_data,
    qqq3_filtered_data
)

st.plotly_chart(fig_mag7_companies)

# Prepare data for scaled performance plot
st.header("Scaled Performance of All Tickers")
scaled_tickers = {}

# Include all tickers: Mag 7 companies, MAGS, Leveraged 5x ETF, QQQ3
for company, ticker in mag7.items():
    if not mag7_data[company].empty:
        scaled_tickers[ticker] = mag7_data[company]
    else:
        logging.warning(f"Skipping {company} ({ticker}) for scaled plot due to missing data.")

# Add ETFs
if not mags_filtered_data.empty:
    scaled_tickers[mags_etf] = mags_filtered_data
if not leveraged_5x_filtered_data.empty:
    scaled_tickers[leveraged_5x_etf] = leveraged_5x_filtered_data
if not qqq3_filtered_data.empty:
    scaled_tickers[qqq3_etf] = qqq3_filtered_data

# Add Weighted Portfolio scaled to 100
if not weighted_portfolio.empty:
    # Rename the column to 'Adj Close' for consistency in scaling
    scaled_portfolio = weighted_portfolio.rename(columns={'Weighted Portfolio': 'Adj Close'})
    scaled_tickers['Weighted Mag 7 Portfolio'] = scaled_portfolio
else:
    st.warning("Weighted Mag 7 Portfolio could not be added to the scaled plot due to missing data.")

# Plot scaled performance
fig_scaled = plot_scaled_tickers(scaled_tickers)
st.plotly_chart(fig_scaled)