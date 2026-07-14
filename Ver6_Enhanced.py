# Ver6_Enhanced.py
# Changes made:
# 3. Added option to download chart as PNG.
# 4. Added option to download data as CSV.
# Inherited all features from Ver6.py:
# - Multiple stock comparison
# - SMA/EMA selection
# - RSI, MACD with histogram, Bollinger Bands
# - Trading signals (BUY/SELL/HOLD with reasoning)
# - Statistics panel
# - Error handling for ticker/date/data
# - Icons for sections
# - Market status + live mode auto-refresh
# - RUNNING marker for clarity

import yfinance as yf
import plotly.graph_objs as go
import streamlit as st
import pandas as pd
from datetime import date, datetime
from streamlit_autorefresh import st_autorefresh

# Title
st.title("📈 Stock Market Dashboard - V6 (Enhanced)")
st.write("RUNNING: Ver6_Enhanced.py")

# Sidebar inputs
st.sidebar.header("User Input")
tickers = st.sidebar.text_input("Enter Stock Tickers (comma-separated)", "AAPL,MSFT,TSLA")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", value=date.today())

# Market Status
now = datetime.utcnow()
market_open = now.hour >= 13 and now.hour < 20
if market_open:
    st.sidebar.success("🟢 Market Open")
else:
    st.sidebar.error("🔴 Market Closed")

# Live mode toggle
live_mode = st.sidebar.checkbox("Enable Live Mode", value=False)
refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 10, 300, 60)
if live_mode:
    st_autorefresh(interval=refresh_interval * 1000, key="refresh")

# SMA/EMA selection
ma_type = st.sidebar.selectbox("Select Moving Average Type", ["SMA", "EMA"])
ma_window = st.sidebar.slider("Moving Average Window", 10, 100, 50)

placeholder = st.empty()

# --- Functions ---
def fetch_data(ticker, start_date, end_date):
    if not ticker.strip():
        st.error("❌ Please enter a valid ticker symbol.")
        return pd.DataFrame()
    if start_date >= end_date:
        st.error("❌ Start Date must be earlier than End Date.")
        return pd.DataFrame()
    try:
        data = yf.download(ticker, start=start_date, end=end_date, multi_level_index=False)
    except Exception as e:
        st.error(f"⚠️ Error fetching {ticker}: {e}")
        return pd.DataFrame()
    if data.empty:
        st.warning(f"⚠️ No data available for {ticker}.")
        return pd.DataFrame()
    return data

def calculate_indicators(data):
    if data.empty:
        return data
    # Bollinger Bands
    window = 20
    data['MA20'] = data['Close'].rolling(window=window).mean()
    std = data['Close'].rolling(window=window).std()
    data['Upper'] = data['MA20'] + (2 * std)
    data['Lower'] = data['MA20'] - (2 * std)
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
    data['Histogram'] = data['MACD'] - data['Signal']
    return data

def calculate_ma(data, ma_type, window):
    if data.empty:
        return data
    if ma_type == "SMA":
        data[f"{window}-day SMA"] = data['Close'].rolling(window=window).mean()
    else:
        data[f"{window}-day EMA"] = data['Close'].ewm(span=window, adjust=False).mean()
    return data

def plot_stock(data, ticker, ma_type, window):
    st.subheader(f"📊 {ticker}")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name=f"{ticker} Close"))
    ma_col = f"{window}-day {ma_type}"
    if ma_col in data.columns:
        fig.add_trace(go.Scatter(x=data.index, y=data[ma_col], name=ma_col))
    fig.add_trace(go.Scatter(x=data.index, y=data['Upper'], name='Upper Band', line=dict(dash='dot')))
    fig.add_trace(go.Scatter(x=data.index, y=data['Lower'], name='Lower Band', line=dict(dash='dot')))
    fig.update_layout(title=f"{ticker} Price with {ma_type} + Bollinger Bands", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    # Download chart as PNG
    st.download_button(
        label="📥 Download Chart (PNG)",
        data=fig.to_image(format="png"),
        file_name=f"{ticker}_chart.png",
        mime="image/png"
    )

    # RSI
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI'))
    fig_rsi.add_hline(y=70, line=dict(color="red", dash="dash"))
    fig_rsi.add_hline(y=30, line=dict(color="green", dash="dash"))
    fig_rsi.update_layout(title="RSI (14-day)", yaxis=dict(range=[0,100]), template="plotly_dark")
    st.plotly_chart(fig_rsi, use_container_width=True)

    # MACD
    fig_macd = go.Figure()
    fig_macd.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD'))
    fig_macd.add_trace(go.Scatter(x=data.index, y=data['Signal'], name='Signal'))
    fig_macd.add_trace(go.Bar(x=data.index, y=data['Histogram'], name='Histogram', opacity=0.5))
    fig_macd.update_layout(title="MACD with Histogram", template="plotly_dark")
    st.plotly_chart(fig_macd, use_container_width=True)

    # Statistics
    st.subheader("📊 Stock Statistics")
    st.write(f"Average Closing Price: {float(data['Close'].mean()):.2f}")
    st.write(f"Highest Closing Price: {float(data['Close'].max()):.2f}")
    st.write(f"Lowest Closing Price: {float(data['Close'].min()):.2f}")
    st.write(f"Highest Volume: {int(data['Volume'].max())}")
    st.write(f"Average Volume: {int(data['Volume'].mean())}")
    st.write(f"Latest RSI: {float(data['RSI'].iloc[-1]):.2f}")
    st.write(f"Latest MACD: {float(data['MACD'].iloc[-1]):.2f}")

    # Download data as CSV
    st.download_button(
        label="📥 Download Data (CSV)",
        data=data.to_csv().encode("utf-8"),
        file_name=f"{ticker}_data.csv",
        mime="text/csv"
    )

# --- Main Execution ---
for ticker in [t.strip().upper() for t in tickers.split(",")]:
    data = fetch_data(ticker, start_date, end_date)
    if not data.empty:
        data = calculate_indicators(data)
        data = calculate_ma(data, ma_type, ma_window)
        plot_stock(data, ticker, ma_type, ma_window)
