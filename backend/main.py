from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import stock   # 라우터 불러오기
import requests
import os
from dotenv import load_dotenv

app = FastAPI(title="Stock Insight AI")

# CORS 설정 (프론트엔드 연결용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(stock.router)  # ← 라우터 연결! 

# 환경변수 로드
load_dotenv()
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

# 서버 생존 확인용 (신규 추가!)
@app.get("/")
def root():
    return {"message": "Stock Insight AI 서버가 살아있어요!"}

# 주가 조회 (server.py에서 가져옴)
@app.get("/stock/{symbol}")
def get_stock(symbol: str):
    return get_stock_data(symbol)  # ← 서비스 호출만!

   