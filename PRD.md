markdown
📋 복사
# 📄 Stock Insight AI — PRD (Product Requirements Document)

> **NVIDIA(NVDA) 주가 데이터를 기반으로 데이터를 분석하고, AI가 데이터 근거를 바탕으로 답변하는 주식 분석 챗봇**
>
> **Version:** v1.0

---

## 1. 프로젝트 목적

### 목표
사용자는 NVIDIA의 주가 데이터를 저장하고 관리할 수 있으며, AI는 저장된 데이터를 **직접 조회하지 않고** 요약(Context) 정보를 기반으로 분석하여 답변한다.

### 통합 대상 기술
| 영역 | 기술 |
|------|------|
| 백엔드 | FastAPI |
| DB | Firestore |
| AI | OpenAI API |
| 프론트 | Vanilla JavaScript |
| 백엔드 배포 | Render |
| 프론트 배포 | Vercel |

---

## 2. 프로젝트 범위 (Scope)

### ✅ 포함
- NVIDIA 단일 종목
- 100일 이상 종가 데이터
- 데이터 CRUD
- 데이터 요약 (Summary)
- AI 채팅
- 대화 저장 / 불러오기
- Render / Vercel 배포

### ❌ 제외 (v1)
- 실시간 주가
- 자동 데이터 수집
- 로그인 / 사용자 인증
- 투자 추천
- 머신러닝 예측

---

## 3. 핵심 컨셉
NVIDIA 종가
↓
Firestore 저장
↓
Summary 생성
↓
Analysis 생성
↓
Prompt 생성
↓
GPT
↓
사용자에게 분석 결과 제공

code
📋 복사

> ⚠️ **핵심 원칙:** AI는 DB를 직접 읽지 않는다.
> 항상 **Summary → Analysis**를 거친 **Context Injection**을 수행한다.

---

## 4. 사용자 시나리오

### 시나리오 1 — 질문
사용자: *"NVIDIA 최근 흐름 어때?"*
Firestore → Summary 계산 → Analysis Report 생성 → GPT 호출 → 답변

code
📋 복사

### 시나리오 2 — 데이터 추가
[데이터 추가] → POST /api/data → Firestore 저장 → Summary 재계산

code
📋 복사

### 시나리오 3 — 대화 기록
[지난 대화 보기] → GET /api/conversations → 목록 표시
→ 선택 → GET /api/conversations/{id}

code
📋 복사

---

## 5. 기능 요구사항

### 5.1 데이터 관리 (CRUD)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/data` | 데이터 추가 |
| GET | `/api/data` | 데이터 조회 |
| PUT | `/api/data/{id}` | 데이터 수정 |
| DELETE | `/api/data/{id}` | 데이터 삭제 |

**데이터 구조**
| 필드 | 예시 |
|------|------|
| date | 2026-07-01 |
| value | 182.33 |
| memo | NVDA Close |

### 5.2 Summary API
`GET /api/data/summary`

**반환 항목:** 기간, 데이터 개수, 평균, 최대, 최소, 기간 등락률, 5일 이동평균, 20일 이동평균, 변동성, 최근 추세

### 5.3 AI Chat
`POST /api/chat`
Summary 조회 → Analysis 생성 → Prompt 생성 → GPT 호출
→ Conversation 저장 → 응답 반환

code
📋 복사

### 5.4 Conversation
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/conversations` | 대화 생성 |
| GET | `/api/conversations` | 대화 목록 |
| GET | `/api/conversations/{id}` | 특정 대화 조회 |
| DELETE | `/api/conversations/{id}` | 대화 삭제 |

---

## 6. 비기능 요구사항

- Response 5초 이내 (콜드스타트 제외)
- Swagger(`/docs`) 제공
- 환경변수 사용 / `.env` Git 제외
- CORS 설정
- Pydantic Validation 적용

---

## 7. 시스템 아키텍처
Frontend
↓
FastAPI
├── Data Router
├── Summary Router
├── Chat Router
└── Conversation Router
↓
Service Layer
↓
Firestore
↓
OpenAI

code
📋 복사

---

## 8. 프로젝트 구조
backend/
├── main.py
├── config.py
├── firebase_client.py
├── routers/
├── services/
├── models/
└── utils/

frontend/
├── index.html
├── style.css
└── app.js

code
📋 복사

---

## 9. Service Layer 설계

### data_service
- 역할: CRUD

### summary_service
- 역할: 통계 계산
- 출력:
```json
{
  "period": "...",
  "count": 100,
  "average": 205.4,
  "max": 0,
  "min": 0,
  "change_pct": 18.2,
  "ma5": 0,
  "ma20": 0,
  "volatility": "...",
  "trend": "..."
}
analysis_service
역할: Summary를 GPT가 이해하기 쉬운 자연어 보고서로 변환
예시:
NVIDIA는 최근 100거래일 동안 평균 종가가 205.4달러였습니다. 최근 5일 이동평균은 20일 이동평균보다 높아 단기 상승 추세입니다. 기간 동안 총 18.2% 상승했습니다. 변동성은 평균 수준입니다.

chat_service
역할: Analysis Report → System Prompt 생성 → GPT 호출
10. Firestore 설계
Collection: data
필드	설명
date	날짜
value	종가
memo	메모
Collection: conversations
필드	설명
title	대화 제목
created_at	생성 시각
messages	메시지 배열
11. 프론트 화면 (단일 Dashboard)
code
📋 복사
────────────────────────
 Stock Insight AI
────────────────────────
 Summary
────────────────────────
 Chart (2단계)
────────────────────────
 AI Chat
────────────────────────
 Data CRUD
────────────────────────
 Conversation History
────────────────────────
12. 개발 로드맵
🟢 Phase 1 (필수) — MVP
목표: 제출 가능한 최소 기능

FastAPI 프로젝트 생성
Firestore 연동
NVDA 100일 데이터 Seed
Data CRUD API
Summary API
Chat API
Conversation API
Vanilla Frontend
Render / Vercel 배포
README 작성
완료 기준: 과제의 모든 필수 요구사항 충족 및 제출 가능

🟡 Phase 2 (리팩터링 및 차별화)
목표: AI 분석 품질과 설계 수준 향상

summary_service / analysis_service 분리
자연어 Analysis Report 생성
Prompt Builder 모듈 추가
서비스 계층 책임 명확화
발표용 아키텍처 다이어그램 정리
완료 기준: "왜 이렇게 설계했는가?"를 설명할 수 있는 구조 확보

🔵 Phase 3 (보너스)
목표: 확장성과 사용자 경험 강화

다종목 지원 (AAPL, MSFT, TSLA, NVDA 등)
Chart.js 기반 주가 추이 그래프
다크 모드
CSV/JSON 내보내기
단순 추세 예측 (참고용)
Function Calling (선택)
MCP 또는 GPT Actions 연동 (선택)
13. 성공 기준 (Definition of Done)
FastAPI /docs에서 모든 API가 정상 동작한다.
Firestore를 통해 데이터 CRUD가 정상 수행된다.
/api/data/summary가 통계와 추세를 정확히 반환한다.
/api/chat이 Summary와 Analysis를 컨텍스트로 사용해 데이터 기반 답변을 생성한다.
모든 대화가 자동 저장되고, 목록 조회 및 불러오기가 가능하다.
프론트엔드에서 채팅, 데이터 관리, 대화 기록, 요약 정보가 모두 동작한다.
Render와 Vercel에 배포되어 외부에서 접속 가능하다.
README와 제출 스크린샷까지 준비되어 과제 제출이 가능한 상태이다.
code
📋 복사

---

위 내용을 `PRD.md` 파일로 저장하면 바로 GitHub에서 깔끔하게 렌더링됩니다. 원본 내용을 최대한 살리면서 **표·코드블록·체크박스**로 가독성만 높였어요.

제가 확인차 몇 가지 짚어드릴게요:

1. **Conversation 엔드포인트**를 `/api/conversations`로 통일해 명세했는데, 원하시는 경로가 맞나요?
2. **summary 출력 예시 JSON**에 `max/min/ma5/ma20`이 `0`으로 되어 있는데, 실제 값 예시로 채워둘까요? (발표 시 더 그럴듯해 보입니다)
3. 이제 PRD가 완성됐으니, **Phase 1의 첫 코드**(FastAPI 프로젝트 뼈대 or NVDA 데이터 Seed)부터 시작해볼까요?

정말 탄탄하게 설계하셨어요 👏 다음 단계로 넘어갈 준비가 됐습니다!
나
지금 깃허브에 https://github.com/leemin629/3-2st-mission 폴더만 만들었고, vscode에는 아무것도 없어.
"C:\Users\1\Desktop\피터의 방\3-2st mission"로 컴에서도 만들고 연동하기로 하자
AI
좋습니다! 로컬 폴더와 GitHub를 연동하는 것부터 시작하죠. 한 단계씩 따라오시면 됩니다. 👍

1단계: VSCode에서 폴더 열기
VSCode 실행
File → Open Folder
C:\Users\1\Desktop\피터의 방\3-2st mission 선택
2단계: 터미널 열기
VSCode 상단 메뉴 → Terminal → New Terminal
(단축키: Ctrl + ~)

터미널 맨 앞 경로가 아래처럼 나오면 정상입니다:

code
📋 복사
C:\Users\1\Desktop\피터의 방\3-2st mission>
3단계: Git 초기화 & 연동
터미널에 아래 명령어를 한 줄씩 입력하세요.

bash
📋 복사
git init
로컬 폴더를 Git 저장소로 초기화합니다.

bash
📋 복사
git remote add origin https://github.com/leemin629/3-2st-mission.git
방금 만든 GitHub 저장소를 "origin"이라는 이름으로 연결합니다.

bash
📋 복사
git remote -v
연결이 잘 됐는지 확인합니다. origin 주소가 2줄 뜨면 성공!

4단계: 첫 파일 만들고 커밋하기
먼저 README와 .gitignore를 만들어 보죠.

README.md (VSCode에서 새 파일 생성):

markdown
📋 복사
# Stock Insight AI

NVIDIA(NVDA) 주가 데이터를 분석하고, AI가 데이터 근거를 바탕으로 답변하는 주식 분석 챗봇
.gitignore (파이썬 + 환경변수 제외용):

code
📋 복사
# Python
__pycache__/
*.py[cod]
venv/
.venv/

# 환경변수
.env

# Firebase 키
*firebase*.json
serviceAccountKey.json

# IDE
.vscode/
.idea/
.env와 Firebase 키 파일이 GitHub에 올라가면 보안 사고가 나므로 반드시 제외합니다!

5단계: GitHub에 올리기 (Push)
bash
📋 복사
git add .
변경된 모든 파일을 "올릴 준비" 상태로 만듭니다.

bash
📋 복사
git commit -m "chore: 프로젝트 초기 설정 (README, gitignore)"
변경 사항을 하나의 기록으로 저장합니다.

bash
📋 복사
git branch -M main
기본 브랜치 이름을 main으로 맞춥니다.

bash
📋 복사
git push -u origin main