# services/stock_service.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

def fetch_stock(symbol: str):
    """Alpha Vantage에서 주가 데이터를 가져온다"""
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": API_KEY
    }
    response = requests.get(url, params=params)
    return response.json()

# ⬇️ 여기에 더미 함수 추가!
def get_stock_data(symbol: str):
    """더미 데이터 (지금 사용)"""
    return {
        "Global Quote": {
            "01. symbol": symbol,
            "05. price": "138.50",
            "09. change": "-2.30",
            "10. change percent": "-1.63%"
        }
    }