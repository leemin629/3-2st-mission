from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from firebase_config import db
from validation_utils import clean_text, validate_symbol, validate_price, validate_date
from datetime import datetime, timedelta
from typing import Optional, Literal
from firebase_admin import firestore
from services.price_alert_service import alert_settings
from services.stock_data_service import read_records, summarize_records, WINDOW_LIMIT

router = APIRouter()


# ===== Pydantic 검증 모델 =====
class DataItem(BaseModel):
    symbol: str = "NVDA"
    date: str
    value: float
    memo: str = ""
    alert_direction: Literal["none", "above", "below"] = "none"
    alert_target: Optional[float] = None
    rearm_alert: bool = False


def sanitize_data_item(item: DataItem) -> dict:
    """
    데이터 추가/수정 전에 입력값을 검증하고 정리합니다.
    """
    target = validate_price(item.alert_target) if item.alert_direction != "none" else None
    return {
        "alert_direction": item.alert_direction, "alert_target": target,
        "symbol": validate_symbol(item.symbol),
        "date": validate_date(item.date),
        "value": validate_price(item.value),
        "memo": clean_text(item.memo, 200, "메모")
    }


# ===== 데이터 요약 =====
@router.get("/summary")
async def get_summary(
    symbol: str = Query("NVDA"),
    period: Optional[int] = Query(
        None,
        ge=1,
        le=3650,
        description="최근 N일 기준으로 요약합니다. 예: 7, 30, 90"
    )
):
    """최근 100개 자료 기준. period는 그 범위 안에서 마지막 저장일 기준 N일을 선택합니다."""
    symbol = validate_symbol(symbol)
    records = read_records(symbol)
    if period is not None and records:
        latest = datetime.strptime(records[0]["date"], "%Y-%m-%d").date()
        start = (latest - timedelta(days=period - 1)).isoformat()
        records = [row for row in records if row["date"] >= start]
    summary = summarize_records(records)
    if not summary:
        return {"symbol": symbol, "count": 0, "window_limit": WINDOW_LIMIT,
                "message": f"{symbol} 데이터가 없습니다."}
    return {"symbol": symbol, "period": period,
            "summary 기준": "최근 100개 자료" if period is None else f"최근 100개 중 최근 {period}일",
            **summary}



# ===== 차트용 데이터 =====
@router.get("/history")
async def get_history(symbol: str = Query("NVDA")):
    symbol = validate_symbol(symbol)
    records = list(reversed(read_records(symbol)))
    return {"symbol": symbol, "window_limit": WINDOW_LIMIT,
            "dates": [row["date"] for row in records],
            "prices": [row["value"] for row in records]}



# 전체 종목의 목표가 도달 기록 (새로고침 후에도 확인 가능)
@router.get("/alerts")
def list_price_alerts():
    docs = db.collection("data").where("alert_status", "==", "triggered").stream()
    result = [{"id": doc.id, **doc.to_dict()} for doc in docs]
    result.sort(key=lambda item: str(item.get("alert_triggered_at") or ""), reverse=True)
    return result


# ===== CRUD =====

# 1. POST /api/data - 새 데이터 추가
@router.post("")
async def create_data(item: DataItem):
    safe_item = sanitize_data_item(item)

    safe_item.update(alert_settings(item.alert_direction, safe_item["alert_target"], symbol=safe_item["symbol"]))
    ref = db.collection("data").add(safe_item)

    return {
        "id": ref[1].id,
        **safe_item
    }


# 2. GET /api/data - 목록 조회
@router.get("")
async def list_data(symbol: str = Query(None), view: Literal["recent", "alerts"] = Query("recent")):
    if symbol:
        symbol = validate_symbol(symbol)
    # 오래된 자료의 활성/완료 알림은 별도 목록에서 계속 편집할 수 있습니다.
    return read_records(symbol, alerts_only=(view == "alerts"))



# 3. PUT /api/data/{id} - 수정
@router.put("/{item_id}")
async def update_data(item_id: str, item: DataItem):
    safe_item = sanitize_data_item(item)
    doc_ref = db.collection("data").document(item_id)

    @firestore.transactional
    def save(transaction):
        snapshot = doc_ref.get(transaction=transaction)
        if not snapshot.exists:
            raise HTTPException(status_code=404, detail="데이터를 찾을 수 없습니다")
        patch = dict(safe_item)
        patch.update(alert_settings(item.alert_direction, safe_item["alert_target"],
                                    snapshot.to_dict(), item.rearm_alert, safe_item["symbol"]))
        transaction.update(doc_ref, patch)
        return patch

    patch = save(db.transaction())
    return {"id": item_id, **patch}



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