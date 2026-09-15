// 서버에서 받아온 주가를 저장할 변수
let stockData = null;

// 🎯 색상+화살표를 적용하는 함수
function applyColor(element, value, baseline) {
  if (value > baseline) {
    element.style.color = "#e53935";  // 빨강 (상승) 🔴
    element.textContent += " ▲";
  } else if (value < baseline) {
    element.style.color = "#1e88e5";  // 파랑 (하락) 🔵
    element.textContent += " ▼";
  } else {
    element.style.color = "#757575";  // 회색 (동일)
  }
}

// 페이지가 열리면 NVDA 주가를 한 번 받아온다
async function loadStock() {
  try {
    const response = await fetch("http://127.0.0.1:8000/stock/NVDA");
    const data = await response.json();
    stockData = data["Global Quote"];

    console.log("주가 데이터 받음:", stockData);

    const prevClose = Number(stockData["08. previous close"]);

    // ── 현재가 ──
    const priceEl = document.getElementById("currentPrice");
    const currentPrice = Number(stockData["05. price"]);
    priceEl.textContent = "$" + currentPrice.toFixed(2);
    applyColor(priceEl, currentPrice, prevClose);

    // ── 등락률 ──
    const changeEl = document.getElementById("changePercent");
    const numberPercent = parseFloat(stockData["10. change percent"]);
    if (numberPercent > 0) {
      changeEl.textContent = "+" + numberPercent.toFixed(2) + "% ▲";
      changeEl.style.color = "#e53935";
    } else if (numberPercent < 0) {
      changeEl.textContent = numberPercent.toFixed(2) + "% ▼";
      changeEl.style.color = "#1e88e5";
    } else {
      changeEl.textContent = numberPercent.toFixed(2) + "%";
      changeEl.style.color = "#757575";
    }

        // ── 최고가 ──
    const highEl = document.getElementById("highPrice");
    const highPrice = Number(stockData["03. high"]);
    if (isNaN(highPrice)) {
      highEl.textContent = "—";                    // ✅ 데이터 없으면 대시!
    } else {
      highEl.textContent = "$" + highPrice.toFixed(2);
      applyColor(highEl, highPrice, prevClose);
    }

    // ── 최저가 ──
    const lowEl = document.getElementById("lowPrice");
    const lowPrice = Number(stockData["04. low"]);
    if (isNaN(lowPrice)) {
      lowEl.textContent = "—";                     // ✅ 데이터 없으면 대시!
    } else {
      lowEl.textContent = "$" + lowPrice.toFixed(2);
      applyColor(lowEl, lowPrice, prevClose);
    }

  } catch (error) {
    console.log("데이터 받기 실패:", error);
  }
}

// 페이지 열리자마자 실행
loadStock();

// HTML 요소 찾기
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const chatMessages = document.getElementById("chatMessages");

// 메시지를 화면에 추가하는 함수 (async로 변경!)
async function sendMessage() {
  const text = messageInput.value.trim();
  if (text === "") return;

  // 사용자 메시지
  const userRow = document.createElement("div");
  userRow.className = "message-row message-row--user";
  userRow.innerHTML =
    '<span class="message__time">' + getCurrentTime() + "</span>" +
    '<div class="message message--user">' + text + "</div>";
  chatMessages.appendChild(userRow);
  scrollToBottom();

  messageInput.value = "";

  // "입력 중..." 표시 (답변 기다리는 동안 보여줌)
  const loadingRow = document.createElement("div");
  loadingRow.className = "message-row message-row--ai";
  loadingRow.innerHTML =
    '<div class="message message--ai">입력 중...</div>';
  chatMessages.appendChild(loadingRow);
  scrollToBottom();

  // 🤖 서버에서 Gemini 답변 받기 (기다림)
  const reply = await getAiReply(text);

    // "입력 중..." 지우고 진짜 답변으로 교체 (줄바꿈 변환!)
  loadingRow.innerHTML =
        '<div class="message message--ai">' + formatReply(reply) + "</div>" +
    '<span class="message__time">' + getCurrentTime() + "</span>";
}

// Enter 키로 전송
messageInput.addEventListener("keydown", function (e) {
  if (e.key === "Enter") {
    sendMessage();
  }
});

// 전송 버튼 클릭
sendBtn.addEventListener("click", sendMessage);

// 채팅창 맨 아래로 스크롤
function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 🤖 서버(/chat)에 물어보고 Gemini 답변 받기
async function getAiReply(text) {
  try {
    const response = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        symbol: "NVDA"
      })
    });

    const data = await response.json();
    console.log("사용된 모델:", data.model);  // 어떤 모델이 답했는지 확인
    return data.reply;

  } catch (error) {
    console.log("채팅 에러:", error);
    return "서버와 연결할 수 없어요. 서버가 켜져 있는지 확인해주세요.";
  }
}

// 현재 시간 반환 (예: "14:05")
function getCurrentTime() {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, "0");
  const minutes = String(now.getMinutes()).padStart(2, "0");
  return hours + ":" + minutes;
}

// 📜 채팅 기록 불러오기
async function loadHistory() {
  try {
    const response = await fetch("http://127.0.0.1:8000/chat/history");
    const data = await response.json();
    const history = data.history;

    // 저장된 대화를 하나씩 화면에 그리기
    history.forEach(function (item) {
      // 1. 사용자 질문 말풍선
      const userRow = document.createElement("div");
      userRow.className = "message-row message-row--user";
      userRow.innerHTML =
        '<div class="message message--user">' + item.message + "</div>";
      chatMessages.appendChild(userRow);

      // 2. AI 답변 말풍선 (줄바꿈 변환!)
      const aiRow = document.createElement("div");
      aiRow.className = "message-row message-row--ai";
      aiRow.innerHTML =
        '<div class="message message--ai">' + formatReply(item.reply) + "</div>";  // ✅ 수정!
      chatMessages.appendChild(aiRow);
    });

    scrollToBottom();
    console.log("채팅 기록 불러오기 완료:", history.length + "개");

  } catch (error) {
    console.log("기록 불러오기 실패:", error);
  }
}

// 페이지 열리자마자 기록 불러오기
loadHistory();

// 📝 AI 답변 포맷팅 (마크다운 → HTML 변환)
function formatReply(text) {
  return text
    .replace(/^## (.+)$/gm, '<span class="chat-title">$1</span>')  // ## 제목 → 큰 글씨
    .replace(/\*\*(.+?)\*\*/g, "<b>$1</b>")                        // **글씨** → 굵게
    .replace(/\n/g, "<br>");                                       // 줄바꿈 → <br>
}