from fastapi import FastAPI    # ← 추가! FastAPI 도구 가져오기
import requests
import os
from dotenv import load_dotenv

app = FastAPI()                # ← 추가! app을 실제로 만들기 🏠

load_dotenv()
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

@app.get("/stock/{symbol}")    # ← 이제 app이 있으니까 작동! ✅
def get_stock(symbol: str):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": API_KEY
    }
    response = requests.get(url, params=params)
    return response.json()