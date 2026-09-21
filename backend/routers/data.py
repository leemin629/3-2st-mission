from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from firebase_config import db
from validation_utils import clean_text, validate_symbol, validate_price, validate_date

router = APIRouter()


# ===== Pydantic 검증 모델 =====
class DataItem(BaseModel):
    symbol: str = "NVDA"
    date: str
    value: float
    memo: str = ""


def sanitize_data_item(item: DataItem) -> dict:
    """
    데이터 추가/수정 전에 입력값을 검증하고 정리합니다.
    """
    return {
        "symbol": validate_symbol(item.symbol),
        "date": validate_date(item.date),
        "value": validate_price(item.value),
        "memo": clean_text(item.memo, 200, "메모")
    }


# ===== 데이터 요약 =====
@router.get("/summary")
async def get_summary(symbol: str = Query("NVDA")):
    symbol = validate_symbol(symbol)

    docs = db.collection("data") \
        .where("symbol", "==", symbol) \
        .stream()

    prices = []
    records = []

    for doc in docs:
        d = doc.to_dict()
        prices.append(d["value"])
        records.append({
            "date": d["date"],
            "value": d["value"]
        })

    if not prices:
        return {"error": f"{symbol} 데이터가 없습니다."}

    avg_price = sum(prices) / len(prices)
    high_price = max(prices)
    low_price = min(prices)

    records.sort(key=lambda x: x["date"])

    oldest = records[0]["value"]
    latest = records[-1]["value"]

    change_percent = ((latest - oldest) / oldest) * 100 if oldest != 0 else 0

    if change_percent > 0:
        trend = "상승"
    elif change_percent < 0:
        trend = "하락"
    else:
        trend = "보합"

    return {
        "symbol": symbol,
        "count": len(prices),
        "current_price": round(latest, 2),
        "average_price": round(avg_price, 2),
        "high_price": round(high_price, 2),
        "low_price": round(low_price, 2),
        "change_percent": round(change_percent, 2),
        "trend": trend
    }


# ===== 차트용 데이터 =====
@router.get("/history")
async def get_history(symbol: str = Query("NVDA")):
    symbol = validate_symbol(symbol)

    docs = db.collection("data") \
        .where("symbol", "==", symbol) \
        .stream()

    records = []

    for doc in docs:
        d = doc.to_dict()
        records.append({
            "date": d["date"],
            "value": d["value"]
        })

    if not records:
        return {"error": f"{symbol} 데이터가 없습니다."}

    records.sort(key=lambda x: x["date"])

    dates = [r["date"] for r in records]
    prices = [r["value"] for r in records]

    return {
        "symbol": symbol,
        "dates": dates,
        "prices": prices
    }


# ===== CRUD =====

# 1. POST /api/data - 새 데이터 추가
@router.post("")
async def create_data(item: DataItem):
    safe_item = sanitize_data_item(item)

    ref = db.collection("data").add(safe_item)

    return {
        "id": ref[1].id,
        **safe_item
    }


# 2. GET /api/data - 목록 조회
@router.get("")
async def list_data(symbol: str = Query(None)):
    query = db.collection("data")

    if symbol:
        symbol = validate_symbol(symbol)
        query = query.where("symbol", "==", symbol)

    docs = query.stream()

    result = [
        {
            "id": doc.id,
            **doc.to_dict()
        }
        for doc in docs
    ]

    result.sort(key=lambda x: x["date"], reverse=True)

    return result


# 3. PUT /api/data/{id} - 수정
@router.put("/{item_id}")
async def update_data(item_id: str, item: DataItem):
    doc_ref = db.collection("data").document(item_id)

    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="데이터를 찾을 수 없습니다")

    safe_item = sanitize_data_item(item)

    doc_ref.update(safe_item)

    return {
        "id": item_id,
        **safe_item
    }


# 4. DELETE /api/data/{id} - 삭제
@router.delete("/{item_id}")
async def delete_data(item_id: str):
    doc_ref = db.collection("data").document(item_id)

    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="데이터를 찾을 수 없습니다")

    doc_ref.delete()

    return {
        "message": "삭제 완료",
        "id": item_id
    }