# Ver5_Enhanced4.py
# Changes made:
# 9. Added consistent icons across dashboard sections:
#    📈 for Price, 📊 for Statistics, 📉 for RSI/MACD, 💹 for Trading Signal.
#    Enhancement: Improves visual appeal and readability.
# 10. README.md content prepared separately (not inside this file).
#    Enhancement: Ensures proper documentation with Overview, Features, Screenshots, Installation, etc.

import yfinance as yf
import plotly.graph_objs as go
import streamlit as st
import pandas as pd
from datetime import date, datetime
from streamlit_autorefresh import st_autorefresh

# Title
st.title("📈 Stock Market Dashboard - V5 (Enhanced)")
st.write("RUNNING: Ver5_Enhanced4.py")

# Sidebar inputs
st.sidebar.header("User Input")
ticker = st.sidebar.text_input("Enter Stock Ticker", "AAPL")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", value=date.today())

# Market Status
now = datetime.utcnow()
market_open = now.hour >= 13 and now.hour < 20  # 9:30am–4pm EST ~ 13:30–20:00 UTC
if market_open:
    st.sidebar.success("🟢 Market Open")
else:
    st.sidebar.error("🔴 Market Closed")

# Live mode toggle
live_mode = st.sidebar.checkbox("Enable Live Mode", value=False)
refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 10, 300, 60)
if live_mode:
    st_autorefresh(interval=refresh_interval * 1000, key="refresh")

placeholder = st.empty()

# --- Modular Functions ---

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
        st.error(f"⚠️ Error fetching data: {e}")
        return pd.DataFrame()
    if data.empty:
        st.warning("⚠️ No data available for this ticker/date range.")
        return pd.DataFrame()
    return data

def calculate_indicators(data):
    if data.empty:
        return data
    window = 20
    data['MA20'] = data['Close'].rolling(window=window).mean()
    std = data['Close'].rolling(window=window).std()
    data['Upper'] = data['MA20'] + (2 * std)
    data['Lower'] = data['MA20'] - (2 * std)
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    data['RSI'] = 100 - (100 / (1 + rs))
    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = exp1 - exp2
    data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
    data['Histogram'] = data['MACD'] - data['Signal']
    return data

def plot_price(data, ticker):
    st.subheader("📈 Price Chart")
    fig = go.Figure(data=[go.Candlestick(
        x=data.index, open=data['Open'], high=data['High'],
        low=data['Low'], close=data['Close'], name="Candlestick"
    )])
    fig.add_trace(go.Scatter(x=data.index, y=data['Upper'], name='Upper Band', line=dict(dash='dot')))
    fig.add_trace(go.Scatter(x=data.index, y=data['Lower'], name='Lower Band', line=dict(dash='dot')))
    fig.update_layout(title=f"{ticker} Candlestick with Bollinger Bands", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

def plot_volume(data):
    st.subheader("📊 Volume")
    fig_vol = go.Figure()
    fig_vol.add_trace(go.Bar(x=data.index, y=data['Volume'], name='Volume'))
    fig_vol.update_layout(title="Trading Volume", template="plotly_dark")
    st.plotly_chart(fig_vol, use_container_width=True)

def plot_rsi(data):
    st.subheader("📉 RSI")
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI'))
    fig_rsi.add_hline(y=70, line=dict(color="red", dash="dash"))
    fig_rsi.add_hline(y=30, line=dict(color="green", dash="dash"))
    fig_rsi.update_layout(title="RSI (14-day)", yaxis=dict(range=[0,100]), template="plotly_dark")
    st.plotly_chart(fig_rsi, use_container_width=True)

def plot_macd(data):
    st.subheader("📉 MACD")
    fig_macd = go.Figure()
    fig_macd.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD'))
    fig_macd.add_trace(go.Scatter(x=data.index, y=data['Signal'], name='Signal'))
    fig_macd.add_trace(go.Bar(x=data.index, y=data['Histogram'], name='Histogram', opacity=0.5))
    fig_macd.update_layout(title="MACD with Histogram", template="plotly_dark")
    st.plotly_chart(fig_macd, use_container_width=True)

def show_statistics(data):
    st.subheader("📊 Stock Statistics")
    st.write(f"Average Closing Price: {float(data['Close'].mean()):.2f}")
    st.write(f"Highest Closing Price: {float(data['Close'].max()):.2f}")
    st.write(f"Lowest Closing Price: {float(data['Close'].min()):.2f}")
    st.write(f"Highest Volume: {int(data['Volume'].max())}")
    st.write(f"Average Volume: {int(data['Volume'].mean())}")
    st.write(f"Latest RSI: {float(data['RSI'].iloc[-1]):.2f}")
    st.write(f"Latest MACD: {float(data['MACD'].iloc[-1]):.2f}")

def show_trading_signal(data):
    st.subheader("💹 Trading Signal")
    latest_rsi = data['RSI'].iloc[-1]
    latest_macd = data['MACD'].iloc[-1]
    latest_signal = data['Signal'].iloc[-1]
    latest_price = data['Close'].iloc[-1]
    if latest_rsi < 30 and latest_macd > latest_signal and latest_price <= data['Lower'].iloc[-1]:
        st.success("BUY Signal")
        st.write(f"Reason: RSI = {latest_rsi:.2f} (oversold), MACD bullish crossover, Price near Lower Bollinger Band")
    elif latest_rsi > 70 and latest_macd < latest_signal and latest_price >= data['Upper'].iloc[-1]:
        st.error("SELL Signal")
        st.write(f"Reason: RSI = {latest_rsi:.2f} (overbought), MACD bearish crossover, Price near Upper Bollinger Band")
    else:
        st.info("HOLD Signal")
        st.write(f"Reason: RSI = {latest_rsi:.2f}, MACD neutral, Price not at extremes")

# --- Main Execution ---
def run_dashboard():
    data = fetch_data(ticker, start_date, end_date)
    if data.empty:
        return
    data = calculate_indicators(data)

    with placeholder.container():
        # Price Card
        current = data['Close'].iloc[-1]
        today_high = data['High'].iloc[-1]
        today_low = data['Low'].iloc[-1]
        today_volume = data['Volume'].iloc[-1]
        previous = data['Close'].iloc[-2]
        change = current - previous

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📈 Current Price", f"${current:.2f}", f"{change:.2f}")
        col2.metric("Today's High", f"${today_high:.2f}")
        col3.metric("Today's Low", f"${today_low:.2f}")
        col4.metric("Today's Volume", f"{int(today_volume)}")

        st.caption(f"Last Updated: {datetime.now().strftime('%H:%M:%S')}")

        # Statistics
        show_statistics(data)

        # Trading Signal
        show_trading_signal(data)

        # Charts
        plot_price(data, ticker)
        plot_volume(data)
        plot_rsi(data)
        plot_macd(data)

# Run once
run_dashboard()
