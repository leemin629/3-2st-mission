// 서버에서 받아온 주가를 저장할 변수
let stockData = null;

// 페이지가 열리면 NVDA 주가를 한 번 받아온다
async function loadStock() {
  try {
    const response = await fetch("http://127.0.0.1:8000/stock/NVDA");
    const data = await response.json();
    stockData = data["Global Quote"];

    console.log("주가 데이터 받음:", stockData);

    // 👇 현재가 카드에 진짜 값 넣기
    const priceEl = document.getElementById("currentPrice");
    priceEl.textContent = "$" + Number(stockData["05. price"]).toFixed(2);
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

// 메시지를 화면에 추가하는 함수
function sendMessage() {
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

  // AI 답변
  setTimeout(function () {
    const aiRow = document.createElement("div");
    aiRow.className = "message-row message-row--ai";
    aiRow.innerHTML =
      '<div class="message message--ai">' + getAiReply(text) + "</div>" +
      '<span class="message__time">' + getCurrentTime() + "</span>";
    chatMessages.appendChild(aiRow);
    scrollToBottom();
  }, 500);
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

// AI 답변 반환
function getAiReply(text) {
  const msg = text.toLowerCase();

  if (stockData === null) {
    return "주가 데이터를 불러오는 중이에요. 잠시 후 다시 물어봐 주세요.";
  }

  const price = stockData["05. price"];
  const change = stockData["09. change"];
  const changePercent = stockData["10. change percent"];

  if (msg.includes("안녕")) {
    return "안녕하세요! NVDA 주가에 대해 무엇이든 물어보세요.";
  } else if (msg.includes("가격") || msg.includes("주가") || msg.includes("평균")) {
    return "현재 NVDA 가격은 $" + price + "입니다.";
  } else if (msg.includes("등락") || msg.includes("변동") || msg.includes("수익")) {
    return "변동: " + change + " (" + changePercent + ")";
  } else {
    return "죄송해요, 아직 학습 중이에요. 곧 답변드릴게요.";
  }
}

// 현재 시간 반환 (예: "14:05")
function getCurrentTime() {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, "0");
  const minutes = String(now.getMinutes()).padStart(2, "0");
  return hours + ":" + minutes;
}