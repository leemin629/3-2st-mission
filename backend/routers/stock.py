# routers/stock.py
from fastapi import APIRouter
from services.stock_service import fetch_stock  # 주방 함수 불러오기

router = APIRouter()  # app 대신 router 사용!

@router.get("/stock/{symbol}")
def get_stock(symbol: str):
    return fetch_stock(symbol)  # 주방에 요리 시키기