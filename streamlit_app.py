import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
from io import BytesIO

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

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
qqq5_etf = 'qqq5.l'              # Ticker for the QQQ5 Leveraged ETF from Leverage Shares

# Define QQQ ETF
qqq_etf = 'QQQ'                  # Standard QQQ ETF

# List of all tickers to fetch
all_tickers = list(mag7.values()) + [mags_etf, leveraged_5x_etf, qqq3_etf, qqq5_etf, qqq_etf]

# Function to convert DataFrame to Excel
def to_excel(df):
    """Convert a DataFrame to an Excel file in memory."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Make a copy to avoid modifying the original DataFrame
        df_to_export = df.copy()
        
        # Remove timezone information from the index if present
        if isinstance(df_to_export.index, pd.DatetimeIndex) and df_to_export.index.tz is not None:
            logging.info("Removing timezone information from datetime index")
            df_to_export.index = df_to_export.index.tz_convert(None)
        
        df_to_export.to_excel(writer, index=True, sheet_name='Sheet1')
        # Removed writer.save()
    processed_data = output.getvalue()
    logging.info("Dataframe exported to Excel successfully")
    return processed_data

# Caching the fetch_stock_data function to prevent repeated data fetching
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_stock_data(ticker, start_date, end_date, interval='30m'):
    """
    Fetch historical stock data for the given ticker.
    """
    try:
        logging.info(f"Fetching data for ticker: {ticker}")
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
        logging.warning("No data to filter")
        return pd.DataFrame()  # Return empty dataframe if no data is present

    cest = pytz.timezone('Europe/Berlin')

    # Check if the index is already localized
    if data.index.tz is None:
        try:
            logging.info("Localizing data index to UTC and converting to CEST")
            data.index = data.index.tz_localize('UTC').tz_convert(cest)
        except Exception as e:
            logging.error(f"Error localizing timezone for data: {e}")
            return pd.DataFrame()

    # Filter by the given time range
    data_filtered = data.between_time(start_time.strftime('%H:%M'), end_time.strftime('%H:%M'))
    logging.info(f"Filtered data between {start_time} and {end_time}")
    return data_filtered

# Caching the calculate_weighted_portfolio function
@st.cache_data(show_spinner=False)
def calculate_weighted_portfolio(mag7_data):
    """
    Calculate the weighted portfolio where each company has a weight of 1/7.
    """
    logging.info("Calculating weighted portfolio")
    # Assign equal weights (1/7) to each company
    weights = 1 / len(mag7_data)

    portfolio = pd.DataFrame()
    for company, data in mag7_data.items():
        if not data.empty:
            portfolio[company] = data['Adj Close'] * weights
            logging.info(f"Added {company} to weighted portfolio")
        else:
            logging.warning(f"Skipping {company} due to no data.")

    if not portfolio.empty:
        portfolio['Weighted Portfolio'] = portfolio.sum(axis=1)
        logging.info("Calculated Weighted Mag 7 Portfolio")
        return portfolio[['Weighted Portfolio']]
    else:
        logging.error("No data available to calculate weighted portfolio.")
        return pd.DataFrame()

# Plot Mag7 with Leveraged ETFs and Weighted MAGS 5x
def plot_mag7_with_leveraged_etf(mag7_data, weighted_portfolio, mags_filtered_data, leveraged_5x_data, qqq3_data, qqq5_data, weighted_mags_5x):
    """
    Plot all Mag 7 companies' stock prices, along with the Weighted Mag 7 Portfolio, MAGS ETF,
    Leveraged 5x ETF, QQQ3 Leveraged ETF, QQQ5 Leveraged ETF, and Weighted MAGS 5x Portfolio.
    """
    logging.info("Plotting Mag 7 companies with leveraged ETFs and weighted MAGS 5x")
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
            logging.info(f"Plotted {company}")
        else:
            st.warning(f"No data available for {company}, skipping in the plot.")
            logging.warning(f"No data available for {company}")

    # Plot Weighted Portfolio
    if not weighted_portfolio.empty:
        fig.add_trace(go.Scatter(
            x=weighted_portfolio.index,
            y=weighted_portfolio['Weighted Portfolio'],
            mode='lines',
            name='Weighted Mag 7 Portfolio',
            line=dict(dash='dash')
        ))
        logging.info("Plotted Weighted Mag 7 Portfolio")
    else:
        st.warning("Weighted Mag 7 Portfolio could not be calculated due to missing data.")
        logging.warning("Weighted Mag 7 Portfolio missing")

    # Plot Weighted MAGS 5x Portfolio
    if not weighted_mags_5x.empty:
        fig.add_trace(go.Scatter(
            x=weighted_mags_5x.index,
            y=weighted_mags_5x['Weighted MAGS 5x'],
            mode='lines',
            name='Weighted MAGS 5x Portfolio',
            line=dict(dash='dot', color='green')
        ))
        logging.info("Plotted Weighted MAGS 5x Portfolio")
    else:
        st.warning("Weighted MAGS 5x Portfolio could not be plotted due to missing data.")
        logging.warning("Weighted MAGS 5x Portfolio missing")

    # Plot MAGS ETF
    if not mags_filtered_data.empty:
        fig.add_trace(go.Scatter(
            x=mags_filtered_data.index,
            y=mags_filtered_data['Adj Close'],
            mode='lines',
            name='MAGS ETF',
            line=dict(dash='dot')
        ))
        logging.info("Plotted MAGS ETF")
    else:
        st.warning("MAGS ETF data is not available, skipping in the plot.")
        logging.warning("MAGS ETF data missing")

    # Plot Leveraged 5x ETF
    if not leveraged_5x_data.empty:
        fig.add_trace(go.Scatter(
            x=leveraged_5x_data.index,
            y=leveraged_5x_data['Adj Close'],
            mode='lines',
            name='Leveraged 5x Mag 7 ETF',
            line=dict(dash='dashdot')
        ))
        logging.info("Plotted Leveraged 5x Mag 7 ETF")
    else:
        st.warning("Leveraged 5x Mag 7 ETF data is not available, skipping in the plot.")
        logging.warning("Leveraged 5x Mag 7 ETF data missing")

    # Plot QQQ3 Leveraged ETF
    if not qqq3_data.empty:
        fig.add_trace(go.Scatter(
            x=qqq3_data.index,
            y=qqq3_data['Adj Close'],
            mode='lines',
            name='QQQ3 Leveraged ETF',
            line=dict(dash='longdash')
        ))
        logging.info("Plotted QQQ3 Leveraged ETF")
    else:
        st.warning("QQQ3 Leveraged ETF data is not available, skipping in the plot.")
        logging.warning("QQQ3 Leveraged ETF data missing")

    # Plot QQQ5 Leveraged ETF
    if not qqq5_data.empty:
        fig.add_trace(go.Scatter(
            x=qqq5_data.index,
            y=qqq5_data['Adj Close'],
            mode='lines',
            name='QQQ5 Leveraged ETF',
            line=dict(dash='solid', color='black')
        ))
        logging.info("Plotted QQQ5 Leveraged ETF")
    else:
        st.warning("QQQ5 Leveraged ETF data is not available, skipping in the plot.")
        logging.warning("QQQ5 Leveraged ETF data missing")

    # Update layout
    fig.update_layout(
        title="Mag 7 Companies, Weighted Portfolio, Weighted MAGS 5x Portfolio, MAGS ETF, Leveraged 5x ETF, QQQ3 & QQQ5 Leveraged ETFs (08:00 to 23:00 CEST)",
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

    logging.info("Finished plotting Mag 7 and ETFs with Weighted MAGS 5x")
    return fig

# Plot scaled performance and percentage changes
def plot_scaled_performance(tickers_data):
    """
    Plot scaled performance and percentage changes of selected tickers, sharing the same x-axis.
    """
    logging.info("Plotting scaled performance and percentage changes of selected tickers")
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        subplot_titles=("Scaled Performance of Selected Tickers",
                                        "Percentage Changes Every 30 Minutes (Bar Chart)",
                                        "Distribution of Percentage Changes (Histogram)"),
                        vertical_spacing=0.1)

    # 1. Scaled Performance
    for ticker, data in tickers_data.items():
        if not data.empty:
            data = data.sort_index()
            first_valid_index = data['Adj Close'].first_valid_index()
            if first_valid_index is not None:
                first_price = data.loc[first_valid_index, 'Adj Close']
                scaled_prices = (data['Adj Close'] / first_price) * 100
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=scaled_prices,
                    mode='lines',
                    name=ticker
                ), row=1, col=1)
                logging.info(f"Plotted scaled data for {ticker}")
            else:
                st.warning(f"No valid adjusted close prices for {ticker}, skipping in the scaled plot.")
                logging.warning(f"No valid adjusted close prices for {ticker}")
        else:
            st.warning(f"No data available for {ticker}, skipping in the scaled plot.")
            logging.warning(f"No data available for {ticker}")

    # 2. Percentage Changes Every 30 Minutes (Bar Chart)
    for ticker, data in tickers_data.items():
        if not data.empty:
            pct_change = data['Adj Close'].pct_change() * 100
            pct_change = pct_change.dropna()
            fig.add_trace(go.Bar(
                x=pct_change.index,
                y=pct_change.values,
                name=f'{ticker} % Change',
                opacity=0.6
            ), row=2, col=1)
            logging.info(f"Added bar chart for {ticker}")

    # 3. Distribution of Percentage Changes (Histogram)
    for ticker, data in tickers_data.items():
        if not data.empty:
            pct_change = data['Adj Close'].pct_change() * 100
            pct_change = pct_change.dropna()
            fig.add_trace(go.Histogram(
                x=pct_change.values,
                name=f'{ticker} % Change',
                opacity=0.6
            ), row=3, col=1)
            logging.info(f"Added histogram for {ticker}")

    # Update layout
    fig.update_layout(
        height=900,
        title_text="Scaled Performance, Percentage Changes, and Distribution of Selected Tickers",
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
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
        logging.warning("No tickers data provided to create dataframe")
        return pd.DataFrame()

    combined_df = pd.DataFrame()

    for ticker, data in tickers_data.items():
        if not data.empty:
            df = data[['Adj Close']].copy()
            df.rename(columns={'Adj Close': f'{ticker} Value'}, inplace=True)
            df[f'{ticker} % Change'] = df[f'{ticker} Value'].pct_change() * 100
            combined_df = combined_df.join(df, how='outer') if not combined_df.empty else df
            logging.info(f"Added data for {ticker} to dataframe")
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

    logging.info("Created combined dataframe with values and percentage changes")
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

    # Define new unified time range
    data_start_time = datetime.time(8, 0)   # 08:00 CEST
    data_end_time = datetime.time(23, 0)    # 23:00 CEST

    # Fetch MAGS ETF data
    st.header(f"Comparing with MAGS ETF: {mags_etf}")
    mags_data = fetch_stock_data(mags_etf, start_date, end_date)
    mags_filtered_data = filter_data_by_time_range(mags_data, data_start_time, data_end_time)
    logging.info("Fetched and filtered MAGS ETF data")

    # Fetch Leveraged 5x ETF data
    st.header(f"Leveraged 5x ETF: {leveraged_5x_etf}")
    leveraged_5x_data = fetch_stock_data(leveraged_5x_etf, start_date, end_date)
    leveraged_5x_filtered_data = filter_data_by_time_range(leveraged_5x_data, data_start_time, data_end_time)
    logging.info("Fetched and filtered Leveraged 5x ETF data")

    # Fetch QQQ3 Leveraged ETF data
    st.header(f"QQQ3 Leveraged ETF: {qqq3_etf}")
    qqq3_data = fetch_stock_data(qqq3_etf, start_date, end_date)
    qqq3_filtered_data = filter_data_by_time_range(qqq3_data, data_start_time, data_end_time)
    logging.info("Fetched and filtered QQQ3 Leveraged ETF data")

    # Fetch QQQ5 Leveraged ETF data
    st.header(f"QQQ5 Leveraged ETF: {qqq5_etf}")
    qqq5_data = fetch_stock_data(qqq5_etf, start_date, end_date)
    qqq5_filtered_data = filter_data_by_time_range(qqq5_data, data_start_time, data_end_time)
    logging.info("Fetched and filtered QQQ5 Leveraged ETF data")

    # Plot MAGS ETF data
    st.subheader(f"{mags_etf} ETF (08:00 to 23:00 CEST)")
    if mags_data is None or mags_filtered_data.empty:
        st.warning(f"Data for {mags_etf} ETF could not be fetched.")
        logging.warning(f"No data for {mags_etf} ETF")
    else:
        fig_mags = go.Figure()
        fig_mags.add_trace(go.Scatter(
            x=mags_filtered_data.index,
            y=mags_filtered_data['Adj Close'],
            mode='lines',
            name=mags_etf
        ))
        fig_mags.update_layout(
            title=f"{mags_etf} ETF Adjusted Close (08:00 to 23:00 CEST)",
            xaxis_title='Date',
            yaxis_title='Adjusted Close Price',
            hovermode='x unified',
            xaxis_rangeslider_visible=False  # Disables range slider for cleaner view
        )
        st.plotly_chart(fig_mags)
        logging.info("Displayed MAGS ETF plot")

        # Create and display dataframe for MAGS ETF
        st.subheader(f"Dataframe for {mags_etf} ETF")
        df_mags = create_dataframe({mags_etf: mags_filtered_data})
        st.dataframe(df_mags)
        logging.info("Displayed MAGS ETF dataframe")

        # Export to Excel button for MAGS ETF
        if not df_mags.empty:
            excel_mags = to_excel(df_mags)
            st.download_button(
                label="Export MAGS ETF Data to Excel",
                data=excel_mags,
                file_name='MAGS_ETF_Data.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            logging.info("Added Export button for MAGS ETF dataframe")

    # Fetch and filter data for Mag 7 companies (08:00 to 23:00 CEST)
    st.header("Mag 7 Company Performance (08:00 to 23:00 CEST)")
    mag7_data = {}

    for company, ticker in mag7.items():
        logging.info(f"Processing data for {company} ({ticker})")
        data = fetch_stock_data(ticker, start_date, end_date)
        if data is None:
            st.error(f"Failed to fetch data for {company} ({ticker}).")
            logging.error(f"Failed to fetch data for {company} ({ticker})")
            mag7_data[company] = pd.DataFrame()  # Assign empty DataFrame
        else:
            filtered_data = filter_data_by_time_range(data, data_start_time, data_end_time)
            if filtered_data.empty:
                st.warning(f"No data available for {company} ({ticker}) in the specified time range.")
                logging.warning(f"No data for {company} ({ticker}) in specified time range")
            mag7_data[company] = filtered_data
            logging.info(f"Processed data for {company} ({ticker})")

    # Calculate the weighted portfolio for the Mag 7 companies
    weighted_portfolio = calculate_weighted_portfolio(mag7_data)

    # Create Weighted MAGS 5x Portfolio
    if not weighted_portfolio.empty:
        weighted_mags_5x = weighted_portfolio.copy()
        weighted_mags_5x['Weighted MAGS 5x'] = weighted_mags_5x['Weighted Portfolio'] * 5
        logging.info("Created Weighted MAGS 5x Portfolio")
    else:
        weighted_mags_5x = pd.DataFrame()
        logging.warning("Weighted Mag 7 Portfolio missing; cannot create Weighted MAGS 5x")

    # Plot all Mag 7 companies, weighted portfolio, MAGS ETF, Leveraged 5x ETF, QQQ3 Leveraged ETF, and QQQ5 Leveraged ETF
    st.subheader("All Mag 7 Companies, Weighted Portfolio, Weighted MAGS 5x Portfolio, MAGS ETF, Leveraged 5x ETF, QQQ3 & QQQ5 Leveraged ETFs (08:00 to 23:00 CEST)")
    fig_mag7_companies = plot_mag7_with_leveraged_etf(
        mag7_data,
        weighted_portfolio,
        mags_filtered_data,
        leveraged_5x_filtered_data,
        qqq3_filtered_data,
        qqq5_filtered_data,
        weighted_mags_5x
    )
    st.plotly_chart(fig_mag7_companies)
    logging.info("Displayed Mag 7 companies and ETFs plot")

    # Create and display dataframe for all tickers
    combined_tickers = list(mag7.values()) + [mags_etf, leveraged_5x_etf, qqq3_etf, qqq5_etf]
    combined_data = {ticker: data for ticker, data in zip(
        combined_tickers, 
        list(mag7_data.values()) + [mags_filtered_data, leveraged_5x_filtered_data, qqq3_filtered_data, qqq5_filtered_data]
    )}
    df_combined = create_dataframe(combined_data)
    if not df_combined.empty:
        st.subheader("Combined Dataframe of All Tickers")
        st.dataframe(df_combined)
        logging.info("Displayed combined dataframe of all tickers")

        # Export to Excel button for combined dataframe
        excel_combined = to_excel(df_combined)
        st.download_button(
            label="Export Combined Data to Excel",
            data=excel_combined,
            file_name='Combined_Mag7_ETFs_Data.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        logging.info("Added Export button for combined dataframe")
    else:
        st.warning("No combined data available to display.")
        logging.warning("Combined dataframe is empty")

    # Prepare data for scaled performance plot
    st.header("Scaled Performance and Percentage Changes of Selected Tickers")

    # Display the selected date range
    st.write(f"**Date Range:** {start_date} to {end_date}")
    logging.info(f"Displaying scaled performance from {start_date} to {end_date}")

    # Select tickers for the scaled performance graph: MAGS, leveraged ETFs, Weighted Portfolio, Weighted MAGS 5x
    scaled_tickers = {}
    if not mags_filtered_data.empty:
        scaled_tickers[mags_etf] = mags_filtered_data
    if not leveraged_5x_filtered_data.empty:
        scaled_tickers[leveraged_5x_etf] = leveraged_5x_filtered_data
    if not weighted_portfolio.empty:
        # Rename the column to 'Adj Close' for consistency in scaling
        scaled_portfolio = weighted_portfolio.rename(columns={'Weighted Portfolio': 'Adj Close'})
        scaled_tickers['Weighted Mag 7 Portfolio'] = scaled_portfolio
    if not weighted_mags_5x.empty:
        scaled_mags_5x = weighted_mags_5x.rename(columns={'Weighted MAGS 5x': 'Adj Close'})
        scaled_tickers['Weighted MAGS 5x Portfolio'] = scaled_mags_5x

    # Plot scaled performance only if there are tickers to plot
    if scaled_tickers:
        fig_scaled = plot_scaled_performance(scaled_tickers)
        st.plotly_chart(fig_scaled)
        logging.info("Displayed scaled performance and percentage changes plot")

        # Create and display dataframe for scaled performance
        st.subheader("Scaled Dataframe of Selected Tickers")
        df_scaled = create_dataframe(scaled_tickers)
        if not df_scaled.empty:
            st.dataframe(df_scaled)
            logging.info("Displayed scaled dataframe")
            
            # Export to Excel button for scaled dataframe
            excel_scaled = to_excel(df_scaled)
            st.download_button(
                label="Export Scaled Data to Excel",
                data=excel_scaled,
                file_name='Scaled_Selected_Tickers_Data.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            logging.info("Added Export button for scaled dataframe")
        else:
            st.warning("No scaled data available to display.")
            logging.warning("Scaled dataframe is empty")

        # Note: The percentage changes and histograms are already included in the 'plot_scaled_performance' function as subplots
    else:
        st.warning("No tickers available to plot scaled performance.")
        logging.warning("No tickers available for scaled performance")

with tabs[1]:
    st.header("QQQ Comparison")

    # Fetch QQQ ETF data
    st.subheader(f"QQQ ETF: {qqq_etf}")
    qqq_data = fetch_stock_data(qqq_etf, start_date, end_date)
    qqq_filtered_data = filter_data_by_time_range(qqq_data, data_start_time, data_end_time)
    logging.info("Fetched and filtered QQQ ETF data")

    # Fetch qqq3.mi Leveraged ETF data
    st.subheader(f"qqq3.mi Leveraged ETF: {qqq3_etf}")
    qqq3_mi_data = fetch_stock_data(qqq3_etf, start_date, end_date)
    qqq3_mi_filtered_data = filter_data_by_time_range(qqq3_mi_data, data_start_time, data_end_time)
    logging.info("Fetched and filtered qqq3.mi Leveraged ETF data")

    # Fetch qqq5.l Leveraged ETF data
    st.subheader(f"qqq5.l Leveraged ETF: {qqq5_etf}")
    qqq5_l_data = fetch_stock_data(qqq5_etf, start_date, end_date)
    qqq5_l_filtered_data = filter_data_by_time_range(qqq5_l_data, data_start_time, data_end_time)
    logging.info("Fetched and filtered qqq5.l Leveraged ETF data")

    # First Graph: QQQ, qqq3.mi, and qqq5.l Adjusted Close Prices
    st.subheader("Adjusted Close Prices of QQQ, qqq3.mi, and qqq5.l")
    if (qqq_data is None or qqq_filtered_data.empty) and \
       (qqq3_mi_data is None or qqq3_mi_filtered_data.empty) and \
       (qqq5_l_data is None or qqq5_l_filtered_data.empty):
        st.warning("Data for QQQ, qqq3.mi, and qqq5.l could not be fetched.")
        logging.warning("No data fetched for QQQ, qqq3.mi, and qqq5.l")
    else:
        fig_qqq = go.Figure()
        if qqq_data is not None and not qqq_filtered_data.empty:
            fig_qqq.add_trace(go.Scatter(
                x=qqq_filtered_data.index,
                y=qqq_filtered_data['Adj Close'],
                mode='lines',
                name='QQQ ETF'
            ))
            logging.info("Plotted QQQ ETF")
        else:
            st.warning("QQQ ETF data is not available, skipping in the plot.")
            logging.warning("QQQ ETF data missing")

        if qqq3_mi_data is not None and not qqq3_mi_filtered_data.empty:
            fig_qqq.add_trace(go.Scatter(
                x=qqq3_mi_filtered_data.index,
                y=qqq3_mi_filtered_data['Adj Close'],
                mode='lines',
                name='qqq3.mi Leveraged ETF'
            ))
            logging.info("Plotted qqq3.mi Leveraged ETF")
        else:
            st.warning("qqq3.mi Leveraged ETF data is not available, skipping in the plot.")
            logging.warning("qqq3.mi Leveraged ETF data missing")

        if qqq5_l_data is not None and not qqq5_l_filtered_data.empty:
            fig_qqq.add_trace(go.Scatter(
                x=qqq5_l_filtered_data.index,
                y=qqq5_l_filtered_data['Adj Close'],
                mode='lines',
                name='qqq5.l Leveraged ETF',
                line=dict(color='purple')
            ))
            logging.info("Plotted qqq5.l Leveraged ETF")
        else:
            st.warning("qqq5.l Leveraged ETF data is not available, skipping in the plot.")
            logging.warning("qqq5.l Leveraged ETF data missing")

        fig_qqq.update_layout(
            title="Adjusted Close Prices of QQQ, qqq3.mi, and qqq5.l (08:00 to 23:00 CEST)",
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
        logging.info("Displayed QQQ, qqq3.mi, and qqq5.l Adjusted Close Prices plot")

        # Create and display dataframe for QQQ, qqq3.mi, and qqq5.l Adjusted Close Prices
        df_qqq = create_dataframe({
            qqq_etf: qqq_filtered_data,
            qqq3_etf: qqq3_mi_filtered_data,
            qqq5_etf: qqq5_l_filtered_data
        })
        st.subheader("Dataframe for QQQ, qqq3.mi, and qqq5.l Adjusted Close Prices")
        st.dataframe(df_qqq)
        logging.info("Displayed dataframe for QQQ, qqq3.mi, and qqq5.l")

        # Export to Excel button for QQQ, qqq3.mi, and qqq5.l dataframe
        if not df_qqq.empty:
            excel_qqq = to_excel(df_qqq)
            st.download_button(
                label="Export QQQ, qqq3.mi, and qqq5.l Data to Excel",
                data=excel_qqq,
                file_name='QQQ_Leveraged_ETFs_Data.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            logging.info("Added Export button for QQQ, qqq3.mi, and qqq5.l dataframe")
