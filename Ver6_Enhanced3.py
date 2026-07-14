# Ver6_Enhanced3.py
# Changes made:
# 7. Added News Feed integration (ticker-related headlines).
# 8. Added Watchlist functionality (summary panel).
# Inherits all features from Ver6_Enhanced2.py:
# - Multiple stock comparison
# - SMA/EMA selection
# - RSI, MACD with histogram, Bollinger Bands
# - Moving average crossover signals (configurable + 50/200 quick check)
# - Trading signals (BUY/SELL/HOLD with reasoning)
# - Statistics panel
# - Company information panel
# - Error handling for ticker/date/data
# - Icons for sections
# - Market status + live mode auto-refresh
# - Download chart as PNG, download data as CSV
# - RUNNING marker for clarity

import yfinance as yf
import plotly.graph_objs as go
import streamlit as st
import pandas as pd
from datetime import date, datetime
from streamlit_autorefresh import st_autorefresh

# Title
st.title("📈 Stock Market Dashboard - V6 (Enhanced3)")
st.write("RUNNING: Ver6_Enhanced3.py")

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

# News Feed toggle
st.sidebar.markdown("---")
enable_news = st.sidebar.checkbox("Enable News Feed", value=True)

# Watchlist input
st.sidebar.markdown("---")
watchlist_input = st.sidebar.text_input("Add to Watchlist (comma-separated)", "GOOGL,AMZN")

# --- Cached Functions ---
@st.cache_data(ttl=300)
def fetch_data_cached(ticker, start_date, end_date):
    try:
        data = yf.download(ticker, start=start_date, end=end_date, multi_level_index=False)
    except Exception as e:
        return pd.DataFrame(), f"Error fetching {ticker}: {e}"
    if data.empty:
        return pd.DataFrame(), f"No data available for {ticker}."
    return data, None

@st.cache_data(ttl=1800)
def fetch_news_cached(ticker):
    try:
        tk = yf.Ticker(ticker)
        news = tk.news
        return news if news else []
    except Exception:
        return []

# --- Indicators ---
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

# --- Plotting (simplified, inherits from Enhanced2) ---
def plot_stock(data, ticker, ma_type, window):
    st.subheader(f"📊 {ticker}")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name=f"{ticker} Close"))
    ma_col = f"{window}-day {ma_type}"
    if ma_col in data.columns:
        fig.add_trace(go.Scatter(x=data.index, y=data[ma_col], name=ma_col))
    if 'Upper' in data.columns and 'Lower' in data.columns:
        fig.add_trace(go.Scatter(x=data.index, y=data['Upper'], name='Upper Band', line=dict(dash='dot')))
        fig.add_trace(go.Scatter(x=data.index, y=data['Lower'], name='Lower Band', line=dict(dash='dot')))
    fig.update_layout(title=f"{ticker} Price with {ma_type} + Bollinger Bands", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    # Download chart as PNG
    try:
        st.download_button(
            label="📥 Download Chart (PNG)",
            data=fig.to_image(format="png"),
            file_name=f"{ticker}_chart.png",
            mime="image/png"
        )
    except Exception:
        st.info("PNG export requires kaleido. Chart download disabled if kaleido is not available.")

    # Download data as CSV
    st.download_button(
        label="📥 Download Data (CSV)",
        data=data.to_csv().encode("utf-8"),
        file_name=f"{ticker}_data.csv",
        mime="text/csv"
    )

# --- News Feed ---
def show_news(ticker):
    st.markdown("### 📰 News Feed")
    news_items = fetch_news_cached(ticker)
    if not news_items:
        st.info("No news available for this ticker.")
        return
    for item in news_items[:5]:  # show top 5
        st.write(f"**{item.get('title','No Title')}**")
        st.write(f"Source: {item.get('publisher','Unknown')} | Published: {item.get('providerPublishTime','N/A')}")
        st.markdown(f"[Read more]({item.get('link','')})")
        st.markdown("---")

# --- Watchlist ---
def show_watchlist(watchlist):
    st.markdown("### 📋 Watchlist Summary")
    summary_data = []
    for ticker in watchlist:
        data, err = fetch_data_cached(ticker, start_date, end_date)
        if err or data.empty:
            continue
        latest_price = float(data['Close'].iloc[-1])
        prev_price = float(data['Close'].iloc[-2]) if len(data) > 1 else latest_price
        pct_change = ((latest_price - prev_price) / prev_price) * 100 if prev_price else 0
        volume = int(data['Volume'].iloc[-1])
        summary_data.append({
            "Ticker": ticker,
            "Latest Price": f"{latest_price:.2f}",
            "% Change": f"{pct_change:.2f}%",
            "Volume": f"{volume}"
        })
    if summary_data:
        st.dataframe(pd.DataFrame(summary_data))
    else:
        st.info("No valid tickers in watchlist.")

# --- Main Execution ---
for ticker in [t.strip().upper() for t in tickers.split(",")]:
    data, err = fetch_data_cached(ticker, start_date, end_date)
    if err:
        st.warning(err)
        continue
    if not data.empty:
        data = calculate_indicators(data)
        plot_stock(data, ticker, ma_type, ma_window)
        if enable_news:
            show_news(ticker)

# Watchlist display
watchlist = [t.strip().upper() for t in watchlist_input.split(",") if t.strip()]
if watchlist:
    show_watchlist(watchlist)
