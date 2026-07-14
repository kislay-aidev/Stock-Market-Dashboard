# Ver4_Enhanced6.py
# Changes made:
# 9. Removed unused imports (like time).
#    Bug fixed: Cleaner code, avoids confusion and unnecessary dependencies.
# 10. Organized code into modular functions:
#     - fetch_data()
#     - calculate_indicators()
#     - plot_price()
#     - plot_volume()
#     - plot_rsi()
#     - plot_macd()
#     - show_statistics()
#     Enhancement: Easier to maintain, extend, and debug. Clear separation of concerns.

import yfinance as yf
import plotly.graph_objs as go
import streamlit as st
import pandas as pd
from datetime import date, datetime
from streamlit_autorefresh import st_autorefresh

# Title
st.title("📈 Stock Market Dashboard - V4 (Real-Time Updates)")
st.write("RUNNING: Ver4_Enhanced6.py")

# Sidebar inputs
st.sidebar.header("User Input")
ticker = st.sidebar.text_input("Enter Stock Ticker", "AAPL")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", value=date.today())

# Live mode toggle
live_mode = st.sidebar.checkbox("Enable Live Mode", value=False)
refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 10, 300, 60)

# Trigger auto-refresh if live mode is enabled
if live_mode:
    st_autorefresh(interval=refresh_interval * 1000, key="refresh")

# Placeholder for charts
placeholder = st.empty()

# --- Modular Functions ---

def fetch_data(ticker, start_date, end_date):
    try:
        data = yf.download(ticker, start=start_date, end=end_date, multi_level_index=False)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
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

    return data

def plot_price(data, ticker):
    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name="Candlestick"
    )])
    fig.add_trace(go.Scatter(x=data.index, y=data['Upper'], name='Upper Band', line=dict(dash='dot')))
    fig.add_trace(go.Scatter(x=data.index, y=data['Lower'], name='Lower Band', line=dict(dash='dot')))
    fig.update_layout(title=f"{ticker} Candlestick with Bollinger Bands", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

def plot_volume(data):
    fig_vol = go.Figure()
    fig_vol.add_trace(go.Bar(x=data.index, y=data['Volume'], name='Volume'))
    fig_vol.update_layout(title="Trading Volume", template="plotly_dark")
    st.plotly_chart(fig_vol, use_container_width=True)

def plot_rsi(data):
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI'))
    fig_rsi.update_layout(title="RSI (14-day)", yaxis=dict(range=[0,100]), template="plotly_dark")
    st.plotly_chart(fig_rsi, use_container_width=True)

def plot_macd(data):
    fig_macd = go.Figure()
    fig_macd.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD'))
    fig_macd.add_trace(go.Scatter(x=data.index, y=data['Signal'], name='Signal'))
    fig_macd.update_layout(title="MACD", template="plotly_dark")
    st.plotly_chart(fig_macd, use_container_width=True)

def show_statistics(data):
    st.subheader("📊 Stock Statistics")
    st.write(f"Average Closing Price: {float(data['Close'].mean()):.2f}")
    st.write(f"Max Closing Price: {float(data['Close'].max()):.2f}")
    st.write(f"Min Closing Price: {float(data['Close'].min()):.2f}")

    # Buy/Sell indicator logic
    st.subheader("📌 Trading Signal")
    latest_rsi = data['RSI'].iloc[-1]
    latest_macd = data['MACD'].iloc[-1]
    latest_signal = data['Signal'].iloc[-1]

    if latest_rsi < 30 and latest_macd > latest_signal:
        st.success("BUY Signal: RSI oversold & MACD bullish crossover")
    elif latest_rsi > 70 and latest_macd < latest_signal:
        st.error("SELL Signal: RSI overbought & MACD bearish crossover")
    else:
        st.info("HOLD Signal: No strong buy/sell indication")

# --- Main Execution ---
def run_dashboard():
    data = fetch_data(ticker, start_date, end_date)
    if data.empty:
        return
    data = calculate_indicators(data)

    with placeholder.container():
        # Current price metric
        current = data['Close'].iloc[-1]
        previous = data['Close'].iloc[-2]
        change = current - previous
        st.metric("Current Price", f"${current:.2f}", f"{change:.2f}")

        # Last updated timestamp
        st.caption(f"Last Updated: {datetime.now().strftime('%H:%M:%S')}")

        plot_price(data, ticker)
        plot_volume(data)
        plot_rsi(data)
        plot_macd(data)
        show_statistics(data)

# Run once (Streamlit reruns automatically if live mode is enabled)
run_dashboard()
