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
mags_etf = 'MAGS'                # Ticker for the Mag 7 ETF
leveraged_5x_etf = 'MAG7.MI'     # Ticker for the Leveraged 5x Mag 7 ETF from Milan Stock Exchange
qqq3_etf = 'qqq3.mi'             # Ticker for the QQQ3 Leveraged ETF

# Define QQQ ETF
qqq_etf = 'QQQ'                  # Standard QQQ ETF

# List of all tickers to fetch
all_tickers = list(mag7.values()) + [mags_etf, leveraged_5x_etf, qqq3_etf, qqq_etf]

# Caching the fetch_stock_data function to prevent repeated data fetching
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_stock_data(ticker, start_date, end_date, interval='30m'):
    """
    Fetch historical stock data for the given ticker.
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

# Caching the filter_data_by_time_range function
@st.cache_data(show_spinner=False)
def filter_data_by_time_range(data, start_time, end_time):
    """
    Filter data for a specific time range after converting to CEST timezone.
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

# Caching the calculate_weighted_portfolio function
@st.cache_data(show_spinner=False)
def calculate_weighted_portfolio(mag7_data):
    """
    Calculate the weighted portfolio where each company has a weight of 1/7.
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

# Plot selected tickers scaled to 100
def plot_selected_scaled_tickers(tickers_data):
    """
    Plot selected tickers scaled to 100 at the beginning of the time series.
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
        title="Scaled Performance of Selected Tickers (100 at Start)",
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

# Plot percentage changes as bar charts
def plot_percentage_bar_charts(tickers_data):
    """
    Plot bar charts showing % changes for each ticker over time.
    """
    fig = go.Figure()

    for ticker, data in tickers_data.items():
        if not data.empty:
            # Calculate % change
            pct_change = data['Adj Close'].pct_change() * 100
            # Drop the first NaN
            pct_change = pct_change.dropna()
            fig.add_trace(go.Bar(
                x=pct_change.index,
                y=pct_change.values,
                name=f'{ticker} % Change',
                opacity=0.6
            ))

    fig.update_layout(
        title="Percentage Changes Every 30 Minutes",
        xaxis_title='Date',
        yaxis_title='Percentage Change (%)',
        hovermode='x unified',
        barmode='overlay',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5
        ),
        xaxis_rangeslider_visible=False
    )

    return fig

# Plot percentage changes as histograms
def plot_percentage_histograms(tickers_data):
    """
    Plot histograms showing the distribution of % changes for each ticker.
    """
    fig = go.Figure()

    for ticker, data in tickers_data.items():
        if not data.empty:
            # Calculate % change
            pct_change = data['Adj Close'].pct_change() * 100
            # Drop the first NaN
            pct_change = pct_change.dropna()
            fig.add_trace(go.Histogram(
                x=pct_change.values,
                name=f'{ticker} % Change',
                opacity=0.6
            ))

    fig.update_layout(
        title="Distribution of Percentage Changes",
        xaxis_title='Percentage Change (%)',
        yaxis_title='Count',
        hovermode='x unified',
        barmode='overlay',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5
        )
    )

    return fig

# Function to create dataframe with values and percentage changes
def create_dataframe(tickers_data):
    """
    Create a dataframe showing Adjusted Close Prices and % Change for each ticker.
    """
    if not tickers_data:
        return pd.DataFrame()

    combined_df = pd.DataFrame()

    for ticker, data in tickers_data.items():
        if not data.empty:
            df = data[['Adj Close']].copy()
            df.rename(columns={'Adj Close': f'{ticker} Value'}, inplace=True)
            df[f'{ticker} % Change'] = df[f'{ticker} Value'].pct_change() * 100
            combined_df = combined_df.join(df, how='outer') if not combined_df.empty else df
        else:
            logging.warning(f"Skipping {ticker} for dataframe due to missing data.")

    # Drop the first row if it contains NaN due to pct_change
    combined_df.dropna(inplace=True)

    # Format % Change columns
    value_columns = [col for col in combined_df.columns if 'Value' in col]
    pct_columns = [col for col in combined_df.columns if '% Change' in col]

    # Format % Change columns to 2 decimals with %
    for pct_col in pct_columns:
        combined_df[pct_col] = combined_df[pct_col].map("{:.2f}%".format)

    # Reorder columns: all Value columns first, then % Change columns
    combined_df = combined_df[value_columns + pct_columns]

    return combined_df

# Streamlit app layout with tabs
st.title('Mag 7 Stock Data Comparison with MAGS ETF and Leveraged ETFs')

# Create tabs
tabs = st.tabs(["Main", "QQQ"])

with tabs[0]:
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

        # Create and display dataframe for MAGS ETF
        st.subheader(f"Dataframe for {mags_etf} ETF")
        st.dataframe(create_dataframe({mags_etf: mags_filtered_data}))

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

    # Create and display dataframe for Mag 7 Companies, Weighted Portfolio, MAGS ETF, Leveraged 5x ETF, and QQQ3 Leveraged ETF
    combined_tickers = list(mag7.values()) + [mags_etf, leveraged_5x_etf, qqq3_etf]
    combined_data = {ticker: data for ticker, data in zip(
        combined_tickers, 
        list(mag7_data.values()) + [mags_filtered_data, leveraged_5x_filtered_data, qqq3_filtered_data]
    )}
    df_combined = create_dataframe(combined_data)
    if not df_combined.empty:
        st.subheader("Combined Dataframe of All Tickers")
        st.dataframe(df_combined)
    else:
        st.warning("No combined data available to display.")

    # Prepare data for scaled performance plot
    st.header("Scaled Performance of Selected Tickers")

    # Display the selected date range
    st.write(f"**Date Range:** {start_date} to {end_date}")

    # Select tickers for the scaled performance graph: MAGS, MAG7.MI, Weighted Portfolio
    scaled_tickers = {}
    if not mags_filtered_data.empty:
        scaled_tickers[mags_etf] = mags_filtered_data
    if not leveraged_5x_filtered_data.empty:
        scaled_tickers[leveraged_5x_etf] = leveraged_5x_filtered_data
    if not weighted_portfolio.empty:
        # Rename the column to 'Adj Close' for consistency in scaling
        scaled_portfolio = weighted_portfolio.rename(columns={'Weighted Portfolio': 'Adj Close'})
        scaled_tickers['Weighted Mag 7 Portfolio'] = scaled_portfolio
    else:
        st.warning("Weighted Mag 7 Portfolio could not be added to the scaled plot due to missing data.")

    # Plot scaled performance only if there are tickers to plot
    if scaled_tickers:
        fig_scaled = plot_selected_scaled_tickers(scaled_tickers)
        st.plotly_chart(fig_scaled)

        # Create and display dataframe for scaled performance
        st.subheader("Scaled Dataframe of Selected Tickers")
        df_scaled = create_dataframe(scaled_tickers)
        if not df_scaled.empty:
            st.dataframe(df_scaled)
        else:
            st.warning("No scaled data available to display.")

        # Plot Percentage Changes as Bar Charts
        st.subheader("Percentage Changes Every 30 Minutes (Bar Chart)")
        fig_bar = plot_percentage_bar_charts(scaled_tickers)
        st.plotly_chart(fig_bar)

        # Plot Percentage Changes as Histograms
        st.subheader("Distribution of Percentage Changes (Histogram)")
        fig_hist = plot_percentage_histograms(scaled_tickers)
        st.plotly_chart(fig_hist)
    else:
        st.warning("No tickers available to plot scaled performance.")

with tabs[1]:
    st.header("QQQ Comparison")

    # Fetch QQQ ETF data
    st.subheader(f"QQQ ETF: {qqq_etf}")
    qqq_data = fetch_stock_data(qqq_etf, start_date, end_date)
    qqq_filtered_data = filter_data_by_time_range(qqq_data, etf_start_time, etf_end_time)

    # Fetch qqq3.mi Leveraged ETF data
    st.subheader(f"qqq3.mi Leveraged ETF: {qqq3_etf}")
    qqq3_mi_data = fetch_stock_data(qqq3_etf, start_date, end_date)
    qqq3_mi_filtered_data = filter_data_by_time_range(qqq3_mi_data, etf_start_time, etf_end_time)

    # First Graph: QQQ and qqq3.mi Adjusted Close Prices
    st.subheader("Adjusted Close Prices of QQQ and qqq3.mi")
    if (qqq_data is None or qqq_filtered_data.empty) and (qqq3_mi_data is None or qqq3_mi_filtered_data.empty):
        st.warning("Data for both QQQ and qqq3.mi could not be fetched.")
    else:
        fig_qqq = go.Figure()
        if qqq_data is not None and not qqq_filtered_data.empty:
            fig_qqq.add_trace(go.Scatter(
                x=qqq_filtered_data.index,
                y=qqq_filtered_data['Adj Close'],
                mode='lines',
                name='QQQ ETF'
            ))
        else:
            st.warning("QQQ ETF data is not available, skipping in the plot.")

        if qqq3_mi_data is not None and not qqq3_mi_filtered_data.empty:
            fig_qqq.add_trace(go.Scatter(
                x=qqq3_mi_filtered_data.index,
                y=qqq3_mi_filtered_data['Adj Close'],
                mode='lines',
                name='qqq3.mi Leveraged ETF'
            ))
        else:
            st.warning("qqq3.mi Leveraged ETF data is not available, skipping in the plot.")

        fig_qqq.update_layout(
            title="Adjusted Close Prices of QQQ and qqq3.mi",
            xaxis_title='Date',
            yaxis_title='Adjusted Close Price',
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5
            ),
            xaxis_rangeslider_visible=False
        )

        st.plotly_chart(fig_qqq)

        # Create and display dataframe for QQQ and qqq3.mi Adjusted Close Prices
        st.subheader("Dataframe for QQQ and qqq3.mi Adjusted Close Prices")
        st.dataframe(create_dataframe({qqq_etf: qqq_filtered_data, qqq3_etf: qqq3_mi_filtered_data}))

    # Second Graph: QQQ and qqq3.mi Scaled to 100
    st.subheader("Scaled Performance of QQQ and qqq3.mi (100 at Start)")

    # Prepare data for scaled performance plot
    scaled_qqq_tickers = {}

    if qqq_data is not None and not qqq_filtered_data.empty:
        scaled_qqq_tickers[qqq_etf] = qqq_filtered_data
    else:
        logging.warning(f"Skipping {qqq_etf} for scaled plot due to missing data.")

    if qqq3_mi_data is not None and not qqq3_mi_filtered_data.empty:
        scaled_qqq_tickers[qqq3_etf] = qqq3_mi_filtered_data
    else:
        logging.warning(f"Skipping {qqq3_etf} for scaled plot due to missing data.")

    if not scaled_qqq_tickers:
        st.warning("No data available to plot scaled performance for QQQ and qqq3.mi.")
    else:
        fig_scaled_qqq = plot_selected_scaled_tickers(scaled_qqq_tickers)
        st.plotly_chart(fig_scaled_qqq)

        # Create and display dataframe for scaled QQQ and qqq3.mi
        st.subheader("Scaled Dataframe of QQQ and qqq3.mi")
        df_scaled_qqq = create_dataframe(scaled_qqq_tickers)
        if not df_scaled_qqq.empty:
            st.dataframe(df_scaled_qqq)
        else:
            st.warning("No scaled data available to display.")

        # Plot Percentage Changes as Bar Charts
        st.subheader("Percentage Changes Every 30 Minutes (Bar Chart)")
        fig_bar_qqq = plot_percentage_bar_charts(scaled_qqq_tickers)
        st.plotly_chart(fig_bar_qqq)

        # Plot Percentage Changes as Histograms
        st.subheader("Distribution of Percentage Changes (Histogram)")
        fig_hist_qqq = plot_percentage_histograms(scaled_qqq_tickers)
        st.plotly_chart(fig_hist_qqq)