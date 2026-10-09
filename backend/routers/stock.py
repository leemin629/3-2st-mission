from fastapi import APIRouter, HTTPException
from services.stock_service import fetch_stock, fetch_market
from firebase_config import db
from validation_utils import validate_symbol, validate_date, validate_price

router = APIRouter()

@router.post("/{symbol}/sync")
def sync_stock(symbol: str):
    symbol = validate_symbol(symbol)
    payload = fetch_market(symbol, "TIME_SERIES_DAILY")
    series = payload.get("Time Series (Daily)")
    if not series:
        raise HTTPException(502, "일별 주가 데이터가 없습니다. 기존 데이터는 유지됩니다.")
    try:
        records = [(validate_date(day), validate_price(values["4. close"]))
                   for day, values in series.items()]
    except (KeyError, TypeError, HTTPException):
        raise HTTPException(502, "주가 응답 형식이 올바르지 않습니다.")
    # 기존 수동 입력/메모를 덮어쓰지 않고 없는 거래일만 추가합니다.
    existing = {doc.to_dict().get("date") for doc in
                db.collection("data").where("symbol", "==", symbol).stream()}
    added = 0
    for day, price in records:
        if day in existing:
            continue
        ref = db.collection("data").document(f"{symbol}_{day}")
        try:
            ref.create({"symbol": symbol, "date": day, "value": price,
                        "memo": f"{symbol} Close", "source": "Alpha Vantage"})
        except Exception as exc:
            if type(exc).__name__ != "AlreadyExists":
                raise HTTPException(503, "일부 데이터 저장에 실패했습니다. 다시 갱신해 주세요.")
            continue
        added += 1
    return {"symbol": symbol, "added": added, "latest_date": max(day for day, _ in records)}

@router.get("/{symbol}")
def read_stock(symbol: str):
    symbol = validate_symbol(symbol)
    payload = fetch_stock(symbol)
    if not payload.get("Global Quote"):
        raise HTTPException(502, "시세 데이터가 없습니다.")
    return payload
