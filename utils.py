# utils.py

import yfinance as yf
import pandas as pd
import pytz
import logging
from io import BytesIO
import streamlit as st

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("app.log"),
            logging.StreamHandler()
        ]
    )

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

def process_data_all_times(data):
    """
    Convert data to CEST timezone without filtering by time range.
    """
    if data is None or data.empty:
        logging.warning("No data to process")
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
    else:
        # If already localized, convert to CEST
        try:
            logging.info("Converting data index to CEST timezone")
            data = data.tz_convert(cest)
        except Exception as e:
            logging.error(f"Error converting timezone for data: {e}")
            return pd.DataFrame()

    logging.info("Data converted to CEST timezone without time filtering")
    return data

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
    processed_data = output.getvalue()
    logging.info("Dataframe exported to Excel successfully")
    return processed_data

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
