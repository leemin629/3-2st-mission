from fastapi import APIRouter
from firebase_config import db

router = APIRouter()

@router.get("/summary")
async def get_summary():
    # 1️⃣ Firestore에서 100일 데이터 전부 읽기
    docs = db.collection("data").stream()

    prices = []      # 가격만 모을 리스트
    records = []      # 날짜+가격 함께 (추세 계산용)

    for doc in docs:
        d = doc.to_dict()
        prices.append(d["value"])
        records.append({"date": d["date"], "value": d["value"]})

    # 2️⃣ 데이터 없으면 방어
    if not prices:
        return {"error": "데이터가 없습니다. seed_data.py를 실행하세요."}

    # 3️⃣ 통계 계산
    avg_price = sum(prices) / len(prices)
    high_price = max(prices)
    low_price = min(prices)

    # 4️⃣ 추세 계산 (날짜순 정렬 후 첫날 vs 마지막날)
    records.sort(key=lambda x: x["date"])   # 날짜 오름차순
    oldest = records[0]["value"]            # 가장 오래된 날
    latest = records[-1]["value"]           # 가장 최근 날

    change = latest - oldest
    change_percent = (change / oldest) * 100

    if change_percent > 0:
        trend = "상승"
    elif change_percent < 0:
        trend = "하락"
    else:
        trend = "보합"

    # 5️⃣ 결과 반환
    return {
        "symbol": "NVDA",
        "count": len(prices),
        "current_price": round(latest, 2),        # 현재가 = 최근 종가
        "average_price": round(avg_price, 2),
        "high_price": round(high_price, 2),
        "low_price": round(low_price, 2),
        "change_percent": round(change_percent, 2),
        "trend": trend
    }