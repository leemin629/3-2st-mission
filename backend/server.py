from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
from dotenv import load_dotenv

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

@app.get("/stock/{symbol}")
def get_stock(symbol: str):
    # 🧪 [개발용] 더미 데이터 - API 한도 아낄 때 사용
    return {
        "Global Quote": {
            "01. symbol": symbol,
            "05. price": "138.50",
            "09. change": "-2.30",
            "10. change percent": "-1.63%"
        }
    }

    # ✅ [실제용] 내일 켤 때 위 return 삭제하면 됨
    # url = "https://www.alphavantage.co/query"
    # params = {
    #     "function": "GLOBAL_QUOTE",
    #     "symbol": symbol,
    #     "apikey": API_KEY
    # }
    # response = requests.get(url, params=params)
    # return response.json()