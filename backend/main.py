from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from fastapi import HTTPException
from validation_utils import validate_symbol
import logging
import google.generativeai as genai
import os
import uvicorn
from dotenv import load_dotenv
from firebase_config import db
from firebase_admin import firestore
from routers import stock, data, conversations   # conversations 추가

# 환경변수 로드
load_dotenv()
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 경로 설정 (배포용 절대경로)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

app = FastAPI(title="Stock Insight AI")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://three-2st-mission.onrender.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(stock.router, prefix="/api/stocks", tags=["stocks"])
app.include_router(data.router, prefix="/api/data", tags=["data"])   # ← 이 줄 추가!
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
# 🤖 Gemini 설정
genai.configure(api_key=GEMINI_API_KEY)

# 📩 요청 데이터 형식 정의
class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    symbol: str = "NVDA"

# 사용할 모델 목록 (폴백용)
# 백엔드 main.py 수정
# 환경변수에 모델을 지정하거나 계정에서 실제 사용 가능한 모델을 조회합니다.
def available_models():
    configured = os.getenv("GEMINI_MODELS", "")
    if configured.strip():
        return [name.strip() for name in configured.split(",") if name.strip()]
    candidates = [m.name for m in genai.list_models()
                  if "generateContent" in m.supported_generation_methods
                  and any(kind in m.name for kind in ("flash", "pro"))
                  and not any(kind in m.name for kind in ("image", "audio", "tts", "live"))]
    candidates.sort(key=lambda name: ("flash" not in name, "lite" not in name, name))
    return candidates[:3]


# 📊 Firestore에서 요약 통계 계산
def get_stock_summary(symbol="NVDA"):
    docs = db.collection("data").where("symbol", "==", symbol).stream()
    records = []
    for doc in docs:
        d = doc.to_dict()
        records.append({"date": d["date"], "value": d["value"]})

    if not records:
        return None

    prices = [r["value"] for r in records]
    records.sort(key=lambda x: x["date"])

    oldest = records[0]["value"]
    latest = records[-1]["value"]
    change_percent = (latest - oldest) / oldest * 100 if oldest else 0
    trend = "상승" if change_percent > 0 else "하락" if change_percent < 0 else "보합"

    return {
        "start_date": records[0]["date"],
        "end_date": records[-1]["date"],
        "count": len(records),
        "current": round(latest, 2),
        "average": round(sum(prices) / len(prices), 2),
        "high": round(max(prices), 2),
        "low": round(min(prices), 2),
        "change_percent": round(change_percent, 2),
        "trend": trend
    }

# 질문에 명시한 종목들을 함께 요약합니다.
def select_chat_symbols(message, fallback):
    symbol_map = {
        "NVDA": ["NVDA", "엔비디아", "NVIDIA"],
        "AAPL": ["AAPL", "애플", "APPLE"],
        "TSLA": ["TSLA", "테슬라", "TESLA"],
        "MSFT": ["MSFT", "마이크로소프트", "MICROSOFT"],
        "GOOGL": ["GOOGL", "구글", "GOOGLE", "알파벳"],
    }
    upper = message.upper()
    compact = "".join(upper.split())
    all_markers = ("5개", "다섯", "전체종목", "모든종목", "전종목", "ALLSTOCKS", "ALLFIVE")
    if any(marker in compact for marker in all_markers):
        return list(symbol_map)
    found = [symbol for symbol, keywords in symbol_map.items()
             if any(keyword.upper() in upper for keyword in keywords)]
    return found or list(symbol_map)


def build_chat_context(symbols):
    sections = []
    for symbol in symbols:
        summary = get_stock_summary(symbol)
        if not summary:
            sections.append(f"[{symbol}] 저장 데이터가 없습니다. 가격을 추측하지 마세요.")
            continue
        sections.append(f"""[{symbol} 저장 데이터 {summary['start_date']} ~ {summary['end_date']} ({summary['count']}개)]
- 마지막 저장 가격: ${summary['current']}
- 평균가: ${summary['average']}
- 최고 저장 가격: ${summary['high']}
- 최저 저장 가격: ${summary['low']}
- 저장 기간 첫 가격 대비 등락률: {summary['change_percent']}%
- 추세: {summary['trend']}""")
    return "\n\n".join(sections)


# 💬 채팅 엔드포인트
@app.post("/chat")
def chat(req: ChatRequest):
    req.message = req.message.strip()
    if not req.message:
        raise HTTPException(400, "메시지를 입력해 주세요.")
    req.symbol = validate_symbol(req.symbol)
    symbols = select_chat_symbols(req.message, req.symbol)
    selected = ", ".join(symbols)
    data_context = build_chat_context(symbols)
    system_prompt = f"""너는 저장된 미국 주가 자료를 설명하는 도우미입니다.
항상 정중한 한국어로 간결하게 답변하세요.
1. 요청 대상은 {selected}입니다. 여러 종목이면 제공된 모든 대상 종목을 설명하세요.
2. 가격과 통계는 아래 저장 데이터에 근거하고, 데이터가 없는 종목은 없다고 표시하세요.
3. 저장 종가를 장중 실시간 시세로 표현하지 마세요. 기준일과 기간을 확인하세요.
4. 종목별 기간이 다르면 비교의 기간 차이를 밝혀 주세요.
5. 최신 뉴스나 수집하지 않은 가격·원인을 추측하지 마세요. 일반 설명은 저장 데이터와 구분하세요.
6. 소제목은 '## 제목', 강조는 **강조** 마크다운을 사용하세요.

{data_context}

사용자 질문: """

    try:
        models = available_models()
    except Exception:
        raise HTTPException(503, "AI 모델 목록을 확인하지 못했습니다. API 키 또는 GEMINI_MODELS 설정을 확인해 주세요.")

    for model_name in models:
        try:
            model = genai.GenerativeModel(model_name)
            full_prompt = system_prompt + req.message
            response = model.generate_content(full_prompt, request_options={"timeout": 30})
            reply = response.text

            try:
                db.collection("chat_history").add({
                    "message": req.message, "reply": reply, "model": model_name,
                    "symbol": selected, "symbols": symbols, "created_at": firestore.SERVER_TIMESTAMP
                })
                saved = True
            except Exception:
                logging.exception("대화 저장 실패")
                saved = False

            return {"reply": reply, "model": model_name, "symbol": selected, "symbols": symbols, "saved": saved}
        except Exception as e:
            print(f"{model_name} 실패: {e}")
            continue
    raise HTTPException(503, "AI가 응답하지 못했습니다. API 키, 모델 설정 또는 호출 한도를 확인해 주세요.")

# 📜 채팅 기록 불러오기 엔드포인트
@app.get("/chat/history")
async def get_chat_history():
    records = conversations.read_records()
    records.reverse()
    for record in records:
        created = record.get("created_at")
        record["time"] = created.astimezone().strftime("%H:%M") if created else ""
    return {"history": records}

# 🎯 프론트엔드 연결 (반드시 맨 아래!)
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

# 🚀 서버 실행 (파일 맨 마지막!)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)