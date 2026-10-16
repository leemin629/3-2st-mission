"""데이터 행에 연결한 목표가 조건을 갱신된 일별 종가로 한 번 확인합니다."""
from uuid import uuid4
from firebase_admin import firestore


def alert_settings(direction, target, previous=None, rearm=False, symbol=None):
    previous = previous or {}
    changed = (previous.get("alert_direction", "none") != direction
               or previous.get("alert_target") != target
               or previous.get("symbol") != symbol)
    if previous and not changed and not rearm:
        return {}
    return {
        "alert_direction": direction, "alert_target": target,
        "alert_status": "active" if direction != "none" else "off",
        "alert_revision": uuid4().hex,
        "alert_checked_date": None, "alert_triggered_date": None,
        "alert_triggered_price": None, "alert_triggered_at": None,
    }


@firestore.transactional
def _check_one(transaction, ref, symbol, day, price):
    snapshot = ref.get(transaction=transaction)
    if not snapshot.exists:
        return None
    item = snapshot.to_dict()
    if item.get("symbol") != symbol or item.get("alert_status") != "active":
        return None
    if (item.get("alert_checked_date") or "") > day:
        return None
    direction, target = item.get("alert_direction"), item.get("alert_target")
    if direction not in ("above", "below") or not isinstance(target, (float, int)):
        return None
    reached = price >= target if direction == "above" else price <= target
    patch = {"alert_checked_date": day}
    if reached:
        patch.update({"alert_status": "triggered", "alert_triggered_date": day,
                      "alert_triggered_price": price,
                      "alert_triggered_at": firestore.SERVER_TIMESTAMP})
    transaction.update(ref, patch)
    if not reached:
        return None
    return {"id": ref.id, "symbol": symbol, "direction": direction,
            "target": target, "date": day, "price": price}


def evaluate_price_alerts(db, symbol, day, price):
    triggered = []
    docs = db.collection("data").where("symbol", "==", symbol).stream()
    for doc in docs:
        if doc.to_dict().get("alert_status") != "active":
            continue
        result = _check_one(db.transaction(), db.collection("data").document(doc.id), symbol, day, price)
        if result:
            triggered.append(result)
    return triggered
