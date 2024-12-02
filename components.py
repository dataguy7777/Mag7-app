# components.py

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
import streamlit as st

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
        title="Mag 7 Companies, Weighted Portfolio, Weighted MAGS 5x Portfolio, MAGS ETF, Leveraged 5x ETF, QQQ3 & QQQ5 Leveraged ETFs",
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

def plot_scaled_performance(tickers_data):
    """
    Plot scaled performance and percentage changes of selected tickers, sharing the same x-axis.
    """
    logging.info("Plotting scaled performance and percentage changes of selected tickers")
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        subplot_titles=("Scaled Relative Performance of Selected Tickers",
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

    # 2. Distribution of Percentage Changes (Histogram)
    for ticker, data in tickers_data.items():
        if not data.empty:
            pct_change = data['Adj Close'].pct_change() * 100
            pct_change = pct_change.dropna()
            fig.add_trace(go.Histogram(
                x=pct_change.values,
                name=f'{ticker} % Change',
                opacity=0.6
            ), row=2, col=1)
            logging.info(f"Added histogram for {ticker}")

    # Update layout
    fig.update_layout(
        height=800,
        title_text="Scaled Relative Performance and Distribution of Percentage Changes",
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
