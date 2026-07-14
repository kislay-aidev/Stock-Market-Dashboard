import yfinance as yf
import plotly.graph_objs as go
import streamlit as st
import pandas as pd

# Title
st.title("📈 Stock Market Dashboard - V2 (Multi-Stock Comparison)")

# Sidebar inputs
st.sidebar.header("User Input")
tickers_input = st.sidebar.text_input("Enter Stock Tickers (comma-separated)", "AAPL,MSFT,TSLA")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2026-07-12"))

tickers = [t.strip().upper() for t in tickers_input.split(",")]

# Plot setup
fig = go.Figure()

stats_data = []

for ticker in tickers:
    data = yf.download(ticker, start=start_date, end=end_date)

    if data.empty:
        st.warning(f"⚠️ No data available for {ticker}.")
        continue

    # Moving Average
    window = 50
    data[f"{window}-day MA"] = data['Close'].rolling(window=window).mean()

    # Add traces
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'],
                             mode='lines', name=f'{ticker} Close'))
    fig.add_trace(go.Scatter(x=data.index, y=data[f"{window}-day MA"],
                             mode='lines', name=f'{ticker} {window}-day MA'))

    # Collect stats
    stats_data.append({
        "Ticker": ticker,
        "Average Close": float(data['Close'].mean()),
        "Max Close": float(data['Close'].max()),
        "Min Close": float(data['Close'].min())
    })

# Chart layout
fig.update_layout(
    title="Multi-Stock Comparison",
    xaxis_title="Date",
    yaxis_title="Price (USD)",
    template="plotly_dark"
)

st.plotly_chart(fig, use_container_width=True)

# Stats table
if stats_data:
    st.subheader("📊 Stock Statistics")
    stats_df = pd.DataFrame(stats_data)
    st.dataframe(stats_df.set_index("Ticker"))
