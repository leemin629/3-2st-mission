"""화면과 AI가 공유하는 최근 100개 일별 자료 및 통계 기준."""
from collections import defaultdict
from firebase_config import db

WINDOW_LIMIT = 100


def read_records(symbol=None, *, alerts_only=False):
    query = db.collection("data")
    if symbol:
        query = query.where("symbol", "==", symbol)
    rows = [{**doc.to_dict(), "id": doc.id} for doc in query.stream()]
    rows.sort(key=lambda row: (row["date"], row["id"]), reverse=True)
    if alerts_only:
        return [row for row in rows if row.get("alert_direction", "none") != "none"]
    counts = defaultdict(int)
    recent = []
    for row in rows:
        key = row.get("symbol", "")
        if counts[key] < WINDOW_LIMIT:
            recent.append(row)
            counts[key] += 1
    return recent


def summarize_records(records):
    if not records:
        return None
    rows = sorted(records, key=lambda row: (row["date"], row["id"]))
    prices = [row["value"] for row in rows]
    first, latest = prices[0], prices[-1]
    change = (latest - first) / first * 100 if first else 0
    return {
        "start_date": rows[0]["date"], "end_date": rows[-1]["date"],
        "count": len(rows), "window_limit": WINDOW_LIMIT,
        "current_price": round(latest, 2),
        "average_price": round(sum(prices) / len(prices), 2),
        "high_price": round(max(prices), 2), "low_price": round(min(prices), 2),
        "change_percent": round(change, 2),
        "trend": "상승" if change > 0 else "하락" if change < 0 else "보합",
    }
