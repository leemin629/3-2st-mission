from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
from dotenv import load_dotenv
from firebase_config import db
from firebase_admin import firestore   # ← 이거 추가!
import google.generativeai as genai
from pydantic import BaseModel

# 1️⃣ 먼저 app을 만들어요 (맨 위로!)
app = FastAPI()

# 2️⃣ 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3️⃣ 환경변수 로드
load_dotenv()
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

# 🔽 여기 추가
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_KEY)

# 🔄 폴백용 모델 리스트
MODEL_LIST = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
]
# 4️⃣ API는 딱 하나만! (저장 포함)
@app.get("/stock/{symbol}")
def get_stock(symbol: str):
    # 더미 데이터
    data = {
        "Global Quote": {
            "01. symbol": symbol,
            "05. price": "138.50",
            "09. change": "-2.30",
            "10. change percent": "-1.63%"
        }
    }

    # Firestore에 저장
    db.collection("stocks").document(symbol).set({
        "symbol": symbol,
        "data": data,
        "created_at": firestore.SERVER_TIMESTAMP
    })

    return data

# 요청 형식 정의
class ChatRequest(BaseModel):
    message: str
    symbol: str = "NVDA"

@app.post("/chat")
def chat(req: ChatRequest):
    # Firestore에서 저장된 주가 가져오기
    doc = db.collection("stocks").document(req.symbol).get()
    if doc.exists:
        stock_info = doc.to_dict()["data"]["Global Quote"]
    else:
        stock_info = {}

    # Gemini에게 보낼 프롬프트
    prompt = f"""
너는 친절한 주식 분석 도우미야. 아래 {req.symbol} 주가 데이터를 참고해서 답해줘.

주가 데이터: {stock_info}

사용자 질문: {req.message}
"""

    # 🔄 폴백 로직: 모델을 순서대로 시도
    for model_name in MODEL_LIST:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            print(f"✅ 성공: {model_name}")
            return {"reply": response.text, "model": model_name}
        except Exception as e:
            print(f"❌ 실패: {model_name} → {e}")
            continue

    # 전부 실패한 경우
    return {"reply": "죄송해요, 지금은 답변할 수 없어요. 잠시 후 다시 시도해주세요."}
 # ✅ [실제용] 내일 켤 때 위 return 삭제하면 됨
    # url = "https://www.alphavantage.co/query"
    # params = {
    #     "function": "GLOBAL_QUOTE",
    #     "symbol": symbol,
    #     "apikey": API_KEY
    # }
    # response = requests.get(url, params=params)
    # return response.json()