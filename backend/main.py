from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
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
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(stock.router, prefix="/api/stocks", tags=["stocks"])
app.include_router(data.router, prefix="/api/data", tags=["data"])   # ← 이 줄 추가!
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
# 🤖 Gemini 설정
genai.configure(api_key=GEMINI_API_KEY)

# 📩 요청 데이터 형식 정의
class ChatRequest(BaseModel):
    message: str

# 사용할 모델 목록 (폴백용)
# 백엔드 main.py 수정
MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.7-flash",
    "gemini-3.1-pro-preview"
]

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
    change_percent = (latest - oldest) / oldest * 100
    trend = "상승" if change_percent > 0 else "하락" if change_percent < 0 else "보합"

    return {
        "current": round(latest, 2),
        "average": round(sum(prices) / len(prices), 2),
        "high": round(max(prices), 2),
        "low": round(min(prices), 2),
        "change_percent": round(change_percent, 2),
        "trend": trend
    }

# 💬 채팅 엔드포인트
@app.post("/chat")
async def chat(req: ChatRequest):
    # 🔍 종목별 별명 사전 (한글/영문 다 인식!)
    SYMBOL_MAP = {
        "NVDA":  ["NVDA", "엔비디아", "NVIDIA"],
        "AAPL":  ["AAPL", "애플", "APPLE"],
        "TSLA":  ["TSLA", "테슬라", "TESLA"],
        "MSFT":  ["MSFT", "마이크로소프트", "MICROSOFT"],
        "GOOGL": ["GOOGL", "구글", "GOOGLE", "알파벳"],
    }

    selected = None
    msg_upper = req.message.upper()
    for symbol, keywords in SYMBOL_MAP.items():
        if any(kw.upper() in msg_upper for kw in keywords):
            selected = symbol
            break

    # 종목 있을 때만 데이터 가져오기!
    summary = get_stock_summary(selected) if selected else None

    if selected and summary:
        # ✅ 특정 종목 → 데이터 기반 답변
        data_context = f"""
[{selected} 최근 100일 실제 데이터]
- 현재가: ${summary['current']}
- 평균가: ${summary['average']}
- 최고가: ${summary['high']}
- 최저가: ${summary['low']}
- 변동률: {summary['change_percent']}%
- 추세: {summary['trend']}
"""
        system_prompt = f"""너는 {selected} 주가 분석 챗봇이야. 아래 규칙을 반드시 지켜서 답변해:

1. 반드시 아래 제공된 [실제 데이터]에 근거해서 답변한다.
2. 데이터에 없는 내용은 일반 지식으로 보충한다.
3. 핵심만 간결하게 답변한다.
4. 내용이 여러 개면 '## 제목'으로 주제를 나눈다.
5. 강조는 <b>강조</b> HTML 태그를 사용한다.
6. 각 주제는 최대 3줄 이내로 요약한다.
7. 불필요한 서론과 면책조항은 쓰지 않는다.
8. 항상 정중하고 공손한 존댓말('~습니다', '~됩니다')로 답변한다.

{data_context}

사용자 질문: """

    else:
        # 🧠 시장 전반 질문 → 애널리스트 모드!
        system_prompt = """너는 미국 주식시장 전문 애널리스트야. 아래 규칙을 반드시 지켜:

1. 미국 주식시장, 산업, 경제 전반에 대해 전문가답게 답변한다.
2. 핵심만 간결하게 답변한다.
3. 내용이 여러 개면 '## 제목'으로 주제를 나눈다.
4. 강조는 <b>강조</b> HTML 태그를 사용한다.
5. 각 주제는 최대 3줄 이내로 요약한다.
6. 특정 종목 상세 데이터가 필요하면 "NVDA, AAPL, TSLA, MSFT, GOOGL 중 하나를 물어보세요"라고 안내한다.
7. 불필요한 서론과 면책조항은 쓰지 않는다.
8. 항상 정중하고 공손한 존댓말('~습니다', '~됩니다')로 답변한다.

사용자 질문: """

    for model_name in MODELS:
        try:
            model = genai.GenerativeModel(model_name)
            full_prompt = system_prompt + req.message
            response = model.generate_content(full_prompt)
            reply = response.text

            db.collection("chat_history").add({
                "message": req.message,
                "reply": reply,
                "model": model_name,
                "created_at": firestore.SERVER_TIMESTAMP
            })

            return {"reply": reply, "model": model_name, "symbol": selected}
        except Exception as e:
            print(f"{model_name} 실패: {e}")
            continue
    return {"reply": "모든 모델이 응답하지 못했어요 🥲", "model": "none"}

# 📜 채팅 기록 불러오기 엔드포인트
@app.get("/chat/history")
async def get_chat_history():
    docs = db.collection("chat_history").order_by("created_at").stream()

    history = []
    for doc in docs:
        data = doc.to_dict()

        # 🕐 시간을 "14:05" 형태로 변환
        created = data.get("created_at")
        time_str = ""
        if created:
            time_str = created.strftime("%H:%M")  # 시:분만 뽑기

        history.append({
            "message": data.get("message"),
            "reply": data.get("reply"),
            "model": data.get("model"),
            "time": time_str,  # ← 시간 추가! ⏰
        })

    return {"history": history}

# 🎯 프론트엔드 연결 (반드시 맨 아래!)
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

# 🚀 서버 실행 (파일 맨 마지막!)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)