# 📈 Stock Market Dashboard in Python

An interactive, high-fidelity stock market dashboard built with **Streamlit**, **Plotly**, and **yFinance**.  
This repository tracks the chronological, step-by-step evolution of a production-grade dashboard, showcasing real-time data visualization, technical indicators, custom trading signals, real-time news aggregation, and automated watchlist tracking.

---

## 🚀 Project Overview
This project displays a progression of Streamlit dashboards, each introducing unique functionalities, architectural refactorings, or bug fixes. The final builds allow users to:
- Enter and compare multiple stock tickers side-by-side.
- Select customizable moving average overlays (SMA/EMA) and window sizes.
- Chart high-fidelity candlesticks combined with Bollinger Bands, volume bars, RSI (14-day) oscillators, and MACD indicators (lines + histograms).
- Track golden cross/death cross events using configurable short/long crossover windows.
- Visualize dynamic BUY/SELL signal markers directly mapped on price charts.
- View real-time company metadata profile cards and ticker-related news feeds.
- Monitor active stock watchlists displaying percent changes and trading volumes.
- Enable auto-refresh intervals with live market open/closed indicators.

---

## ✨ Features Breakdown by Version

Here is a roadmap of the version evolution of files included in this repository:

1. **`Base_Final.py` (V1 - Base Dashboard)**: A simple interface to search a single ticker and display daily close price charts with a 50-day SMA overlay and basic average/max/min statistics.
2. **`Ver2.py` (V2 - Multi-Stock Comparison)**: Introduces support for plotting multiple stocks side-by-side on a shared chart and viewing comparison tables of key metrics.
3. **`Ver3_Final.py` (V3 - Technical Indicators)**: Adds technical analysis support with individual charts for Bollinger Bands, RSI (14-day), and MACD. Implements dynamic date defaults (`date.today()`) and handles yfinance column MultiIndex issues.
4. **`Ver4_Final.py` (V4 - Real-Time Updates & Modularization)**: Integrates auto-refresh functionality, candlestick rendering, volume charting, simple buy/sell warning logic, current price metrics, and organizes codebase into modular, reusable functions.
5. **`Ver5_Final.py` (V5 - UI & Metrics Optimization)**: Incorporates unified icons, a live US market status indicator (Open/Closed), a 4-column metrics header, MACD histograms, price-to-Bollinger-Band boundary checks, and input validations.
6. **`Ver6.py` (V6 - Multi-Stock Selection & SMA/EMA controls)**: Sequentially loops over list of tickers, rendering custom SMA/EMA selections and individual chart sets for each stock.
7. **`Ver6_Enhanced.py` (V6 Enhanced - Chart/Data Exports)**: Embeds plotly PNG chart download options (requires `kaleido`) and CSV data table extraction.
8. **`Ver6_Enhanced2.py` (V6 Enhanced 2 - Company Info & Crossovers)**: Appends a basic company profile information widget and a 50/200 SMA crossover checker.
9. **`Ver6_Enhanced2_Corrected.py` (V6 Enhanced 2 - Code Cleanup)**: Resolves logic redundancy by cleaning up duplicate function definitions and fixing the main application run loop.
10. **`Ver6_Enhanced2_Rectified.py` (V6 Enhanced 2 - Configurable Crossovers)**: Adds custom short/long moving average windows in the sidebar, auto-swapping for range protection, caching decorators (`@st.cache_data`) for network queries, and draws triangle indicators (BUY/SELL) on Plotly close price charts.
11. **`Ver6_Enhanced2_RFixed.py` (V6 Enhanced 2 - News & Watchlists)**: Integrates an automated ticker news feed and watchlist summary widgets alongside weekend support.
12. **`Ver6_Enhanced3.py` (V6 Enhanced 3 - Alternate Branch)**: Reverts custom crossover variables to focus exclusively on watchlist summaries and news.
13. **`Ver6_Enhanced3_Corrected.py` (V6 Enhanced 3 - Combined Build)**: A merged version containing both news integration and customizable crossovers (executes with duplicate loop rendering).

---

## 🛠 Installation

### 1. Prerequisites
Ensure you have **Python 3.8+** installed on your system.

### 2. Clone the Repository
```bash
git clone https://github.com/kislay-aidev/Stock-Market-Dashboard.git
cd Stock-Market-Dashboard
```

### 3. Install Dependencies
Install all required libraries using pip:
```bash
pip install streamlit yfinance plotly pandas streamlit-autorefresh kaleido
```
*(Note: `kaleido` is optional and required specifically for exporting plotly graphs as PNG images.)*

---

## 🚀 Usage Instructions

You can run any specific version of the stock dashboard using Streamlit's command-line interface.

To start the dashboard of your choice, run:

```bash
# Run the base version (V1)
streamlit run Base_Final.py

# Run the multi-stock version (V2)
streamlit run Ver2.py

# Run the technical indicators version (V3)
streamlit run Ver3_Final.py

# Run the real-time auto-refresh version (V4)
streamlit run Ver4_Final.py

# Run the enhanced UI version (V5)
streamlit run Ver5_Final.py

# Run the main multi-ticker loop version (V6)
streamlit run Ver6.py

# Run the final production build featuring crossovers, company profile caching, watchlist summary, and news feed:
streamlit run Ver6_Enhanced2_RFixed.py
```

### Navigating the Interface
1. **Sidebar Controls**:
   - **Enter Stock Tickers**: Supply a comma-separated list of symbols (e.g. `AAPL, MSFT, GOOGL`).
   - **Date Selectors**: Choose start and end dates for historical data.
   - **Enable Live Mode**: Toggle auto-refresh interval slider (ranges 10 to 300 seconds).
   - **Moving Average Controls**: Switch between SMA and EMA type and input custom window values.
   - **Crossover Settings**: Configure short/long indicators (e.g., 20 and 50 days) for signal notifications.
   - **Watchlist & News**: Toggle News Feed elements and supply additional tickers for watchlist panels.
2. **Main Panel**:
   - **Metrics Cards**: View real-time ticker prices, daily highs/lows, volumes, and status.
   - **Interactive Charts**: Hover, zoom, and crop charts using Plotly's UI toolbar. Download charts as images instantly.
   - **Download Buttons**: Export historical metrics to local CSV spreadsheets.
