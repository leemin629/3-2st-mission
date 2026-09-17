import os
import requests
from dotenv import load_dotenv
from firebase_config import db
from firebase_admin import firestore

load_dotenv()
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

SYMBOL = "NVDA"

def fetch_and_save():
    # 1️⃣ Alpha Vantage에서 일별 데이터 요청
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",   # 일별 종가
        "symbol": SYMBOL,
        "outputsize": "compact",           # 최근 100일 (딱 맞음!)
        "apikey": API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()

    # 2️⃣ 에러 체크 (API 한도 초과 등)
    if "Time Series (Daily)" not in data:
        print("❌ 데이터 받기 실패:", data)
        return

    time_series = data["Time Series (Daily)"]
    print(f"✅ {len(time_series)}일치 데이터 받음")

    # 3️⃣ Firestore에 하나씩 저장
    count = 0
    for date, values in time_series.items():
        close_price = float(values["4. close"])   # 종가

        db.collection("data").document(date).set({
            "date": date,
            "value": close_price,
            "memo": "NVDA Close"
        })
        count += 1

    print(f"🎉 Firestore 저장 완료: {count}개")

if __name__ == "__main__":
    fetch_and_save()