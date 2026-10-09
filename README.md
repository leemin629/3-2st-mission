# Stock Insight AI

미국 주식 5종목의 일별 가격을 저장·관리하고, 차트와 요약 통계 및 Gemini AI 설명을 제공하는 웹 애플리케이션입니다.

**가격은 Firestore에 저장된 자료를 기준으로 표시합니다.** ‘5개 종목 데이터 갱신’을 누르면 Alpha Vantage가 제공하는 일별 종가 중 저장되지 않은 날짜를 추가합니다. 장중 실시간 시세, 자동 주기 갱신, 최신 뉴스 검색 기능은 포함하지 않습니다.

문서 기준: 2026년 10월 9일 전달한 백엔드 수정본 및 5개 종목 갱신·복수 종목 채팅 업데이트(`v=20261009c`). 로컬에 실제 적용된 버전은 별도로 확인해야 합니다.

## 주요 기능

| 기능 | 동작 |
|---|---|
| 종목 선택 | NVDA, AAPL, TSLA, MSFT, GOOGL의 자료를 전환합니다. |
| 주가 요약 | 평균가, 마지막 저장 가격, 최고가, 최저가, 기간 등락률을 표시합니다. |
| 차트 | 종목별 전체 저장 자료를 날짜순으로 표시합니다. |
| 데이터 갱신 | 5개 종목을 순서대로 갱신하여 없는 거래일 자료를 추가하고 기존 가격·메모를 보존합니다. |
| 데이터 CRUD | 종목·날짜·가격·메모를 추가하고, 수정 버튼으로 편집하거나 삭제합니다. |
| AI 채팅 | 질문 대상 종목들의 저장 기간·건수·통계를 전달해 Gemini 답변을 생성합니다. 5개 전체 및 복수 종목 비교를 지원합니다. 대기 표시와 중복 전송 방지를 제공합니다. |
| 대화 기록 | 날짜·종목·질문·답변 미리보기 목록을 표시하고, 기록 선택 시 전체 질문·답변을 채팅창에 엽니다. 삭제도 지원합니다. |
| 표시 보조 | 가격의 색상·화살표, 다크 모드, 팝업 이동 및 선택한 창 앞으로 올리기를 지원합니다. |
| 오류 안내 | API 조회·저장·갱신·AI 응답 실패와 대화 저장 실패를 구분해 표시합니다. |

## 데이터 및 통계 기준

### 갱신과 보관

1. 버튼 한 번으로 **NVDA → AAPL → TSLA → MSFT → GOOGL 전체**를 순서대로 갱신합니다. 화면의 선택 종목은 유지합니다.
2. 종목마다 갱신 API를 호출하여 Alpha Vantage의 `TIME_SERIES_DAILY` 응답에서 일별 종가를 가져옵니다. 종목별 추가 건수·마지막 제공 날짜 또는 오류를 표시하며 일부 실패해도 나머지는 계속 처리합니다.
3. 해당 종목에 이미 같은 날짜의 자료가 있으면 추가하지 않습니다. 기존 수동 입력과 메모도 유지합니다.
4. 새 API 자료는 `종목_날짜` 문서 ID로 저장하고, 반복 실행 시 같은 거래일의 자동 자료를 중복 추가하지 않습니다.
5. 오래된 자료를 자동 삭제하지 않으므로 **100개를 초과해 누적**될 수 있습니다. 100개 자료는 100일의 달력 기간과 다릅니다.
6. 제공처가 반환하는 범위 밖의 누락 날짜는 이 버튼만으로 모두 복구된다고 보장할 수 없습니다.
7. API 한도·이용 권한·연결 오류는 화면에 표시합니다. 임의의 더미 가격으로 대체하지 않습니다.

현재 갱신 방식은 새 날짜를 추가하는 방식이므로, 제공처가 과거 가격을 정정하더라도 기존 날짜를 자동 재수정하지 않습니다. 사용자가 기존 자료를 삭제한 뒤 다시 갱신하면 제공 범위 안의 날짜는 다시 추가될 수 있습니다.

### 통계의 의미

기본 화면은 선택 종목의, 채팅은 질문 대상 종목별 **전체 저장 자료**를 사용합니다. 최근 100개나 최근 100일로 자동 제한하지 않습니다.

| 지표 | 계산 기준 |
|---|---|
| 마지막 저장 가격 | 날짜순으로 마지막 자료의 `value` |
| 평균가 | 전체 저장 가격의 합 ÷ 자료 수 |
| 최고가·최저가 | 저장된 `value`의 최대·최소 |
| 등락률 | `(마지막 가격 − 첫 가격) ÷ 첫 가격 × 100` |
| 추세 | 등락률이 양수면 상승, 음수면 하락, 0이면 보합 |

API에서 가져온 `value`는 **일별 종가**입니다. 따라서 최고·최저는 저장된 종가 중 최고·최저이며 장중 고가·저가가 아닙니다. 수동으로 추가한 자료도 통계와 차트 및 AI 요약에 포함됩니다. 수동 입력에는 동일 종목·날짜의 중복을 막는 제약이 없으므로 같은 날짜를 여러 번 등록하면 각각 계산됩니다.

- 마지막 저장 가격·최고가·최저가: 기간 평균가보다 높으면 **빨강 ▲**, 낮으면 **파랑 ▼**, 같으면 회색입니다.
- 등락률: 양수는 **빨강 ▲**, 음수는 **파랑 ▼**, 0은 회색입니다.
- 평균가는 기본 색상을 유지합니다.
- 가격 카드의 화살표는 평균가와 비교한 표시이며 전일 대비 변화가 아닙니다.

`GET /api/data/summary?symbol=NVDA&period=30`처럼 API에서 최근 N일 요약을 요청할 수도 있습니다. 이 기간은 마지막 저장 날짜부터 거꾸로 계산한 달력 일수입니다. 현재 화면과 채팅은 이 기간 옵션을 사용하지 않습니다.

## 사용 순서

1. 종목을 선택하고 저장 기간·건수를 확인합니다.
2. ‘5개 종목 데이터 갱신’을 한 번 눌러 다섯 종목을 순서대로 갱신합니다.
3. 갱신 결과와 마지막 저장 날짜를 확인합니다.
4. ‘데이터 관리 열기’에서 자료를 추가·수정·삭제합니다. 성공하면 표·요약·차트가 다시 조회됩니다.
5. 채팅창에서 질문합니다. “5개 종목 비교해 줘” 또는 “전체 종목 설명해 줘”는 다섯 종목을, “엔비디아와 애플 비교해 줘”는 명시한 두 종목을 사용합니다. 전체 요청·종목명이 없으면 기본으로 다섯 종목의 자료를 함께 사용합니다. 화면에서 선택한 종목이 기본 분석 범위를 제한하지 않습니다.
6. ‘대화 기록 보기’에서 기록을 누르면 해당 질문과 답변 전체를 확인할 수 있습니다.

‘새 대화’는 채팅 화면을 비우며 저장 기록은 유지합니다. 이전 기록을 다시 표시하는 기능과 AI가 다음 질문에서 그 맥락을 기억하는 기능은 다릅니다. 현재는 과거 대화를 다음 프롬프트에 포함하지 않습니다.

## 기술 및 구조

| 구분 | 사용 기술 |
|---|---|
| 화면 | HTML, CSS, JavaScript, Chart.js |
| API 서버 | Python, FastAPI, Uvicorn, Pydantic |
| 저장소 | Firebase Firestore |
| 일별 주가 수집 | Alpha Vantage, Requests |
| AI | Google Gemini API (`google-generativeai`) |
| 배포 구성 | FastAPI에서 화면과 API를 함께 제공; 기존 배포 주소는 Render |

| 파일 | 현재 역할 |
|---|---|
| `backend/main.py` | FastAPI 앱 생성, CORS·라우터 등록, 채팅·기록 API, 채팅 통계 계산, 정적 화면 제공 |
| `backend/routers/data.py` | 자료 CRUD, 화면용 요약 및 차트 API |
| `backend/routers/conversations.py` | 새 기록 저장, 기존·새 기록 통합 조회, 상세 조회·삭제 |
| `backend/routers/stock.py` | 종목별 일별 갱신 API(화면에서 5개 순차 호출) 및 별도 시세 조회 API |
| `backend/services/stock_service.py` | Alpha Vantage HTTP 요청, 타임아웃·오류 처리 |
| `backend/validation_utils.py` | 종목·날짜·가격·메모 검증 |
| `backend/firebase_config.py` | Firebase 서비스 계정 및 Firestore 연결 |
| `backend/requirements.txt` | Python 의존성 목록 |
| `frontend/index.html` | 화면 구조와 입력 폼 |
| `frontend/app.js` | API 요청, 차트·채팅·기록·CRUD 처리 |
| `frontend/style.css` | 화면·팝업·기록 목록·다크 모드 스타일 |
| `PROJECT_REPORT.md` | 구현 설명, 변경 내역, 검증 범위 및 발표 준비 |

실행 대상은 **`main:app`**입니다. 기존 `app.py`와 `server.py`는 다른 코드이며 이번 화면의 실행 진입점이 아닙니다. `seed_data.py`는 기존 가격·메모를 덮어쓸 수 있는 초기 수집 스크립트로, 화면의 보존형 갱신 버튼과 동작이 다릅니다.

## 로컬 실행: Windows PowerShell

### 기존 프로젝트와 가상환경을 사용하는 경우

프로젝트 최상위에 `venv`가 있는 현재 폴더 구조 기준입니다.

```powershell
cd "C:\Users\win\Desktop\코디세이\세번째 과제\3-2st-mission\backend"
..\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

브라우저에서 [로컬 화면](http://127.0.0.1:8000/)과 [로컬 Swagger](http://127.0.0.1:8000/docs)를 확인합니다. `Application startup complete.`가 출력되어야 앱 시작이 완료된 것입니다.

### 새로 설치하는 경우

프로젝트 최상위에서 가상환경을 만든 후 해당 Python으로 설치·실행합니다.

```powershell
git clone https://github.com/leemin629/3-2st-mission
cd 3-2st-mission
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
cd backend
..\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

새 환경에서의 의존성 설치 및 Python 버전 호환성은 이번 수정 검증에 포함되지 않았습니다. 설치 실패 시 오류를 확인하고 의존성 구성을 점검해야 합니다.

### 환경변수와 Firebase 인증

`backend/.env`에 실제 API 키를 설정합니다. 아래 값은 예시 자리표시자입니다.

```dotenv
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key
GEMINI_API_KEY=your_gemini_api_key
# 선택 사항: 계정에서 실제 사용할 수 있는 모델 이름을 쉼표로 지정
# GEMINI_MODELS=your_available_model_name
```

| 변수 | 의미 |
|---|---|
| `ALPHA_VANTAGE_API_KEY` | 일별 데이터 갱신·별도 시세 API 인증 |
| `GEMINI_API_KEY` | AI 모델 조회 및 답변 생성 인증 |
| `GEMINI_MODELS` | 선택 사항. 미지정 시 계정의 사용 가능한 텍스트 모델 후보를 조회합니다. |
| `FIREBASE_CREDENTIALS` | Firebase 서비스 계정 **JSON 전체 문자열**. 파일 경로가 아닙니다. |
| `PORT` | `python main.py` 실행 시 사용할 포트. 위 Uvicorn 명령에서는 `--port`를 사용합니다. |

Firebase는 `firebase_config.py`에 지정된 기존 로컬 인증 JSON을 유지하거나, 서버 실행 전에 `FIREBASE_CREDENTIALS`를 운영체제 환경변수로 설정합니다. 예를 들어 인증 JSON을 `backend/firebase-service-account.json`에 별도 보관한 경우:

```powershell
$env:FIREBASE_CREDENTIALS = Get-Content .\firebase-service-account.json -Raw
..\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

현재 코드의 Firebase 초기화는 `.env` 로드보다 먼저 발생할 수 있으므로 `FIREBASE_CREDENTIALS`는 위처럼 실행 환경에 먼저 설정하는 편이 확실합니다. `.env`와 서비스 계정 JSON은 Git에 올리지 않습니다. 새 이름의 인증 파일을 사용한다면 그 파일도 `.gitignore`에 추가합니다.

## API 목록

| 메서드 | 경로 | 동작 |
|---|---|---|
| GET | `/api/data?symbol=NVDA` | 날짜 내림차순 자료 목록 |
| POST | `/api/data` | 자료 추가 |
| PUT | `/api/data/{id}` | 종목·날짜·가격·메모 수정 |
| DELETE | `/api/data/{id}` | 자료 삭제 |
| GET | `/api/data/summary?symbol=NVDA` | 저장 기간·건수·통계·추세 |
| GET | `/api/data/history?symbol=NVDA` | 차트용 날짜·가격 배열 |
| POST | `/api/stocks/{symbol}/sync` | 없는 거래일의 일별 종가 추가 |
| GET | `/api/stocks/{symbol}` | 별도 시세 요청. 현재 화면 카드에서는 사용하지 않음 |
| POST | `/chat` | 저장 통계를 포함한 AI 답변 생성 |
| GET | `/chat/history` | 과거 기록을 시간순으로 조회 |
| GET | `/api/conversations` | 새 기록과 기존 기록을 최신순으로 조회 |
| GET | `/api/conversations/{id}` | 선택 대화 상세 조회 |
| POST | `/api/conversations` | 질문·답변 쌍을 별도로 저장 |
| DELETE | `/api/conversations/{id}` | 선택 기록 삭제 |

데이터 요청 예시:

```json
{"symbol":"NVDA","date":"2026-10-08","value":180.25,"memo":"수동 입력 예시"}
```

채팅 요청 예시:

```json
{"message":"평균가와 마지막 저장 가격을 비교해 주세요.","symbol":"NVDA"}
```

위 숫자는 API 형식 설명용 예시이며 실제 시세가 아닙니다.

## 저장 및 AI 처리

- `data`: 종목별 날짜·가격·메모. 새 자동 수집 자료에는 `source`도 저장합니다.
- `chat_history`: 새 자동 채팅 기록과 별도 저장 API의 기록. 질문·답변·모델·종목 표시 문자열·종목 목록(`symbols`)·서버 생성 시간을 저장합니다.
- `conversations`: 이전 구현의 기록을 읽고 상세 조회·삭제할 때만 함께 지원합니다. 기존 자료를 자동 이동하지 않습니다.
- 다크 모드 설정: Firestore가 아니라 브라우저 `localStorage`에 저장합니다.

통합 기록 ID는 `chat_history:문서ID` 또는 `conversations:문서ID` 형태입니다. 프론트엔드는 이를 URL 인코딩해 사용합니다. 접두어 없는 과거 ID는 `conversations` 문서로 처리합니다.

채팅은 전체 종목 요청이면 다섯 종목을, 명시한 지원 종목이 있으면 해당 종목들을, 종목을 명시하지 않으면 기본으로 다섯 종목을 함께 사용합니다. 각 종목의 저장 자료를 요약하여 기간·건수·가격 통계와 지침·질문을 하나의 프롬프트 문자열로 전달합니다. 모델을 재학습하는 방식은 아닙니다. 답변 생성 후 저장을 시도하며, 저장만 실패하면 답변을 반환하고 화면에 저장 실패를 표시합니다.

## 검증 상태와 한계

| 확인 항목 | 확인 수준 |
|---|---|
| Python·JavaScript 문법 | 수정 과정에서 검사 통과 |
| 기록 통합·상세·삭제, 입력 검증, 보존형 갱신 | 모의 Firestore 기반 백엔드 테스트 6개 통과 |
| 5개 순차 갱신·부분 실패 처리, 복수 종목 선택, 기록 선택, 색상·화살표, 안전한 출력, 오류 안내 | 모의 DOM 기능 검사 통과 |
| 일별 데이터 갱신 | 사용자가 선택 종목의 2026-10-08 자료까지 확인했다고 보고 |
| 최종 기록 목록 디자인·모바일·터치 | 실제 적용 화면의 최종 확인은 남아 있음 |
| 전체 CRUD·AI·기록의 실제 서비스 통합 | 이번 작업에서 실제 인증정보로 전 과정을 검증하지 않음 |
| 최신 코드의 Render 배포·새 환경 패키지 설치 | 미검증 |

종목별 저장 기간이 다르면 비교 시 그 차이를 밝히도록 AI에 지시합니다. 현재 화면과 채팅의 통계 함수는 같은 전체 기간 기준이지만 코드가 각각 존재합니다. 공통 서비스로 통합하는 작업은 남아 있습니다. AI 답변의 수치 사용은 화면 통계와 비교해야 하며, 수집하지 않은 뉴스나 가격 변동 원인을 최신 사실로 보장하지 않습니다.

현재 자료와 대화는 사용자별로 분리되지 않으며 별도 사용자 인증도 구현되어 있지 않습니다. CORS는 사용자 인증을 대신하지 않습니다. 기록 삭제는 데이터베이스의 해당 기록을 삭제하며, 이미 열려 있는 채팅 말풍선까지 즉시 제거하지는 않습니다.

## 기존 주소

아래 주소는 기존 문서에 등록된 프로젝트 주소입니다. 이번 수정본의 배포 완료나 현재 접속 상태를 의미하지 않습니다.

- [GitHub 저장소](https://github.com/leemin629/3-2st-mission)
- [Render 화면](https://three-2st-mission.onrender.com/)
- [Render Swagger](https://three-2st-mission.onrender.com/docs)

현재 구성은 FastAPI에서 정적 화면과 API를 함께 제공합니다. 별도 Vercel 배포는 이번 수정에서 수행하지 않았습니다. 다른 출처의 프론트엔드를 연결할 경우 실제 출처에 맞춘 CORS 설정이 필요합니다.

## 업데이트가 화면에 반영되지 않을 때

1. 실행 프로젝트의 `frontend/app.js`에서 `conversation-card`를 검색합니다.
2. `frontend/index.html`의 `app.js`와 `style.css` 참조에 `v=20261009c`가 있는지 확인합니다.
3. ZIP을 풀면서 `frontend/frontend` 또는 별도 압축파일 이름 폴더에 저장되지 않았는지 확인합니다.
4. 로컬 화면에서 `Ctrl+F5`로 새로고침합니다.
5. 필요하면 서버를 종료하고 위 가상환경 Python으로 다시 실행합니다.

`No module named 'google'` 오류가 발생하면 먼저 기존 `venv`의 Python으로 실행했는지 확인합니다. 일반 Python에 새로 설치하기 전에 실행 환경을 맞춥니다.
