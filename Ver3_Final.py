# Changed the Multi-Index dataset series to single-index.
# Instead of:
# data = yf.download(ticker, start=start_date, end=end_date)

# if isinstance(data.columns, pd.MultiIndex):
#     data.columns = data.columns.get_level_values(0)

# Used this:
# data = yf.download(
#     ticker,
#     start=start_date,
#     end=end_date,
#     multi_level_index=False
# )

# Also, avoided hardcoding the end date to a specific date, and instead used the current date as the default end date.
# end_date = st.sidebar.date_input("End Date", pd.to_datetime("2026-07-12"))
# the line: pd.to_datetime("2026-07-12")

# Now used this instead: 
# from datetime import date

# end_date = st.sidebar.date_input(
#     "End Date",
#     value=date.today()
# )

# Also added :
# st.write("RUNNING: Ver3_Enhanced5.py")
# Immediately after the title.
# To see, which file is run after running the streamlit app.

import yfinance as yf
import plotly.graph_objs as go
import streamlit as st
import pandas as pd

from datetime import date

# Title
st.title("📈 Stock Market Dashboard - V3 (Technical Indicators)")

# App Run Check
st.write("RUNNING: Ver3_Enhanced5.py")

# Sidebar inputs
st.sidebar.header("User Input")
ticker = st.sidebar.text_input("Enter Stock Ticker", "AAPL")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input(
    "End Date",
    value=date.today()
)

# Fetch data
data = yf.download(
    ticker,
    start=start_date,
    end=end_date,
    multi_level_index=False
)

if data.empty:
    st.warning("⚠️ No data available for this ticker/date range.")
else:
    # --- Indicators ---
    # RSI
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    data['RSI'] = 100 - (100 / (1 + rs))

    # MACD
    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = exp1 - exp2
    data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()

    # Bollinger Bands
    window = 20
    data['MA20'] = data['Close'].rolling(window=window).mean()

    # Correct std calculation (already a Series)
    std = data['Close'].rolling(window=window).std()

    # Assign safely
    data['Upper'] = data['MA20'] + (2 * std)
    data['Lower'] = data['MA20'] - (2 * std)


    # --- Plot ---
    fig = go.Figure()

    # Price + Bollinger Bands
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Close Price'))
    fig.add_trace(go.Scatter(x=data.index, y=data['Upper'], name='Upper Band', line=dict(dash='dot')))
    fig.add_trace(go.Scatter(x=data.index, y=data['Lower'], name='Lower Band', line=dict(dash='dot')))

    # Layout
    fig.update_layout(title=f"{ticker} Price with Bollinger Bands", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    # RSI Plot
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI'))
    fig_rsi.update_layout(title="RSI (14-day)", yaxis=dict(range=[0,100]), template="plotly_dark")
    st.plotly_chart(fig_rsi, use_container_width=True)

    # MACD Plot
    fig_macd = go.Figure()
    fig_macd.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD'))
    fig_macd.add_trace(go.Scatter(x=data.index, y=data['Signal'], name='Signal'))
    fig_macd.update_layout(title="MACD", template="plotly_dark")
    st.plotly_chart(fig_macd, use_container_width=True)

    # Stats
    st.subheader("📊 Stock Statistics")
    st.write(f"Average Closing Price: {float(data['Close'].mean()):.2f}")
    st.write(f"Max Closing Price: {float(data['Close'].max()):.2f}")
    st.write(f"Min Closing Price: {float(data['Close'].min()):.2f}")
