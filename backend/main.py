from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import stock
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel      # ← 추가!
import google.generativeai as genai # ← 추가!
import os
from dotenv import load_dotenv
from firebase_config import db
from firebase_admin import firestore

app = FastAPI(title="Stock Insight AI")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(stock.router)

# 환경변수 로드
load_dotenv()
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # ← 추가!

# 🤖 Gemini 설정
genai.configure(api_key=GEMINI_API_KEY)

# 📩 요청 데이터 형식 정의
class ChatRequest(BaseModel):
    message: str

# 사용할 모델 목록 (폴백용)
MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
]
# 💬 채팅 엔드포인트 (★ mount보다 위에 있어야 함!)
@app.post("/chat")
async def chat(req: ChatRequest):
    # 🎯 AI 답변 규칙 (간결하게!)
    system_prompt = """너는 주가 분석 챗봇이야. 아래 규칙을 반드시 지켜서 답변해:

1. 핵심만 간결하게 답변한다.
2. 내용이 여러 개면 '## 제목'으로 주제를 나눈다.
3. 강조할 부분은 마크다운(**) 대신 반드시 HTML 태그 <b>강조</b>를 사용한다.
4. 각 주제는 새로운 줄에서 시작한다.
5. 각 주제는 최대 3줄 이내로 요약한다.
6. 불필요한 서론과 면책조항은 쓰지 않는다.
7. 전체 답변은 되도록 짧게 유지한다.

사용자 질문: """

    for model_name in MODELS:
        try:
            model = genai.GenerativeModel(model_name)
            # 🎯 규칙 + 질문을 합쳐서 보내기!
            full_prompt = system_prompt + req.message
            response = model.generate_content(full_prompt)
            reply = response.text  # ← 답변을 변수에 저장

            # 💾 Firestore에 채팅 기록 저장
            db.collection("chat_history").add({
                "message": req.message,              # 사용자 질문
                "reply": reply,                      # AI 답변
                "model": model_name,                 # 사용된 모델
                "created_at": firestore.SERVER_TIMESTAMP  # 저장 시간
            })

            return {"reply": reply, "model": model_name}
        except Exception as e:
            print(f"{model_name} 실패: {e}")
            continue
    return {"reply": "모든 모델이 응답하지 못했어요 🥲", "model": "none"}

# 📜 채팅 기록 불러오기 엔드포인트
@app.get("/chat/history")
async def get_chat_history():
    # created_at 기준 오래된 순으로 정렬해서 가져오기
    docs = db.collection("chat_history").order_by("created_at").stream()
    
    history = []
    for doc in docs:
        data = doc.to_dict()
        history.append({
            "message": data.get("message"),
            "reply": data.get("reply"),
            "model": data.get("model"),
        })
    
    return {"history": history}

# 🎯 프론트엔드 연결 (반드시 맨 아래!)
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")