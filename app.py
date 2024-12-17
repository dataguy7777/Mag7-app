# app.py

import streamlit as st
import pandas as pd
import datetime
import logging
import plotly.graph_objects as go  # Added Plotly import

from utils import (
    setup_logging,
    fetch_stock_data,
    process_data_all_times,
    calculate_weighted_portfolio,
    to_excel,
    create_dataframe
)
from components import (
    plot_mag7_with_leveraged_etf,
    plot_scaled_performance
)

# Initialize logging
setup_logging()

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

# Streamlit app layout with tabs
st.title('Mag 7 Stock Data Comparison with MAGS ETF and Leveraged ETFs')

# Create tabs
tabs = st.tabs(["Main", "QQQ"])

# Caching data fetch to avoid redundancy
@st.cache_data(ttl=1800)
def get_data(ticker, start, end):
    return fetch_stock_data(ticker, start, end)

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

    # Fetch ETF data using cached function
    mags_data = get_data(mags_etf, start_date, end_date)
    leveraged_5x_data = get_data(leveraged_5x_etf, start_date, end_date)
    qqq3_data = get_data(qqq3_etf, start_date, end_date)
    qqq5_data = get_data(qqq5_etf, start_date, end_date)
    qqq_data = get_data(qqq_etf, start_date, end_date)

    # Process fetched data
    mags_filtered_data = process_data_all_times(mags_data)
    leveraged_5x_filtered_data = process_data_all_times(leveraged_5x_data)
    qqq3_filtered_data = process_data_all_times(qqq3_data)
    qqq5_filtered_data = process_data_all_times(qqq5_data)

    logging.info("Fetched and processed ETF data")

    # Plot MAGS ETF data
    st.header(f"Comparing with MAGS ETF: {mags_etf}")
    st.subheader(f"{mags_etf} ETF")
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
            title=f"{mags_etf} ETF Adjusted Close",
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

    # Fetch and process data for Mag 7 companies
    st.header("Mag 7 Company Performance")
    mag7_data = {}

    for company, ticker in mag7.items():
        logging.info(f"Processing data for {company} ({ticker})")
        data = get_data(ticker, start_date, end_date)
        if data is None:
            st.error(f"Failed to fetch data for {company} ({ticker}).")
            logging.error(f"Failed to fetch data for {company} ({ticker})")
            mag7_data[company] = pd.DataFrame()  # Assign empty DataFrame
        else:
            filtered_data = process_data_all_times(data)
            if filtered_data.empty:
                st.warning(f"No data available for {company} ({ticker}).")
                logging.warning(f"No data for {company} ({ticker})")
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

    # Plot all Mag 7 companies and ETFs
    st.subheader("All Mag 7 Companies, Weighted Portfolio, Weighted MAGS 5x Portfolio, MAGS ETF, Leveraged 5x ETF, QQQ3 & QQQ5 Leveraged ETFs")
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
    st.header("Scaled Performance of Selected Tickers")

    # Display the selected date range
    st.write(f"**Date Range:** {start_date} to {end_date}")
    logging.info(f"Displaying scaled performance from {start_date} to {end_date}")

    # Select tickers for the scaled performance graph
    scaled_tickers = {}
    if not mags_filtered_data.empty:
        scaled_tickers[mags_etf] = mags_filtered_data
    if not leveraged_5x_filtered_data.empty:
        scaled_tickers[leveraged_5x_etf] = leveraged_5x_filtered_data
    if not weighted_portfolio.empty:
        scaled_portfolio = weighted_portfolio.rename(columns={'Weighted Portfolio': 'Adj Close'})
        scaled_tickers['Weighted Mag 7 Portfolio'] = scaled_portfolio
    if not weighted_mags_5x.empty:
        scaled_mags_5x = weighted_mags_5x.rename(columns={'Weighted MAGS 5x': 'Adj Close'})
        scaled_tickers['Weighted MAGS 5x Portfolio'] = scaled_mags_5x

    # Plot scaled performance
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
    else:
        st.warning("No tickers available to plot scaled performance.")
        logging.warning("No tickers available for scaled performance")

with tabs[1]:
    st.header("QQQ Comparison")

    # Fetch QQQ and Leveraged ETF data using cached function
    qqq_data = get_data(qqq_etf, start_date, end_date)
    qqq3_mi_data = get_data(qqq3_etf, start_date, end_date)
    qqq5_l_data = get_data(qqq5_etf, start_date, end_date)

    # Process fetched data
    qqq_filtered_data = process_data_all_times(qqq_data)
    qqq3_mi_filtered_data = process_data_all_times(qqq3_mi_data)
    qqq5_l_filtered_data = process_data_all_times(qqq5_l_data)

    logging.info("Fetched and processed QQQ and Leveraged ETF data")

    # Create proxies without modifying original DataFrame
    if not qqq_filtered_data.empty:
        qqq_proxy = qqq_filtered_data.copy()
        qqq_proxy['PROXY QQQ3'] = qqq_proxy['Adj Close'] * 3
        qqq_proxy['PROXY QQQ5'] = qqq_proxy['Adj Close'] * 5
        logging.info("Created PROXY QQQ3 and PROXY QQQ5")
    else:
        st.warning("QQQ ETF data is not available to create proxies.")
        logging.warning("QQQ ETF data missing; cannot create proxies")

    # Plot Adjusted Close Prices
    st.subheader("Adjusted Close Prices of QQQ, qqq3.mi, qqq5.l, PROXY QQQ3, and PROXY QQQ5")
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

        # Plot proxies if available
        if not qqq_filtered_data.empty and 'PROXY QQQ3' in qqq_proxy.columns:
            fig_qqq.add_trace(go.Scatter(
                x=qqq_proxy.index,
                y=qqq_proxy['PROXY QQQ3'],
                mode='lines',
                name='PROXY QQQ3 (QQQ * 3)',
                line=dict(dash='dot', color='orange')
            ))
            logging.info("Plotted PROXY QQQ3")
        else:
            st.warning("PROXY QQQ3 data is not available, skipping in the plot.")
            logging.warning("PROXY QQQ3 data missing")

        if not qqq_filtered_data.empty and 'PROXY QQQ5' in qqq_proxy.columns:
            fig_qqq.add_trace(go.Scatter(
                x=qqq_proxy.index,
                y=qqq_proxy['PROXY QQQ5'],
                mode='lines',
                name='PROXY QQQ5 (QQQ * 5)',
                line=dict(dash='dash', color='brown')
            ))
            logging.info("Plotted PROXY QQQ5")
        else:
            st.warning("PROXY QQQ5 data is not available, skipping in the plot.")
            logging.warning("PROXY QQQ5 data missing")

        fig_qqq.update_layout(
            title="Adjusted Close Prices of QQQ, qqq3.mi, qqq5.l, PROXY QQQ3, and PROXY QQQ5",
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
        logging.info("Displayed QQQ, qqq3.mi, qqq5.l, PROXY QQQ3, and PROXY QQQ5 Adjusted Close Prices plot")

        # Create and display dataframe for QQQ and Proxies
        df_qqq = create_dataframe({
            qqq_etf: qqq_filtered_data,
            qqq3_etf: qqq3_mi_filtered_data,
            qqq5_etf: qqq5_l_filtered_data,
            'PROXY QQQ3': qqq_proxy[['PROXY QQQ3']] if not qqq_proxy.empty else pd.DataFrame(),
            'PROXY QQQ5': qqq_proxy[['PROXY QQQ5']] if not qqq_proxy.empty else pd.DataFrame()
        })
        st.subheader("Dataframe for QQQ, qqq3.mi, qqq5.l, PROXY QQQ3, and PROXY QQQ5 Adjusted Close Prices")
        st.dataframe(df_qqq)
        logging.info("Displayed dataframe for QQQ, qqq3.mi, qqq5.l, PROXY QQQ3, and PROXY QQQ5")

        # Export to Excel button for QQQ dataframe
        if not df_qqq.empty:
            excel_qqq = to_excel(df_qqq)
            st.download_button(
                label="Export QQQ, qqq3.mi, qqq5.l, PROXY QQQ3, and PROXY QQQ5 Data to Excel",
                data=excel_qqq,
                file_name='QQQ_Leveraged_ETFs_Proxies_Data.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            logging.info("Added Export button for QQQ, qqq3.mi, qqq5.l, PROXY QQQ3, and PROXY QQQ5 dataframe")

    # Plot Scaled Relative Evolution for QQQ Tab
    st.subheader("Scaled Relative Performance of QQQ and Proxies")

    # Prepare tickers for scaled relative performance
    scaled_qqq_tickers = {}
    if not qqq_filtered_data.empty:
        scaled_qqq_tickers[qqq_etf] = qqq_filtered_data
        if 'PROXY QQQ3' in qqq_proxy.columns:
            scaled_qqq_tickers['PROXY QQQ3'] = qqq_proxy[['PROXY QQQ3']]
        if 'PROXY QQQ5' in qqq_proxy.columns:
            scaled_qqq_tickers['PROXY QQQ5'] = qqq_proxy[['PROXY QQQ5']]
    if not qqq3_mi_filtered_data.empty:
        scaled_qqq_tickers[qqq3_etf] = qqq3_mi_filtered_data
    if not qqq5_l_filtered_data.empty:
        scaled_qqq_tickers[qqq5_etf] = qqq5_l_filtered_data

    # Plot scaled relative performance
    if scaled_qqq_tickers:
        fig_scaled_qqq = go.Figure()
        for ticker, data in scaled_qqq_tickers.items():
            if not data.empty:
                data = data.sort_index()
                first_valid_index = data['Adj Close'].first_valid_index()
                if first_valid_index is not None:
                    first_price = data.loc[first_valid_index, 'Adj Close']
                    scaled_prices = (data['Adj Close'] / first_price) * 100
                    fig_scaled_qqq.add_trace(go.Scatter(
                        x=data.index,
                        y=scaled_prices,
                        mode='lines',
                        name=ticker
                    ))
                    logging.info(f"Plotted scaled data for {ticker}")
                else:
                    st.warning(f"No valid adjusted close prices for {ticker}, skipping in the scaled plot.")
                    logging.warning(f"No valid adjusted close prices for {ticker}")
            else:
                st.warning(f"No data available for {ticker}, skipping in the scaled plot.")
                logging.warning(f"No data available for {ticker}")

        fig_scaled_qqq.update_layout(
            title="Scaled Relative Performance of QQQ and Proxies",
            xaxis_title='Date',
            yaxis_title='Scaled Adjusted Close Price (Start = 100)',
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

        st.plotly_chart(fig_scaled_qqq)
        logging.info("Displayed Scaled Relative Performance of QQQ and Proxies plot")

        # Create and display dataframe for scaled relative performance
        df_scaled_qqq = create_dataframe(scaled_qqq_tickers)
        st.subheader("Scaled Dataframe for QQQ and Proxies")
        st.dataframe(df_scaled_qqq)
        logging.info("Displayed scaled dataframe for QQQ and proxies")

        # Export to Excel button for scaled relative performance dataframe
        if not df_scaled_qqq.empty:
            excel_scaled_qqq = to_excel(df_scaled_qqq)
            st.download_button(
                label="Export Scaled QQQ and Proxies Data to Excel",
                data=excel_scaled_qqq,
                file_name='Scaled_QQQ_Proxies_Data.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            logging.info("Added Export button for scaled QQQ and proxies dataframe")
    else:
        st.warning("No tickers available to plot scaled relative performance.")
        logging.warning("No tickers available for scaled relative performance")