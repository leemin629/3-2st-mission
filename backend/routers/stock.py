# routers/stock.py
from fastapi import APIRouter
# 🔥 두 함수 모두 import!
from services.stock_service import fetch_stock, get_stock_data
from firebase_config import db
from datetime import datetime

router = APIRouter()


@router.get("/stock/{symbol}")
def read_stock(symbol: str):   # ✅ 라우터 함수 이름 변경 (겹침 방지!)
    # 1. 실제 API 호출 시도
    data = fetch_stock(symbol)

    # 2. API 제한 감지 시 → 더미 데이터로 대체
    if "Information" in data or "Note" in data:
        print("⚠️ API 제한! 더미 데이터 사용")
        data = get_stock_data(symbol)   # ✅ 더미 함수 호출!

    # 3. Firestore에 저장
    db.collection("stocks").add({
        "symbol": symbol,
        "data": data,
        "created_at": datetime.now()
    })

    return data