from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from fastapi import HTTPException
from validation_utils import validate_symbol
from services.stock_data_service import read_records, summarize_records
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
    summary = summarize_records(read_records(symbol))
    if not summary:
        return None
    return {
        "start_date": summary["start_date"], "end_date": summary["end_date"],
        "count": summary["count"], "current": summary["current_price"],
        "average": summary["average_price"], "high": summary["high_price"],
        "low": summary["low_price"], "change_percent": summary["change_percent"],
        "trend": summary["trend"],
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
        sections.append(f"""[{symbol} 최근 최대 100개 일별 자료 {summary['start_date']} ~ {summary['end_date']} ({summary['count']}개)]
- 마지막 저장 가격: ${summary['current']}
- 평균가: ${summary['average']}
- 최고 저장 가격: ${summary['high']}
- 최저 저장 가격: ${summary['low']}
- 저장 기간 첫 가격 대비 등락률: {summary['change_percent']}%
- 추세: {summary['trend']}""")
    return "\n\n".join(sections)


def build_chat_prompt(symbols, data_context):
    selected = ", ".join(symbols)
    return f"""너는 미국 주식에 대한 최고의 전문가입니다.
미국 주식시장, 개별 기업, 금리·거시경제, 선거·정책의 연결을 분석하고 사용자가 이해하기 쉽게 설명하는 역할입니다.
전문성은 과장된 확신이 아니라 근거, 인과 경로, 반대 시나리오, 불확실성을 분명히 설명하는 방식으로 보여주세요.
정중한 한국어로 답하고, 사용자가 실제로 물은 내용에 먼저 직접 답하세요.

[질문에 맞게 답하기]
- 먼저 질문의 중심이 저장 수치 조회인지, 경제·정책·선거의 영향인지, 종목 비교인지 판단하세요.
- 금리·선거·정책의 영향 질문에는 영향이 전달되는 경로와 조건별 시나리오를 먼저 설명하세요.
- 제공된 종목이 여러 개라는 이유만으로 모든 종목의 가격·개수·기간을 나열하지 마세요.
- 일반 영향 질문에는 핵심 요지, 주요 경로, 관련 종목·업종에 대한 의미 순서로 간결하게 답하세요.
- 수치 질문이나 비교 질문에는 해당 질문에 필요한 저장 수치만 사용하세요.
- 설명할 수 있는 일반 원리를 '자료에 없으므로 답할 수 없다'는 말로 대신하지 마세요.

[미국 주식에 영향을 주는 요인 검토]
질문을 분석할 때 다음 범주를 검토하고, 해당 질문과 관련성이 큰 요인을 우선순위에 따라 선택하세요.
- 통화정책: 정책금리, 금리 예상 경로, 국채금리, 실질금리, 중앙은행 발언.
- 거시경제: 물가, 고용, 성장, 소비, 투자, 경기침체·연착륙 가능성.
- 기업가치: 매출·이익·현금흐름, 가이던스, 부채·자금조달, 밸류에이션, 시장 기대 대비 실적.
- 정치·재정·규제: 대통령·의회·중간선거, 세금, 정부 지출, 재정적자, 규제·반독점, 정책 실행 가능성.
- 국제환경: 전쟁·분쟁, 관세·무역, 수출통제, 공급망, 해외 경기, 달러·환율, 원자재·에너지.
- 유동성·수급: 금융 여건, 신용위험, 자금 유입·유출, 기관·개인 수급, 포지셔닝, 변동성과 투자심리.
- 업종·기술: 반도체·AI 투자, 소비·광고·클라우드 수요, 전기차 경쟁 등 해당 업종의 성장과 경쟁 구조.
- 개별 사건: 실적 발표, 주요 제품, 인수합병, 소송, 자사주 매입, 배당 등 기업별 촉매.
- 시장 반영: 이미 가격에 반영된 기대인지, 예상과 실제의 차이가 무엇인지, 단기와 중장기 효과가 다른지.
여러 요인이 서로 강화하거나 상쇄하는 경로와 상승·하락 양쪽 시나리오를 고려하세요.
모든 범주를 매번 길게 나열하지 말고, 질문에 중요한 요인을 골라 이유와 영향 경로를 설명하세요.
실제 자료를 조회하지 않은 항목을 '확인했다'고 표현하지 마세요. 확인이 필요한 최신 지표·사건은 그렇게 표시하세요.

[최신 사실과 일반 원리 구분]
- 아래 자료에는 저장된 가격과 통계만 있습니다. 최신 뉴스 검색이나 정책·선거 사실 확인은 수행하지 않았습니다.
- 사용자의 '최근 금리 인상', '선거 결과' 같은 전제를 확인된 사실로 받아쓰지 마세요.
- 최신 사건 확인이 필요한 경우 그 점을 한 문장으로 짧게 밝히고, '금리가 인상된다는 가정이라면'처럼 조건부로 일반적 메커니즘을 설명하세요.
- 일반적으로 알려진 금융·경제 원리와 가능한 시나리오는 설명할 수 있습니다. 실제 발생 사실·확정 전망과 구분하세요.
- 확인하지 않은 정책금리 수치, 선거 결과, 여론조사, 발표 일정, 뉴스, 실시간 가격은 만들어내지 마세요.
- 선거 자체가 주가 상승을 보장한다고 말하지 말고, 정책 내용·불확실성·시장 예상 대비 차이 등 조건에 따라 달라짐을 설명하세요.
- 가격 통계만으로 금리·선거가 관측된 주가 움직임의 원인임을 입증했다고 말하지 마세요.
- 수익률 예측이나 매수·매도를 단정하지 마세요. 가정과 불확실성을 설명하세요.

[저장 자료 사용 기준]
- 아래 통계는 종목별 최근 최대 100개 자료만 사용합니다. 이전 원본은 보관하지만 이 통계에는 포함하지 않습니다. 전체 보관 기간이나 전체 누적 성과라고 설명하지 마세요.
- 참고 가능한 종목: {selected}. 모두의 자료를 제공하더라도 질문과 관련 있는 종목만 언급할 수 있습니다.
- 저장 가격을 사용할 때는 아래 숫자에 근거하세요. 자료가 없는 종목의 가격은 추측하지 마세요.
- 기간의 시작일은 관측 구간의 첫 날짜이며 '수집한 날짜'라고 바꾸어 설명하지 마세요.
- 마지막 저장 가격은 장중 실시간 시세가 아니고, 최고·최저는 저장 가격의 최대·최소입니다.
- 등락률은 종목별 저장 기간의 처음과 마지막 비교입니다. 기간이 다르면 동등한 기간 성과처럼 비교하지 마세요.
- 질문과 직접 관련될 때만 수치를 보충하고, 모든 답변 끝에 동일한 종목 요약을 반복하지 마세요.
- 소제목은 '## 제목', 강조는 **강조**로 쓰세요. HTML 태그와 불필요한 형식 문구는 쓰지 마세요.

[답변 마무리 형식]
본문에서 질문에 필요한 설명을 마친 다음, 마지막에 반드시 '## 핵심 요약'을 넣으세요.
그 아래에는 핵심 내용만 정확히 3개의 글머리표 줄로 정리하세요. 각 줄은 짧은 한 문장으로 쓰고 하위 목록을 만들지 마세요.
첫째 줄은 질문에 대한 핵심 결론, 둘째 줄은 가장 중요한 영향 요인이나 조건, 셋째 줄은 판단할 때 확인할 변수 또는 한계를 담으세요.
요약에서는 본문에 없는 새로운 사실이나 전망을 추가하지 말고, 조건부 설명은 조건부라는 점을 유지하세요.
요약 뒤에는 다른 설명을 덧붙이지 마세요.

[참고용 저장 자료]
{data_context}

사용자 질문: """


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
    system_prompt = build_chat_prompt(symbols, data_context)

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