// 1. HTML 요소들을 찾아서 변수에 담기
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const chatMessages = document.getElementById("chatMessages");

// 2. 메시지를 화면에 추가하는 함수
function sendMessage() {
  const text = messageInput.value.trim();
  if (text === "") return;

  // --- 사용자 메시지 (줄 전체) ---
  const userRow = document.createElement("div");
  userRow.className = "message-row message-row--user";
  userRow.innerHTML =
    '<span class="message__time">' + getCurrentTime() + "</span>" +
    '<div class="message message--user">' + text + "</div>";
  chatMessages.appendChild(userRow);
  scrollToBottom();

  messageInput.value = "";

  // --- AI 답변 (줄 전체) ---
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

// Enter 키를 누르면 전송
messageInput.addEventListener("keydown", function (e) {
  if (e.key === "Enter") {
    sendMessage();
  }
});

// 3. 전송 버튼 클릭하면 sendMessage 실행
sendBtn.addEventListener("click", sendMessage);

// 채팅창을 맨 아래로 스크롤
function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 사용자 입력에 맞는 AI 답변을 반환
function getAiReply(text) {
  const msg = text.toLowerCase(); // 대소문자 구분 없애기

  if (msg.includes("안녕")) {
    return "안녕하세요! NVDA 주가에 대해 무엇이든 물어보세요.";
  } else if (msg.includes("가격") || msg.includes("주가") || msg.includes("평균")) {
    return "현재 NVDA 평균가는 $205.40입니다.";
  } else if (msg.includes("최고")) {
    return "기간 내 최고가는 $242.10입니다.";
  } else if (msg.includes("최저")) {
    return "기간 내 최저가는 $168.90입니다.";
  } else if (msg.includes("등락") || msg.includes("수익")) {
    return "현재 등락률은 +18.2%입니다.";
  } else {
    return "죄송해요, 아직 학습 중이에요. 곧 답변드릴게요.";
  }
}

// 현재 시간을 "14:05" 형태로 반환
function getCurrentTime() {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, "0");
  const minutes = String(now.getMinutes()).padStart(2, "0");
  return hours + ":" + minutes;
}

