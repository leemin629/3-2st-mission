import os
import requests
import time
from dotenv import load_dotenv
from firebase_config import db

load_dotenv()
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

SYMBOLS = ["NVDA", "AAPL", "TSLA", "MSFT", "GOOGL"]   # ← 여러 종목!


def fetch_and_save(symbol):   # ← symbol 인자로 받음! (소문자!)
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "outputsize": "compact",
        "apikey": API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()

    if "Time Series (Daily)" not in data:
        print(f"❌ {symbol} 실패:", data)
        return

    time_series = data["Time Series (Daily)"]
    print(f"✅ {symbol}: {len(time_series)}일치 받음")

    count = 0
    for date, values in time_series.items():
        close_price = float(values["4. close"])

        doc_id = f"{symbol}_{date}"   # ← 여기서 doc_id 만듦! (중요!)

        db.collection("data").document(doc_id).set({
            "symbol": symbol,
            "date": date,
            "value": close_price,
            "memo": f"{symbol} Close"
        })
        count += 1

    print(f"🎉 {symbol} 저장 완료: {count}개")


if __name__ == "__main__":
    for sym in SYMBOLS:
        fetch_and_save(sym)
        time.sleep(15)
    print("🏁 전체 완료!")