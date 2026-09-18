from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from firebase_config import db

router = APIRouter()


# ===== Pydantic 검증 모델 =====
class DataItem(BaseModel):
    symbol: str = "NVDA"   # ← 이 줄 추가!
    date: str          # 예: "2024-01-15"
    value: float       # 숫자만 허용
    memo: str = ""     # 선택 항목


# ===== 데이터 요약 =====
@router.get("/summary")
async def get_summary(symbol: str = Query("NVDA")):
    # 허용된 종목만 통과 (안전장치)
    allowed = ["NVDA", "AAPL", "TSLA", "MSFT", "GOOGL"]
    if symbol not in allowed:
        raise HTTPException(status_code=400, detail="지원하지 않는 종목입니다")

    # 요청받은 종목으로 조회
    docs = db.collection("data")\
        .where("symbol", "==", symbol)\
        .stream()

    prices = []
    records = []
    for doc in docs:
        d = doc.to_dict()
        prices.append(d["value"])
        records.append({"date": d["date"], "value": d["value"]})

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


# ===== 📈 차트용 데이터 (날짜별 가격 목록) =====
@router.get("/history")
async def get_history(symbol: str = Query("NVDA")):
    # 허용된 종목만 통과 (안전장치)
    allowed = ["NVDA", "AAPL", "TSLA", "MSFT", "GOOGL"]
    if symbol not in allowed:
        raise HTTPException(status_code=400, detail="지원하지 않는 종목입니다")

    # 해당 종목 데이터 조회
    docs = db.collection("data")\
        .where("symbol", "==", symbol)\
        .stream()

    records = []
    for doc in docs:
        d = doc.to_dict()
        records.append({"date": d["date"], "value": d["value"]})

    if not records:
        return {"error": f"{symbol} 데이터가 없습니다."}

    # 날짜순 정렬 (오래된 것 → 최신)
    records.sort(key=lambda x: x["date"])

    # 차트용으로 분리
    dates = [r["date"] for r in records]
    prices = [r["value"] for r in records]

    return {
        "symbol": symbol,
        "dates": dates,      # ["2024-01-15", ...]
        "prices": prices     # [210.5, 212.3, ...]
    }


# ===== CRUD 4개 =====

# 1️⃣ POST /api/data - 새 데이터 추가
@router.post("")
async def create_data(item: DataItem):
    ref = db.collection("data").add(item.dict())
    return {"id": ref[1].id, **item.dict()}


# 2️⃣ GET /api/data - 목록 조회 (종목 필터 추가!)
@router.get("")
async def list_data(symbol: str = Query(None)):   # 🎯 symbol 파라미터 추가!
    query = db.collection("data")
    
    # 🎯 종목이 있으면 필터링! (없으면 전체)
    if symbol:
        query = query.where("symbol", "==", symbol)
    
    docs = query.stream()
    result = [{"id": doc.id, **doc.to_dict()} for doc in docs]
    
    # 🎯 날짜 최신순 정렬! (보기 좋게)
    result.sort(key=lambda x: x["date"], reverse=True)
    
    return result

# 3️⃣ PUT /api/data/{id} - 수정
@router.put("/{item_id}")
async def update_data(item_id: str, item: DataItem):
    doc_ref = db.collection("data").document(item_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="데이터를 찾을 수 없습니다")
    doc_ref.update(item.dict())
    return {"id": item_id, **item.dict()}


# 4️⃣ DELETE /api/data/{id} - 삭제
@router.delete("/{item_id}")
async def delete_data(item_id: str):
    doc_ref = db.collection("data").document(item_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="데이터를 찾을 수 없습니다")
    doc_ref.delete()
    return {"message": "삭제 완료", "id": item_id}