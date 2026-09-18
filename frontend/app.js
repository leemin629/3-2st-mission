// 서버에서 받아온 주가를 저장할 변수
let stockData = null;
let priceChart = null;   // 📊 차트 저장용 (추가!)

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
async function loadStock(symbol = "NVDA") {   // ← 종목 받기 (기본값 NVDA)
  try {
    const response = await fetch("http://127.0.0.1:8000/api/data/summary?symbol=" + symbol);  // ← URL에 종목 붙이기!
    const data = await response.json();
    console.log("요약 데이터 받음:", data);

    const avg = data.average_price;  // 평균가 (기준선)

    // ── 평균가 (기본, 색상 없음) ──
    document.querySelector(".summary .card:first-child .card__value")
      .textContent = "$" + data.average_price.toFixed(2);

    // ── 현재가 ──
    const priceEl = document.getElementById("currentPrice");
    priceEl.textContent = "$" + data.current_price.toFixed(2);
    applyColor(priceEl, data.current_price, avg);

    // ── 최고가 ──
    const highEl = document.getElementById("highPrice");
    highEl.textContent = "$" + data.high_price.toFixed(2);
    applyColor(highEl, data.high_price, avg);

    // ── 최저가 ──
    const lowEl = document.getElementById("lowPrice");
    lowEl.textContent = "$" + data.low_price.toFixed(2);
    applyColor(lowEl, data.low_price, avg);

    // ── 등락률 ──
    const changeEl = document.getElementById("changePercent");
    const pct = data.change_percent;
    if (pct > 0) {
      changeEl.textContent = "+" + pct.toFixed(2) + "% ▲";
      changeEl.style.color = "#e53935";
    } else if (pct < 0) {
      changeEl.textContent = pct.toFixed(2) + "% ▼";
      changeEl.style.color = "#1e88e5";
    } else {
      changeEl.textContent = pct.toFixed(2) + "%";
      changeEl.style.color = "#757575";
    }

  } catch (error) {
    console.log("데이터 받기 실패:", error);
  }
}

// 📊 차트 그리기 함수
async function loadChart(symbol = "NVDA") {
  try {
    // 1. 차트 데이터 받아오기 (history API!)
    const response = await fetch("http://127.0.0.1:8000/api/data/history?symbol=" + symbol);
    const data = await response.json();
    console.log("차트 데이터 받음:", data);

    // 2. 도화지(canvas) 찾기
    const ctx = document.getElementById("priceChart");

    // 3. 기존 차트가 있으면 지우기 (종목 바꿀 때 겹침 방지!)
    if (priceChart !== null) {
      priceChart.destroy();
    }

    // 4. 새 차트 그리기!
    priceChart = new Chart(ctx, {
      type: "line",              // 선 그래프
      data: {
        labels: data.dates,      // x축: 날짜
        datasets: [{
          label: symbol + " 주가",
          data: data.prices,     // y축: 가격
          borderColor: "#4f7cff",     // 선 색 (파랑)
          backgroundColor: "rgba(79, 124, 255, 0.1)",  // 아래 채우기
          fill: true,            // 선 아래 채우기
          tension: 0.3,          // 선 부드럽게
          pointRadius: 0         // 점 숨기기 (깔끔!)
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false }   // ← true를 false로! (범례 숨기기!)
        }
      }
    });

  } catch (error) {
    console.log("차트 그리기 실패:", error);
  }
}

// 페이지 열리자마자 실행
loadStock();
loadChart();   // 📊 차트도 그리기! (추가!)

// 🎯 버튼 클릭 시 실행! (종목 바꾸기)
let currentSymbol = "NVDA";  // 현재 선택된 종목 기억

function selectStock(symbol) {
  currentSymbol = symbol;
  loadStock(symbol);
  loadChart(symbol);   // 📊 차트도 바꾸기! (추가!)
  loadDataList();   // 🎯 이 줄 추가!
  // 🎨 모든 버튼에서 active 제거 → 선택한 것만 추가
  document.querySelectorAll(".stock-buttons button").forEach(function (btn) {
    btn.classList.remove("active");
  });
  event.target.classList.add("active");  // 방금 누른 버튼만 강조!

  console.log("선택한 종목:", symbol);
}

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

  scrollToBottom();  // ✅ 이 한 줄 추가! 답변 완성 후 맨 아래로  
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
        symbol: currentSymbol  // ← 선택한 종목으로!
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
      // 1. 사용자 질문 말풍선 (시간 추가!)
      const userRow = document.createElement("div");
      userRow.className = "message-row message-row--user";
      userRow.innerHTML =
        '<span class="message__time">' + item.time + "</span>" +  // ← 시간 추가! ⏰
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

// 🆕 새 대화 버튼 찾기
const newChatBtn = document.getElementById("newChatBtn");

// 🆕 새 대화 시작 (화면만 비우기)
newChatBtn.addEventListener("click", function () {
  // 확인 창 띄우기
  if (!confirm("새 대화를 시작할까요? (기존 기록은 저장돼요)")) {
    return;  // 취소 누르면 아무것도 안 함
  }

  // 채팅창 비우고 → 인사말만 다시 넣기
  chatMessages.innerHTML =
    '<div class="message-row message-row--ai">' +
      '<div class="message message--ai">' +
        '안녕하세요! 주가에 대해 무엇이든 물어보세요. 📈<br>' +
        '(NVDA, AAPL, TSLA, MSFT, GOOGL 지원)' +
      '</div>' +
    '</div>';

  console.log("🆕 새 대화 시작!");});

 // 💬 채팅 열기/닫기 토글!
const chatToggleBtn = document.getElementById("chatToggleBtn");
const chatToggleWrap = document.querySelector(".chat-toggle-wrap");  // 🎯 상자 추가!
const chatBox = document.getElementById("chatBox");

chatToggleBtn.addEventListener("click", function () {
  chatBox.classList.toggle("chat--hidden");

  if (chatBox.classList.contains("chat--hidden")) {
    // 닫힘 → 상자 보이기 (가운데 유지!)
    chatToggleWrap.style.display = "block";   // 🎯 버튼 대신 wrap!
  } else {
    // 열림 → 상자 숨기기 + 창 위치 가운데로!
    chatToggleWrap.style.display = "none";    // 🎯 버튼 대신 wrap!
    chatBox.style.left = "";
    chatBox.style.top = "";
    chatBox.style.transform = "";
    scrollToBottom();
  }
});

// ✕ 창닫기 버튼 (헤더 안!)
const chatCloseBtn = document.getElementById("chatCloseBtn");

chatCloseBtn.addEventListener("click", function () {
  chatBox.classList.add("chat--hidden");
  chatToggleWrap.style.display = "block";   // 🎯 버튼 대신 wrap!
  chatBox.style.left = "";
  chatBox.style.top = "";
  chatBox.style.transform = "";
});

// 🖱️ 채팅창 드래그로 이동하기!
const chatHeader = document.querySelector(".chat__header");  // 헤더 = 손잡이

let isDragging = false;   // 지금 끌고 있나?
let offsetX = 0;          // 마우스와 창의 X 거리
let offsetY = 0;          // 마우스와 창의 Y 거리

// ① 헤더를 눌렀을 때 (드래그 시작!)
chatHeader.addEventListener("mousedown", function (e) {
  // 🎯 버튼(새대화/창닫기) 누를 땐 드래그 안 함!
  if (e.target.closest("button")) return;

  isDragging = true;
  const rect = chatBox.getBoundingClientRect();
  offsetX = e.clientX - rect.left;
  offsetY = e.clientY - rect.top;
  chatBox.style.transform = "none";
});

// ② 마우스 움직일 때 (창 따라오기!)
document.addEventListener("mousemove", function (e) {
  if (!isDragging) return;                        // 안 끌면 무시

  chatBox.style.left = (e.clientX - offsetX) + "px";  // 새 X 위치
  chatBox.style.top = (e.clientY - offsetY) + "px";   // 새 Y 위치
});

// ③ 마우스 뗐을 때 (드래그 끝!)
document.addEventListener("mouseup", function () {
  isDragging = false;
});

// ===== 🗂️ 데이터 관리 팝업 열기/닫기 =====
const dataToggleBtn = document.getElementById("dataToggleBtn");
const dataBox = document.getElementById("dataBox");
const dataCloseBtn = document.getElementById("dataCloseBtn");

// 열기 버튼 클릭
dataToggleBtn.addEventListener("click", () => {
  dataBox.classList.remove("data-manage--hidden");
  loadDataList();  // 열 때 목록 새로고침!
});

// 닫기 버튼 클릭
dataCloseBtn.addEventListener("click", () => {
  dataBox.classList.add("data-manage--hidden");
});

// ===== 🗂️ 데이터 관리 창 드래그 =====
(function makeDataDraggable() {
  const box = document.getElementById("dataBox");
  const header = box.querySelector(".data-manage__header");

  let isDragging = false;
  let offsetX = 0, offsetY = 0;

  header.addEventListener("mousedown", (e) => {
    // 닫기 버튼 누를 땐 드래그 안 함!
    if (e.target.closest(".data-manage__close")) return;

    isDragging = true;

    // 현재 팝업의 실제 위치 계산
    const rect = box.getBoundingClientRect();

    // transform 제거하고 실제 위치로 고정 (중앙정렬 해제!)
    box.style.transform = "none";
    box.style.left = rect.left + "px";
    box.style.top = rect.top + "px";

    // 마우스와 팝업 좌상단의 거리 기억
    offsetX = e.clientX - rect.left;
    offsetY = e.clientY - rect.top;

    header.style.cursor = "grabbing";
  });

  document.addEventListener("mousemove", (e) => {
    if (!isDragging) return;
    // 마우스 따라 이동!
    box.style.left = (e.clientX - offsetX) + "px";
    box.style.top = (e.clientY - offsetY) + "px";
  });

  document.addEventListener("mouseup", () => {
    isDragging = false;
    header.style.cursor = "grab";
  });
})();

// ===== 🗂️ 데이터 관리 (CRUD) =====

const API_BASE = "http://127.0.0.1:8000";  // 배포 시 이 주소만 바꾸면 됨!

// 1️⃣ 목록 불러오기 (GET)
async function loadDataList() {
  try {
    // 🎯 현재 선택된 종목만 요청!
    const res = await fetch(`${API_BASE}/api/data?symbol=${currentSymbol}`);
    const list = await res.json();

    const tbody = document.getElementById("dataTableBody");
    tbody.innerHTML = "";  // 기존 내용 비우기

    if (list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="padding:12px; text-align:center;">데이터가 없습니다</td></tr>`;
      return;
    }

    // 각 데이터를 한 줄씩 그리기
    list.forEach(item => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td style="padding:8px; border:1px solid #ddd;">${item.symbol || "-"}</td>
        <td style="padding:8px; border:1px solid #ddd;">${item.date}</td>
        <td style="padding:8px; border:1px solid #ddd;">$${item.value}</td>
        <td style="padding:8px; border:1px solid #ddd;">${item.memo || "-"}</td>
        <td style="padding:8px; border:1px solid #ddd; text-align:center;">
          <button onclick="deleteData('${item.id}')" style="background:#f44336; color:#fff; border:none; padding:4px 10px; border-radius:4px; cursor:pointer;">🗑️</button>
        </td>
      `;
      tbody.appendChild(row);
    });
  } catch (err) {
    console.error("목록 불러오기 실패:", err);
  }
}

// 2️⃣ 데이터 추가 (POST)
async function addData() {
  const symbol = document.getElementById("dataSymbol").value;
  const date = document.getElementById("dataDate").value;
  const value = parseFloat(document.getElementById("dataValue").value);
  const memo = document.getElementById("dataMemo").value;

  // 간단한 입력 검증
  if (!date || isNaN(value)) {
    alert("날짜와 가격은 필수예요!");
    return;
  }

  try {
    await fetch(`${API_BASE}/api/data`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbol, date, value, memo })
    });

    // 입력창 비우기
    document.getElementById("dataSymbol").value = "";
    document.getElementById("dataDate").value = "";
    document.getElementById("dataValue").value = "";
    document.getElementById("dataMemo").value = "";

    loadDataList();  // 목록 새로고침!
  } catch (err) {
    console.error("추가 실패:", err);
    alert("추가에 실패했어요 🥲");
  }
}

// 3️⃣ 데이터 삭제 (DELETE)
async function deleteData(id) {
  if (!confirm("정말 삭제할까요?")) return;

  try {
    await fetch(`${API_BASE}/api/data/${id}`, { method: "DELETE" });
    loadDataList();  // 목록 새로고침!
  } catch (err) {
    console.error("삭제 실패:", err);
    alert("삭제에 실패했어요 🥲");
  }
}

// 페이지 열리면 바로 목록 불러오기!
loadDataList();