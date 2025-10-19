import streamlit as st
import pandas as pd
import yfinance as yf
import mplfinance as mpf
from datetime import datetime, timedelta
import io
import matplotlib.pyplot as plt
from stock_symbols import nifty_50, nifty_100, nifty_200, nifty_500, nifty_defense_stocks

def calculate_brick_size(current_price):
    return current_price * 0.01  # 1%

def fetch_and_plot_renko(ticker):
    try:
        # Last 6 months
        end_date = datetime.today()
        start_date = end_date - timedelta(days=6*30)
        
        # Download historical data
        data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)
        
        if data.empty:
            return None, f"No data for {ticker}"
        
        # Flatten multi-index columns if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[0] for col in data.columns]
        
        # Keep only OHLC
        ohlc_cols = ["Open", "High", "Low", "Close"]
        data = data[[col for col in ohlc_cols if col in data.columns]]
        
        # Convert to numeric and drop invalid rows
        data = data.apply(pd.to_numeric, errors="coerce").dropna()
        
        # Skip if insufficient data
        if data.empty or len(data) < 10:
            return None, f"Not enough valid data for {ticker}"
        
        current_price = float(data["Close"].iloc[-1])
        brick_size = calculate_brick_size(current_price)
        
        # Create a figure for the Renko chart
        fig, ax = mpf.plot(
            data,
            type="renko",
            renko_params=dict(brick_size=brick_size),
            style="charles",
            title=f"{ticker} Renko Chart",
            returnfig=True
        )
        
        # Save plot to bytes buffer
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        plt.close(fig)
        
        return buf, None
    except Exception as e:
        return None, f"Error for {ticker}: {str(e)}"

# Streamlit app
st.title("Stock Chart")

# Checkboxes for Nifty index selection
st.header("Select Nifty Index")
col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    all_checked = st.checkbox("All")
with col2:
    nifty_50_checked = st.checkbox("Nifty50", value=all_checked)
with col3:
    nifty_100_checked = st.checkbox("Nifty100", value=all_checked)
with col4:
    nifty_200_checked = st.checkbox("Nifty200", value=all_checked)
with col5:
    nifty_500_checked = st.checkbox("Nifty500", value=all_checked)
with col6:
    nifty_defense_checked = st.checkbox("Nifty Defense", value=all_checked)

# Check if any index is selected
index_selected = nifty_50_checked or nifty_100_checked or nifty_200_checked or nifty_500_checked or nifty_defense_checked or all_checked

# Combine stocks from selected indices
available_stocks = set()
if all_checked or nifty_50_checked:
    available_stocks.update(nifty_50)
if all_checked or nifty_100_checked:
    available_stocks.update(nifty_100)
if all_checked or nifty_200_checked:
    available_stocks.update(nifty_200)
if all_checked or nifty_500_checked:
    available_stocks.update(nifty_500)
if all_checked or nifty_defense_checked:
    available_stocks.update(nifty_defense_stocks)

# Google-like search bar with autocomplete
st.markdown("""
    <style>
        .search-bar {
            display: flex;
            justify-content: center;
            margin: 20px 0;
        }
        .search-bar input {
            width: 60%;
            padding: 10px;
            font-size: 16px;
            border: 1px solid #ccc;
            border-radius: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            outline: none;
        }
        .search-bar input:focus {
            border-color: #007bff;
            box-shadow: 0 0 5px rgba(0,123,255,0.5);
        }
        .suggestions {
            width: 60%;
            margin: 0 auto;
            border: 1px solid #ccc;
            border-radius: 4px;
            max-height: 200px;
            overflow-y: auto;
            background-color: white;
            position: relative;
            z-index: 1000;
        }
        .suggestion-item {
            padding: 10px;
            cursor: pointer;
        }
        .suggestion-item:hover {
            background-color: #f0f0f0;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for search term
if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = ""

# Search bar
search_term = st.text_input(
    "Search for a stock (e.g., BEL)",
    value=st.session_state.selected_stock,
    key="search_input",
    label_visibility="collapsed"
)

# Normalize search term
search_term = search_term.strip().upper()
if search_term and not search_term.endswith(".NS"):
    search_term = f"{search_term}.NS"

# Autocomplete suggestions for selected indices
if index_selected and search_term:
    suggestions = [stock for stock in available_stocks if search_term.split(".NS")[0].lower() in stock.lower()]
    if suggestions:
        st.markdown('<div class="suggestions">', unsafe_allow_html=True)
        for suggestion in sorted(suggestions):  # Sort for consistent display
            if st.button(suggestion, key=f"suggestion_{suggestion}"):
                st.session_state.selected_stock = suggestion
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# Display chart if a stock is entered or selected
if search_term or st.session_state.selected_stock:
    stock_to_plot = st.session_state.selected_stock if st.session_state.selected_stock else search_term
    # If no index is selected, allow any stock; otherwise, validate against selected indices
    if index_selected and stock_to_plot not in available_stocks:
        st.error(f"Please select a valid stock from the selected indices.")
    else:
        # Determine which indices the stock belongs to
        indices = []
        if stock_to_plot in nifty_50:
            indices.append("Nifty 50")
        if stock_to_plot in nifty_100:
            indices.append("Nifty 100")
        if stock_to_plot in nifty_200:
            indices.append("Nifty 200")
        if stock_to_plot in nifty_500:
            indices.append("Nifty 500")
        if stock_to_plot in nifty_defense_stocks:
            indices.append("Nifty Defense")
        
        # Display the indices the stock is tagged in
        if indices:
            st.write(f"Stock {stock_to_plot} is tagged in: {', '.join(indices)}")
        else:
            st.write(f"Stock {stock_to_plot} is not tagged in any predefined indices.")
        
        # Plot the Renko chart
        st.subheader(f"Renko Chart for {stock_to_plot}")
        chart, error = fetch_and_plot_renko(stock_to_plot)
        
        if chart:
            st.image(chart, use_container_width=True)
        else:
            st.error(error)
