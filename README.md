# 📈 Stock Insight AI

> 미국 핵심 5개 종목을 분석하는 AI 챗봇

Google Gemini AI로 주가 데이터를 분석하고, 자연어로 대화하며 인사이트를 얻을 수 있는 풀스택 웹 서비스입니다.

---

## ✨ 주요 기능

- 📊 **실시간 주가 차트** — NVDA, AAPL, TSLA, MSFT, GOOGL (5종목)
- 🤖 **AI 대화 분석** — Google Gemini가 주가 데이터를 분석해 답변
- 💬 **대화 기록 관리** — 대화 저장 / 조회 / 삭제 (Firestore 연동)
- 🗂️ **데이터 관리** — 메모 인라인 편집 (더블클릭으로 수정)
- 📉 **요약 대시보드** — 평균가 / 현재가 / 최고가 / 최저가 / 등락률
- 🖱️ **드래그 가능한 팝업** — 데이터 관리·대화 기록·채팅 창 자유 이동

---

## 🛠️ 기술 스택

| 구분 | 기술 |
|------|------|
| **Backend** | FastAPI, Python 3.14 |
| **Database** | Firebase Firestore |
| **Frontend** | Vanilla JavaScript, Chart.js |
| **AI** | Google Gemini |
| **배포** | Render (백엔드 실시간 배포) |

---

## 📂 프로젝트 구조

```
3-2st-mission/
├── _backup/                    # 백업 파일 보관
│   ├── app_backup.py
│   └── server_backup.py
│
├── backend/                    # 백엔드 (FastAPI)
│   ├── routers/                # API 라우터
│   │   ├── __init__.py
│   │   ├── conversations.py    # 대화 기록 CRUD
│   │   ├── data.py             # 주가 데이터 CRUD
│   │   └── stock.py            # 주가 요약/차트 API
│   │
│   ├── services/               # 비즈니스 로직
│   │   ├── __init__.py
│   │   └── stock_service.py    # 주가 데이터 처리
│   │
│   ├── app.py                  # FastAPI 앱 (라우터 등록)
│   ├── main.py                 # 서버 진입점
│   ├── server.py               # 서버 실행 스크립트
│   ├── firebase_config.py      # Firebase 연결 설정
│   ├── seed_data.py            # 초기 데이터 삽입
│   ├── delete_all.py           # 데이터 전체 삭제 유틸
│   ├── test_stock.py           # 주가 API 테스트
│   ├── index.html              # (백엔드용 정적 파일)
│   ├── MODEL_LIST              # 사용 가능한 Gemini 모델 목록
│   ├── requirements.txt        # Python 패키지 목록
│   └── nvda-catch-up-firebase-adminsdk.json  # Firebase 인증키 (비공개)
│
├── frontend/                   # 프론트엔드
│   ├── index.html              # 메인 화면
│   ├── app.js                  # 전체 로직 (차트·채팅·CRUD)
│   └── style.css               # 스타일
│
├── venv/                       # 가상환경 (Git 제외)
├── .env                        # 환경변수 (API 키 등, 비공개)
├── .gitignore
├── PRD.md                      # 제품 요구사항 문서
└── README.md                   # 프로젝트 설명 (현재 문서)
```

---

## 🚀 실행 방법

### 1. 저장소 클론
```bash
git clone <저장소_URL>
cd 3-2st-mission
```

### 2. 가상환경 생성 및 활성화
```bash
# 가상환경 생성
python -m venv venv

# 활성화 (Windows)
venv\Scripts\activate

# 활성화 (Mac/Linux)
source venv/bin/activate
```

### 3. 패키지 설치
```bash
pip install -r backend/requirements.txt
```

### 4. 환경변수 설정
프로젝트 루트에 `.env` 파일을 만들고 아래 내용을 채웁니다.
```env
GEMINI_API_KEY=your_gemini_api_key_here
```
> Firebase 인증키(`nvda-catch-up-firebase-adminsdk.json`)는 `backend/` 폴더에 위치해야 합니다.

### 5. 서버 실행
```bash
cd backend
uvicorn main:app --reload
```

### 6. 브라우저에서 접속
```
http://localhost:8000
```

---

## 🔌 API 엔드포인트

### 📊 주가 데이터 (`/api/data`)
| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/api/data?symbol=NVDA` | 종목별 데이터 목록 조회 |
| `GET` | `/api/data/summary?symbol=NVDA` | 요약 정보 (평균/현재/최고/최저/등락률) |
| `GET` | `/api/data/history?symbol=NVDA` | 차트용 날짜·가격 데이터 |
| `POST` | `/api/data` | 데이터 추가 |
| `PUT` | `/api/data/{id}` | 데이터 수정 (메모 등) |
| `DELETE` | `/api/data/{id}` | 데이터 삭제 |

### 💬 대화 기록 (`/api/conversations`)
| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/api/conversations` | 대화 목록 조회 |
| `POST` | `/api/conversations` | 대화 저장 |
| `DELETE` | `/api/conversations/{id}` | 대화 삭제 |

### 🤖 채팅 (`/chat`)
| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/chat` | Gemini AI에게 질문하고 답변 받기 |
| `GET` | `/chat/history` | 채팅 기록 불러오기 |

---

## 🎨 주요 UI 특징

- **종목 선택 버튼** — 클릭 시 차트·요약·데이터 동시 갱신
- **색상 코딩** — 상승 🔴 빨강 / 하락 🔵 파랑 / 동일 ⚪ 회색
- **드래그 팝업** — 헤더를 잡고 자유롭게 이동
- **메모 인라인 편집** — 더블클릭 → 입력 → 엔터로 저장
- **버튼 색상 구분** — 데이터 관리(빨강) / 대화 기록(초록) / 채팅(파랑)

---

## 📌 향후 계획

- [ ] 🌙 다크 모드 지원
- [ ] 🔍 종목 검색 기능
- [ ] 👤 로그인 / 회원 관리
- [ ] ⭐ 관심 종목 즐겨찾기

---

## 👤 만든 사람

made with 💙 by leemin629
