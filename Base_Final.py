import yfinance as yf
import plotly.graph_objs as go
import streamlit as st
import pandas as pd

# Title
st.title("📈 Stock Market Dashboard - V1")

# Sidebar inputs
st.sidebar.header("User Input")
ticker = st.sidebar.text_input("Enter Stock Ticker", "AAPL")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2026-07-12"))

# Fetch data
data = yf.download(ticker, start=start_date, end=end_date)

if data.empty:
    st.warning("⚠️ No data available for this ticker/date range.")
else:
    # Moving Average
    window = 50
    data[f"{window}-day MA"] = data['Close'].rolling(window=window).mean()

    # Plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], 
                             mode='lines', name='Close Price'))
    fig.add_trace(go.Scatter(x=data.index, y=data[f"{window}-day MA"], 
                             mode='lines', name=f'{window}-day MA'))

    # Axis scaling
    fig.update_layout(
        title=f"{ticker} Stock Price",
        xaxis_title="Date",
        yaxis=dict(title="Price (USD)", 
                   range=[data['Close'].min()*0.95, data['Close'].max()*1.05]),
        template="plotly_dark"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Basic stats
    st.subheader("📊 Stock Statistics")
    avg_close = float(data['Close'].mean())
    max_close = float(data['Close'].max())
    min_close = float(data['Close'].min())

    st.write(f"Average Closing Price: {avg_close:.2f}")
    st.write(f"Max Closing Price: {max_close:.2f}")
    st.write(f"Min Closing Price: {min_close:.2f}")
