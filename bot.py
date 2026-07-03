import os
from dotenv import load_dotenv
import telebot
import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands
from datetime import datetime, timedelta
import pytz

load_dotenv()

bot = telebot.TeleBot(os.getenv("TELEGRAM_TOKEN"))
pk_tz = pytz.timezone("Asia/Karachi")

high_payout_pairs = ["EURUSD", "GBPUSD", "USDJPY", "EURJPY", "AUDUSD", "USDBDT", "EURGBP"]

def get_1m_signal(asset):
    try:
        data = yf.download(f"{asset}=X", period="1d", interval="1m")
        if len(data) < 80:
            return None
        close = data['Close']
        
        rsi = RSIIndicator(close, 14).rsi().iloc[-1]
        macd_line = MACD(close).macd().iloc[-1]
        macd_sig = MACD(close).macd_signal().iloc[-1]
        bb = BollingerBands(close)
        
        price = close.iloc[-1]
        signal_time = (datetime.now(pk_tz) + timedelta(minutes=1)).strftime("%H:%M")
        
        if rsi < 32 and price <= bb.bollinger_lband().iloc[-1] and macd_line > macd_sig:
            return {"asset": asset, "signal": "🔼 CALL", "time": signal_time, "conf": 85}
        elif rsi > 68 and price >= bb.bollinger_hband().iloc[-1] and macd_line < macd_sig:
            return {"asset": asset, "signal": "🔽 PUT", "time": signal_time, "conf": 84}
        return None
    except:
        return None

@bot.message_handler(commands=['signals'])
def signals(message):
    bot.reply_to(message, "🔍 1m signals scanning...")
    for pair in high_payout_pairs:
        sig = get_1m_signal(pair)
        if sig:
            msg = f"🕒 **{sig['time']}** | **{sig['asset']}** → {sig['signal']} (Conf: {sig['conf']}%) | 1min expiry"
            bot.send_message(message.chat.id, msg)

print("Bot Started...")
bot.infinity_polling()