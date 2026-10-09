# Stock Insight AI 수정 파일 — 2026-10-09

이 ZIP은 전체 프로젝트가 아니라 **교체할 파일만 포함한 수정 묶음**입니다.
기존 3-2st-mission 폴더 안에 압축을 풀어 backend와 frontend 파일을 덮어쓰세요.
기존 README.md, .env, Firebase 인증 파일, requirements.txt 및 .git은 그대로 유지됩니다.

## 확인된 문제와 수정

1. 대화 기록의 행에 열기 동작이 없었습니다. 질문·답변 클릭 및 보기 버튼을 추가했습니다.
2. 채팅 저장은 chat_history, 기록 조회는 conversations로 나뉘어 있었습니다.
   새 대화는 chat_history로 저장하며, 조회·상세·삭제는 두 컬렉션 모두 지원합니다.
3. 화면의 현재가는 실시간 시세가 아니라 마지막 저장 가격이었습니다.
   마지막 저장 가격으로 명칭을 바꾸고 저장 기간·건수와 실시간이 아님을 표시했습니다.
4. 데이터 추가 입력 폼과 삭제 버튼이 없었습니다. 추가·전체 항목 수정·삭제 UI를 추가했습니다.
5. 서버가 400/500 오류를 반환해도 프론트엔드가 성공으로 취급했습니다.
   실패 사유를 표시하며 실패한 입력값은 지우지 않습니다.
6. 수정·삭제 후 차트와 요약이 갱신되지 않았습니다. 작업 후 모두 다시 조회합니다.
7. 채팅 요청의 symbol을 서버가 받지 않았습니다. 질문에 종목명이 없으면 선택 종목을 사용합니다.
8. 기록·데이터의 일부 출력에 HTML 이스케이프가 없었습니다. 안전한 텍스트 출력으로 바꿨습니다.
9. 버튼을 여러 번 눌러 중복 채팅 요청을 보낼 수 있었습니다. 응답 중 중복 전송을 막습니다.
10. 빈 데이터/조회 실패에도 고정 예시 가격이 남았습니다. 빈 값과 오류 안내로 바꿨습니다.
11. 실제 없는 날짜, NaN, 무한대 검증을 보완했습니다.
12. 고정 Gemini 모델 목록 대신 계정의 모델 조회 또는 GEMINI_MODELS 환경변수를 사용합니다.
    AI 답변 생성 후 기록 저장만 실패한 경우 답변을 반환하면서 저장 실패를 알립니다.
13. 팝업을 누르면 앞으로 올라오도록 하고, 헤더 드래그와 버튼 클릭을 구분했습니다.

## 가격과 저장 데이터의 관계

- 실시간 가격 표시나 자동 주기 갱신은 이번 수정에 포함되지 않습니다.
- 선택 종목 데이터 갱신 버튼은 Alpha Vantage TIME_SERIES_DAILY를 요청합니다.
- API가 제공한 일별 종가 중 기존 데이터에 없는 날짜만 추가합니다.
- 기존 날짜의 가격, 사용자가 작성한 메모와 수동 데이터는 덮어쓰지 않습니다.
- 반복 갱신해도 동일 거래일 데이터를 중복 추가하지 않습니다.
- API의 호출 한도/권한/연결 오류는 화면에 안내하며 임의 가격으로 대체하지 않습니다.
- 버튼으로 받을 수 있는 범위와 마지막 거래일은 API 응답에 따라 달라집니다.
- 기존 seed_data.py는 기존 자료와 메모를 덮어쓸 수 있으므로 이 갱신 버튼과 동작이 다릅니다.

## 로컬 실행

기존 환경변수와 설치된 패키지를 유지한 상태에서 PowerShell에서 실행하세요.

```powershell
cd "실제 프로젝트 경로\3-2st-mission\backend"
python -m uvicorn main:app --reload --port 8000
```

브라우저에서 http://127.0.0.1:8000/ 을 열고 Ctrl+F5로 새로고침하세요.

Render 실행 대상도 main:app이어야 합니다. server.py 또는 app.py는 다른 코드입니다.

## 적용 후 확인 순서

1. 선택 종목을 바꾸고 저장 기간 및 차트가 일치하는지 확인합니다.
2. 채팅을 보내 답변을 받은 뒤 대화 기록 보기를 엽니다.
3. 질문·답변 또는 보기 버튼을 눌러 선택한 대화가 열리는지 확인합니다.
4. 데이터 관리에서 추가 → 수정 → 삭제 후 표·요약·차트를 확인합니다.
5. 갱신 버튼을 눌러 결과나 API 오류 안내를 확인합니다.

## 검증 범위

- Python 문법 검사, JavaScript 문법 검사 통과.
- 모의 Firestore를 사용한 백엔드 6개 테스트 통과:
  통합 기록 조회·상세·삭제, 잘못된 ID, 새 기록 저장 컬렉션,
  날짜·가격 검증, 기존 데이터 보존 및 반복 갱신, 비정상 갱신 응답.
- 모의 DOM 테스트 통과: 기록 행/보기 버튼 연결, 팝업 전환,
  답변 HTML 이스케이프 및 서버 오류 처리.
- 실제 브라우저의 레이아웃·터치 동작 및 외부 서비스 연결은 미검증입니다.
- 실제 Firebase, Gemini, Alpha Vantage 인증정보를 사용하거나 운영 데이터를 변경하지 않았습니다.
- 기존 requirements.txt의 설치 가능 여부와 실제 배포 상태는 이번 검증에 포함되지 않습니다.

첨부 원본에는 Firebase 서비스 계정 인증 JSON이 포함되어 있었습니다.
이 수정 묶음에는 인증정보를 넣지 않았습니다. GitHub에 올릴 때 해당 JSON과 .env는 제외하세요.

## GitHub 반영

기존 프로젝트에 파일을 덮어쓴 뒤 프로젝트 최상위에서:

```powershell
git status --short
git add backend/main.py backend/routers/conversations.py backend/routers/data.py backend/routers/stock.py backend/services/stock_service.py backend/validation_utils.py frontend/app.js frontend/index.html frontend/style.css FIX_README.md
git diff --cached --stat
git commit -m "Fix conversation history and data management"
git push origin main
```

현재 브랜치가 main인 경우의 예시입니다. 위 실행은 사용자가 자신의 PC에서 진행합니다.
