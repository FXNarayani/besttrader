import yfinance as yf
import pandas as pd
import ta
import streamlit as st
import plotly.graph_objects as go
import requests
import os

TELEGRAM_TOKEN = "7998270516:AAGDEzMcggj2bzGGLZ09h440fXPkw-NpQmY"
CHAT_ID = "1156008573"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload)
    except:
        pass

def get_stock_data(symbol, period='6mo'):
    data = yf.download(symbol, period=period)
    data.dropna(inplace=True)
    return data

def calculate_indicators(df):
    if df.empty or len(df) < 200:
        return None
    df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_signal'] = macd.macd_signal()
    df['20EMA'] = ta.trend.EMAIndicator(df['Close'], window=20).ema_indicator()
    df['50EMA'] = ta.trend.EMAIndicator(df['Close'], window=50).ema_indicator()
    df['200EMA'] = ta.trend.EMAIndicator(df['Close'], window=200).ema_indicator()
    df['ATR'] = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close'], window=14).average_true_range()
    df['VolumeAvg'] = df['Volume'].rolling(window=20).mean()
    return df

def is_breakout(df):
    latest = df.iloc[-1]
    conditions = [
        latest['Close'] > max(df['Close'][-20:]),
        latest['Volume'] > 1.5 * latest['VolumeAvg'],
        latest['RSI'] > 50 and latest['RSI'] < 70,
        latest['MACD'] > latest['MACD_signal'],
        latest['20EMA'] > latest['50EMA'] > latest['200EMA']
    ]
    return all(conditions)

def is_near_breakout(df):
    latest = df.iloc[-1]
    resistance = max(df['Close'][-20:])
    close = latest['Close']
    rsi = latest['RSI']
    volume = latest['Volume']
    vol_avg = latest['VolumeAvg']
    if (
        0.99 * resistance <= close < resistance and
        55 < rsi < 70 and
        volume >= vol_avg and
        latest['20EMA'] > latest['50EMA'] > latest['200EMA']
    ):
        return {
            "Resistance Zone": round(resistance, 2),
            "Current Price": round(close, 2),
            "RSI": round(rsi, 2),
            "Volume Surge": f"{round(volume / vol_avg, 2)}x",
            "Confidence": "High" if volume > 1.5 * vol_avg else "Medium"
        }
    return None

def plot_candlestick(df, symbol):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    )])
    fig.update_layout(title=f'{symbol} - Candlestick Chart', xaxis_rangeslider_visible=False)
    return fig

def main():
    st.title("🤖 Beast Trader – AI + Telegram Breakout Screener")

    sector_dict = {
        "Nifty 50": ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'ICICIBANK.NS', 'HDFCBANK.NS', 'SBIN.NS', 'LT.NS'],
        "IT": ['TCS.NS', 'INFY.NS'],
        "Banks": ['ICICIBANK.NS', 'HDFCBANK.NS', 'SBIN.NS']
    }

    sector = st.selectbox("📂 Select Sector", list(sector_dict.keys()))
    symbols = sector_dict[sector]

    results = []
    tomorrow_candidates = []

    for symbol in symbols:
        df = get_stock_data(symbol)
        df = calculate_indicators(df)
        if df is None:
            continue

        if is_breakout(df):
            breakout_level = round(max(df['Close'][-20:]), 2)
            buy_zone = f"{breakout_level}-{round(breakout_level * 1.01, 2)}"
            stop_loss = round(breakout_level * 0.98, 2)
            target1 = round(breakout_level * 1.05, 2)
            target2 = round(breakout_level * 1.1, 2)

            message = f"🚀 *Breakout Alert: {symbol}*\n📈 Buy: `{buy_zone}`\n🛡️ SL: `{stop_loss}`\n🎯 Target1: `{target1}`, Target2: `{target2}`\nReason: High volume breakout + RSI + MACD"
            send_telegram_message(message)

            results.append({
                'Stock': symbol,
                'Breakout Level': breakout_level,
                'Buy Zone': buy_zone,
                'Stop-loss': stop_loss,
                'Target 1': target1,
                'Target 2': target2,
                'Confidence': "High",
                'Reason': "Breakout with 1.5x+ volume, RSI 55-70, MACD bullish, EMA stack"
            })

            st.plotly_chart(plot_candlestick(df.tail(60), symbol))

        outlook = is_near_breakout(df)
        if outlook:
            outlook['Stock'] = symbol
            tomorrow_candidates.append(outlook)

    st.subheader("🔥 Today's Breakouts")
    if results:
        st.dataframe(pd.DataFrame(results))
    else:
        st.info("No breakout signals found today. Check again tomorrow!")

    st.subheader("🔮 Potential Breakouts for Tomorrow")
    if tomorrow_candidates:
        st.dataframe(pd.DataFrame(tomorrow_candidates))
    else:
        st.info("No strong setups detected for tomorrow.")

if __name__ == '__main__':
    main()