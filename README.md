# 📈 Stock Insight AI

> 주가 데이터를 분석하고, AI와 대화하며 인사이트를 얻는 웹 애플리케이션

저장된 주가 데이터를 실시간으로 요약·시각화하고, 그 요약 정보를 AI에게 주입하여
**데이터 기반의 정확한 답변**을 제공합니다.

---

## ✨ 주요 기능

- 📊 **주가 요약 & 차트** — 평균/최고/최저/등락률/트렌드 자동 계산 + 라인 차트
- 🤖 **데이터 기반 AI 채팅** — 요약 정보를 프롬프트에 주입한 Gemini 답변
- 🗂️ **데이터 관리(CRUD)** — 추가/조회/수정(메모 인라인 편집)/삭제
- 📜 **대화 기록** — 대화 자동 저장 + 목록 조회 + 삭제
- 🌙 **다크 모드** — 라이트/다크 토글 (설정 자동 저장)
- 🖱️ **팝업 드래그** — 창을 자유롭게 이동

지원 종목: `NVDA` `AAPL` `TSLA` `MSFT` `GOOGL`

---

## 🛠️ 기술 스택

| 구분 | 기술 |
|------|------|
| **프론트엔드** | HTML, CSS, JavaScript (Vanilla), Chart.js |
| **백엔드** | Python, FastAPI, Uvicorn |
| **데이터베이스** | Firebase Firestore |
| **AI** | Google Gemini API |
| **배포** | Vercel (프론트), Render (백엔드) |

> 💡 과제 예시는 OpenAI(GPT)였으나, **Google Gemini API**를 사용했습니다.

---

## 🌐 배포 URL

| 항목 | URL |
|------|-----|
| 🖥️ 프론트엔드 | [배포된 Vercel 주소] |
| ⚙️ 백엔드 API | [배포된 Render 주소] |
| 📄 Swagger UI | [Render 주소]/docs |

> ⚠️ 백엔드는 무료 티어(Render)로, **첫 요청 시 30초~1분** 지연될 수 있습니다.
> (콜드 스타트) 잠시 기다려 주세요!

---

## 💻 로컬 실행 방법

### 1. 저장소 클론
```bash
git clone https://github.com/leemin629/3-2st-mission
cd [\3-2st-mission\backend]
```

### 2. 가상환경 생성 & 활성화
```bash
python -m venv venv

# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 3. 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
프로젝트 루트에 `.env` 파일 생성 (아래 목록 참고)

### 5. 서버 실행
```bash
py -m uvicorn main:app --reload
```

브라우저에서 `http://localhost:8000` 접속!

---

## 🔑 환경 변수 목록

`.env` 파일에 아래 항목을 설정하세요.

```env
# Google Gemini API 키
GEMINI_API_KEY=your_gemini_api_key

# Firebase 서비스 계정 키 (JSON 경로 또는 내용)
FIREBASE_CREDENTIALS=your_firebase_credentials
```

> ⚠️ **키는 절대 코드에 하드코딩하지 마세요!** `.env`는 `.gitignore`에 포함되어야 합니다.

---

## 📁 프로젝트 구조

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

## 📡 API 엔드포인트

### 데이터 API
| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/data` | 데이터 추가 |
| GET | `/api/data` | 목록 조회 (종목 필터) |
| PUT | `/api/data/{id}` | 데이터 수정 |
| DELETE | `/api/data/{id}` | 데이터 삭제 |
| GET | `/api/data/summary` | 요약 정보 (프롬프트 주입용) |
| GET | `/api/data/history` | 차트용 시계열 데이터 |

### 대화 기록 API
| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/conversations` | 대화 저장 |
| GET | `/api/conversations` | 대화 목록 조회 |
| DELETE | `/api/conversations/{id}` | 대화 삭제 |

### AI 채팅 API
| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/chat` | 데이터 요약 주입 → Gemini 답변 |

---

## 🧠 컨텍스트 주입 원리

```
1. 사용자 질문 입력
2. 선택 종목의 요약 조회 (/api/data/summary)
3. 요약을 시스템 프롬프트에 삽입
4. Gemini API 호출
5. 답변 반환 + 대화 자동 저장
```

이 방식으로 AI가 **실제 저장된 데이터**를 근거로 답변합니다.

---

## 📸 스크린샷

### 1. 데이터 요약 + AI 채팅
![채팅 화면](screenshots/chat.png)

### 2. 데이터 관리 (CRUD)
![데이터 관리](screenshots/data.png)

### 3. 대화 기록 불러오기
![대화 기록](screenshots/conversations.png)

---

## 👤 만든 사람

[leemin629 / [GitHub 링크](https://github.com/leemin629/3-2st-mission)]