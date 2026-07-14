# Ver6_Enhanced2.py
# Merged and improved version combining user's style and robustness fixes
# Features:
# - Multiple stock comparison
# - SMA/EMA selection
# - RSI, MACD with histogram, Bollinger Bands
# - Moving average crossover signals (50/200 golden/death + configurable short/long)
# - Robust zero-cross detection for arbitrary short/long MAs
# - Auto-swap short/long windows with info
# - BUY/SELL markers on price chart
# - Company information panel with caching and human-friendly formatting
# - Download chart as PNG and data as CSV
# - Market status + live mode auto-refresh
# - RUNNING marker for clarity
# - Error handling for ticker/date/data
# - Keeps your visual style and layout

import yfinance as yf
import plotly.graph_objs as go
import streamlit as st
import pandas as pd
from datetime import date, datetime
from streamlit_autorefresh import st_autorefresh

# Title and run marker
st.title("📈 Stock Market Dashboard - V6 (Enhanced2)")
st.write("RUNNING: Ver6_Enhanced2.py")

# Sidebar inputs
st.sidebar.header("User Input")
tickers = st.sidebar.text_input("Enter Stock Tickers (comma-separated)", "AAPL,MSFT,TSLA")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", value=date.today())

# Market Status (UTC approximation with weekend handling)
now = datetime.utcnow()
weekday = now.weekday()
market_open = (weekday < 5) and (13 <= now.hour < 20)
if market_open:
    st.sidebar.success("🟢 US Market Open (approx., UTC)")
else:
    st.sidebar.error("🔴 US Market Closed (weekends/UTC approximation)")

# Live mode toggle
live_mode = st.sidebar.checkbox("Enable Live Mode", value=False)
refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 10, 300, 60)
if live_mode:
    st_autorefresh(interval=refresh_interval * 1000, key="refresh")

# SMA/EMA selection
ma_type = st.sidebar.selectbox("Select Moving Average Type", ["SMA", "EMA"])
ma_window = st.sidebar.slider("Moving Average Window (for display)", 10, 100, 50)

# Crossover settings
st.sidebar.markdown("---")
st.sidebar.subheader("Crossover Settings")
short_window = st.sidebar.number_input("Short MA Window", min_value=2, max_value=200, value=20, step=1)
long_window = st.sidebar.number_input("Long MA Window", min_value=3, max_value=400, value=50, step=1)

# Auto-swap if short >= long
if short_window >= long_window:
    st.sidebar.info(f"Swapping windows for crossover: short={short_window}, long={long_window}")
    short_window, long_window = min(short_window, long_window), max(short_window, long_window)


# Utility: human-friendly number formatting
def human_format(num):
    try:
        num = float(num)
    except Exception:
        return str(num)
    magnitude = 0
    units = ['', 'K', 'M', 'B', 'T']
    while abs(num) >= 1000 and magnitude < len(units) - 1:
        magnitude += 1
        num /= 1000.0
    return f'{num:.2f}{units[magnitude]}'

# --- Cached fetch functions ---
@st.cache_data(ttl=300)
def fetch_data_cached(ticker, start_date, end_date):
    try:
        data = yf.download(ticker, start=start_date, end=end_date, multi_level_index=False)
    except Exception as e:
        return pd.DataFrame(), f"Error fetching {ticker}: {e}"
    if data.empty:
        return pd.DataFrame(), f"No data available for {ticker}."
    return data, None

@st.cache_data(ttl=3600)
def fetch_company_info_cached(ticker):
    try:
        tk = yf.Ticker(ticker)
        info = tk.info or {}
        if not info:
            return {}, "No company info available from yfinance."
        company = {
            "longName": info.get("longName") or info.get("shortName") or ticker,
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "marketCap": info.get("marketCap", "N/A"),
            "trailingPE": info.get("trailingPE", "N/A"),
            "forwardPE": info.get("forwardPE", "N/A"),
            "website": info.get("website", "N/A"),
            "country": info.get("country", "N/A"),
            "fullTimeEmployees": info.get("fullTimeEmployees", "N/A"),
            "longBusinessSummary": info.get("longBusinessSummary", "N/A")
        }
        return company, None
    except Exception as e:
        return {}, f"Error fetching company info: {e}"

# --- Indicator calculations ---
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

def calculate_ma(data, ma_type, window):
    if data.empty:
        return data
    col_name = f"{window}-day {ma_type}"
    if ma_type == "SMA":
        data[col_name] = data['Close'].rolling(window=window).mean()
    else:
        data[col_name] = data['Close'].ewm(span=window, adjust=False).mean()
    return data

# Robust crossover detection for arbitrary short/long windows
def calculate_crossovers(data, short_w, long_w, ma_kind="SMA"):
    if data.empty:
        return data, {"signal": "N/A", "reason": "No data"}
    short_col = f"MA_{short_w}"
    long_col = f"MA_{long_w}"
    if ma_kind == "SMA":
        data[short_col] = data['Close'].rolling(window=short_w).mean()
        data[long_col] = data['Close'].rolling(window=long_w).mean()
    else:
        data[short_col] = data['Close'].ewm(span=short_w, adjust=False).mean()
        data[long_col] = data['Close'].ewm(span=long_w, adjust=False).mean()
    diff = data[short_col] - data[long_col]
    data[f"Diff_{short_w}_{long_w}"] = diff
    prev = diff.shift(1)
    cross_up = (prev < 0) & (diff > 0)
    cross_down = (prev > 0) & (diff < 0)
    data['Crossover_Event'] = None
    data.loc[cross_up, 'Crossover_Event'] = "BUY"
    data.loc[cross_down, 'Crossover_Event'] = "SELL"
    events = data.loc[data['Crossover_Event'].notna(), ['Crossover_Event']]
    latest_signal = "HOLD"
    reason = "No recent crossover detected."
    last_date = None
    if not events.empty:
        last_idx = events.index[-1]
        last_event = events['Crossover_Event'].iloc[-1]
        last_date = last_idx
        if last_event == "BUY":
            latest_signal = "BUY"
            reason = f"Short MA ({short_w}) crossed above Long MA ({long_w}) on {last_idx.date()} — bullish (golden cross)."
        else:
            latest_signal = "SELL"
            reason = f"Short MA ({short_w}) crossed below Long MA ({long_w}) on {last_idx.date()} — bearish (death cross)."
    else:
        if not pd.isna(diff.iloc[-1]):
            if diff.iloc[-1] > 0:
                latest_signal = "BUY"
                reason = f"Short MA ({short_w}) is above Long MA ({long_w}) — trend appears bullish."
            elif diff.iloc[-1] < 0:
                latest_signal = "SELL"
                reason = f"Short MA ({short_w}) is below Long MA ({long_w}) — trend appears bearish."
            else:
                latest_signal = "HOLD"
                reason = "Short and Long MA are equal — no clear trend."
    return data, {"signal": latest_signal, "reason": reason, "last_date": last_date}

# Quick 50/200 golden/death cross detector (keeps your original convenience)
def detect_50_200_crossover(data):
    if len(data) < 200:
        return "⚪ Not enough data for 200-day crossover."
    data["SMA50"] = data["Close"].rolling(window=50).mean()
    data["SMA200"] = data["Close"].rolling(window=200).mean()
    if pd.isna(data["SMA50"].iloc[-1]) or pd.isna(data["SMA200"].iloc[-1]):
        return "⚪ Not enough data for crossover detection."
    if data["SMA50"].iloc[-1] > data["SMA200"].iloc[-1] and data["SMA50"].iloc[-2] <= data["SMA200"].iloc[-2]:
        return "🟢 Golden Cross Detected (Bullish)"
    elif data["SMA50"].iloc[-1] < data["SMA200"].iloc[-1] and data["SMA50"].iloc[-2] >= data["SMA200"].iloc[-2]:
        return "🔴 Death Cross Detected (Bearish)"
    else:
        return "⚪ No Crossover Signal"
    
# News Feed toggle
st.sidebar.markdown("---")
enable_news = st.sidebar.checkbox("Enable News Feed", value=True)

# Watchlist input
st.sidebar.markdown("---")
watchlist_input = st.sidebar.text_input("Add to Watchlist (comma-separated)", "GOOGL,AMZN")

# Plotting with markers and download buttons
def plot_stock_with_features(data, ticker, ma_type, window, short_w, long_w):
    st.subheader(f"📊 {ticker}")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name=f"{ticker} Close", line=dict(color="white")))
    display_col = f"{window}-day {ma_type}"
    if display_col in data.columns:
        fig.add_trace(go.Scatter(x=data.index, y=data[display_col], name=display_col, line=dict(color="cyan")))
    short_col = f"MA_{short_w}"
    long_col = f"MA_{long_w}"
    if short_col in data.columns:
        fig.add_trace(go.Scatter(x=data.index, y=data[short_col], name=f"MA {short_w}", line=dict(color="yellow")))
    if long_col in data.columns:
        fig.add_trace(go.Scatter(x=data.index, y=data[long_col], name=f"MA {long_w}", line=dict(color="orange")))
    if 'Upper' in data.columns and 'Lower' in data.columns:
        fig.add_trace(go.Scatter(x=data.index, y=data['Upper'], name='Upper Band', line=dict(dash='dot')))
        fig.add_trace(go.Scatter(x=data.index, y=data['Lower'], name='Lower Band', line=dict(dash='dot')))
    buys = data.loc[data['Crossover_Event'] == "BUY"]
    sells = data.loc[data['Crossover_Event'] == "SELL"]
    if not buys.empty:
        fig.add_trace(go.Scatter(x=buys.index, y=buys['Close'], mode='markers', marker_symbol='triangle-up', marker_color='green', marker_size=12, name='BUY'))
    if not sells.empty:
        fig.add_trace(go.Scatter(x=sells.index, y=sells['Close'], mode='markers', marker_symbol='triangle-down', marker_color='red', marker_size=12, name='SELL'))
    fig.update_layout(title=f"{ticker} Price with MAs + Bollinger Bands", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
    try:
        png = fig.to_image(format="png")
        st.download_button(label="📥 Download Chart (PNG)", data=png, file_name=f"{ticker}_chart.png", mime="image/png")
    except Exception:
        st.info("PNG export requires kaleido. Chart download disabled if kaleido is not available.")
    # RSI
    if 'RSI' in data.columns:
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI'))
        fig_rsi.add_hline(y=70, line=dict(color="red", dash="dash"))
        fig_rsi.add_hline(y=30, line=dict(color="green", dash="dash"))
        fig_rsi.update_layout(title="RSI (14-day)", yaxis=dict(range=[0,100]), template="plotly_dark")
        st.plotly_chart(fig_rsi, use_container_width=True)
    # MACD
    if 'MACD' in data.columns and 'Signal' in data.columns:
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD'))
        fig_macd.add_trace(go.Scatter(x=data.index, y=data['Signal'], name='Signal'))
        if 'Histogram' in data.columns:
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
    if 'RSI' in data.columns:
        st.write(f"Latest RSI: {float(data['RSI'].iloc[-1]):.2f}")
    if 'MACD' in data.columns:
        st.write(f"Latest MACD: {float(data['MACD'].iloc[-1]):.2f}")
    # Download CSV
    st.download_button(label="📥 Download Data (CSV)", data=data.to_csv().encode("utf-8"), file_name=f"{ticker}_data.csv", mime="text/csv")

# Company info display
def show_company_info_cached(ticker):
    st.subheader("🏢 Company Information")
    info, err = fetch_company_info_cached(ticker)
    if err:
        st.warning(err)
        return
    if not info:
        st.warning("No company information available.")
        return
    st.write(f"**Name:** {info.get('longName')}")
    st.write(f"**Sector:** {info.get('sector')}")
    st.write(f"**Industry:** {info.get('industry')}")
    st.write(f"**Market Cap:** {human_format(info.get('marketCap'))}")
    st.write(f"**Trailing P/E:** {info.get('trailingPE')}")
    st.write(f"**Forward P/E:** {info.get('forwardPE')}")
    st.write(f"**Employees:** {info.get('fullTimeEmployees')}")
    st.write(f"**Country:** {info.get('country')}")
    st.write(f"**Website:** {info.get('website')}")
    summary = info.get('longBusinessSummary', "N/A")
    st.markdown("**Business Summary**")
    if summary and summary != "N/A":
        if len(summary) > 1000:
            st.write(summary[:1000] + "...")
            with st.expander("Read full business summary"):
                st.write(summary)
        else:
            st.write(summary)
    else:
        st.write("N/A")

# --- News Feed ---
@st.cache_data(ttl=1800)
def fetch_news_cached(ticker):
    try:
        tk = yf.Ticker(ticker)
        news = tk.news
        return news if news else []
    except Exception:
        return []

def show_news(ticker):
    st.markdown("### 📰 News Feed")
    news_items = fetch_news_cached(ticker)
    if not news_items:
        st.info("No news available for this ticker.")
        return
    for item in news_items[:5]:  # show top 5
        st.write(f"**{item.get('title','No Title')}**")
        ts = item.get('providerPublishTime')
        try:
            published = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M UTC") if ts else "N/A"
        except Exception:
            published = "N/A"
        st.write(f"Source: {item.get('publisher','Unknown')} | Published: {published}")
        st.markdown(f"[Read more]({item.get('link','')})")
        st.markdown("---")

# --- Watchlist ---
def show_watchlist(watchlist, start_date, end_date):
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

# --- Integrate into Main Execution ---
for ticker in [t.strip().upper() for t in tickers.split(",")]:
    data, err = fetch_data_cached(ticker, start_date, end_date)
    if err:
        st.warning(err)
        continue
    if data.empty:
        st.warning(f"No data for {ticker}.")
        continue
    data = calculate_indicators(data)
    data = calculate_ma(data, ma_type, ma_window)
    ma_kind_for_crossover = "SMA" if ma_type == "SMA" else "EMA"
    data, crossover_info = calculate_crossovers(data, short_window, long_window, ma_kind=ma_kind_for_crossover)
    plot_stock_with_features(data, ticker, ma_type, ma_window, short_window, long_window)
    st.markdown("### 🔔 Moving Average Crossover Signals")
    signal = crossover_info.get("signal", "N/A")
    reason = crossover_info.get("reason", "")
    last_date = crossover_info.get("last_date", None)
    if last_date is not None:
        days_since = (pd.Timestamp(date.today()) - pd.Timestamp(last_date.date())).days
        reason = f"{reason} (Last crossover: {last_date.date()}, {days_since} days ago.)"
    if signal == "BUY":
        st.success(f"BUY — {reason}")
    elif signal == "SELL":
        st.error(f"SELL — {reason}")
    else:
        st.info(f"{signal} — {reason}")
    st.markdown("#### Quick 50/200 Check")
    st.write(detect_50_200_crossover(data))
    show_company_info_cached(ticker)
    if enable_news:
        show_news(ticker)
    st.markdown("---")

# --- Watchlist display ---
watchlist = [t.strip().upper() for t in watchlist_input.split(",") if t.strip()]
if watchlist:
    show_watchlist(watchlist, start_date, end_date)
