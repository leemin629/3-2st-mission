from fastapi import FastAPI   
from fastapi.middleware.cors import CORSMiddleware # ← 추가! FastAPI 도구 가져오기
import requests
import os
from dotenv import load_dotenv

app = FastAPI()                # ← 추가! app을 실제로 만들기 🏠

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # 모든 곳에서의 요청 허용
    allow_methods=["*"],      # 모든 방식 허용
    allow_headers=["*"],
)

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