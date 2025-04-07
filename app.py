
import streamlit as st
import openai
import pandas as pd
import numpy as np
import yfinance as yf
import talib as ta

# Load your secrets
openai.api_key = st.secrets["openai_api_key"]

# Set the title and description of the app
st.title("Beast Trader - AI + Telegram Breakout Screener")
st.markdown("Analyze stocks and get trade suggestions based on technical and fundamental data!")

# Function to fetch historical stock data from Yahoo Finance
def get_data(symbol, start_date, end_date):
    data = yf.download(symbol, start=start_date, end=end_date)
    return data

# Function to generate trade suggestions based on AI and sentiment
def get_chatgpt_response(query):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=query,
        temperature=0.7,
        max_tokens=150
    )
    return response.choices[0].text.strip()

# Implement your backtesting logic here
def backtest_strategy(data):
    # Example: Moving average crossover strategy
    data['SMA50'] = ta.SMA(data['Close'], timeperiod=50)
    data['SMA200'] = ta.SMA(data['Close'], timeperiod=200)
    data['Signal'] = np.where(data['SMA50'] > data['SMA200'], 1, 0)
    data['Returns'] = data['Close'].pct_change() * data['Signal'].shift(1)
    return data

# Function to get stock signals and technical indicators
def analyze_stock(symbol):
    data = get_data(symbol, '2020-01-01', '2025-01-01')
    backtested_data = backtest_strategy(data)
    st.write("Stock Analysis:")
    st.line_chart(backtested_data[['Close', 'SMA50', 'SMA200']])

    # Using ChatGPT to generate insights for the stock
    chatgpt_query = f"Analyze the stock {symbol} for breakout potential using technical indicators and market conditions."
    trade_suggestion = get_chatgpt_response(chatgpt_query)
    st.write(f"AI Trade Suggestion: {trade_suggestion}")

# Main code to run the app
if __name__ == "__main__":
    sector = st.selectbox("Select Sector", ['Nifty 50', 'Banks', 'IT', 'Auto'])
    stock_symbol = st.text_input("Enter Stock Symbol", value="NIFTYBEES")
    
    if stock_symbol:
        analyze_stock(stock_symbol)
    else:
        st.write("Please enter a valid stock symbol.")
