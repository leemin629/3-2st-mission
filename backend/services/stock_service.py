import os
import requests
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

def fetch_market(symbol, function):
    key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not key:
        raise HTTPException(503, "ALPHA_VANTAGE_API_KEY 설정이 필요합니다.")
    try:
        response = requests.get("https://www.alphavantage.co/query", params={
            "function": function, "symbol": symbol, "apikey": key,
        }, timeout=20)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        raise HTTPException(502, "주가 제공 서버에 연결하지 못했습니다.")
    if "Information" in data or "Note" in data:
        raise HTTPException(429, "주가 API 호출 한도 또는 이용 권한을 확인해 주세요. 기존 데이터는 유지됩니다.")
    if "Error Message" in data:
        raise HTTPException(502, "주가 제공 서버가 요청을 처리하지 못했습니다.")
    return data

def fetch_stock(symbol):
    return fetch_market(symbol, "GLOBAL_QUOTE")
