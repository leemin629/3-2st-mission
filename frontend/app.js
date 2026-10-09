let currentSymbol = "NVDA", priceChart = null, sending = false, editingId = null;
let popupLevel = 1000;
const $ = id => document.getElementById(id);
const chatMessages = $("chatMessages");
function escapeHTML(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));
}
function formatReply(text) {
  return escapeHTML(text).replace(/^## (.+)$/gm, '<b>$1</b>').replace(/\*\*(.+?)\*\*/g, '<b>$1</b>').replace(/\n/g, '<br>');
}
async function request(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) {
    const detail = typeof data.detail === "string" ? data.detail : "입력값 또는 서버 상태를 확인해 주세요.";
    throw new Error(detail);
  }
  return data;
}
function jsonRequest(method, body) { return {method, headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)}; }
function tableStatus(id, columns, text) { $(id).innerHTML = `<tr><td colspan="${columns}">${escapeHTML(text)}</td></tr>`; }
function scrollToBottom() { chatMessages.scrollTop = chatMessages.scrollHeight; }
function messageRow(kind, text, time = "") {
  const row = document.createElement("div");
  row.className = `message-row message-row--${kind}`;
  row.innerHTML = `<div class="message message--${kind}">${formatReply(text)}</div><span class="message__time">${escapeHTML(time)}</span>`;
  return row;
}
function clearSummary() {
  document.querySelectorAll(".summary .card__value").forEach(el => {el.textContent = "-"; el.style.color = "";});
}
async function loadStock(symbol = currentSymbol) {
  try {
    const data = await request(`/api/data/summary?symbol=${symbol}`);
    if (symbol !== currentSymbol) return;
    clearSummary();
    if (!data.count) { $("dataStatus").textContent = data.message || "저장 데이터가 없습니다."; return; }
    const values = [data.average_price, data.current_price, data.high_price, data.low_price, data.change_percent];
    document.querySelectorAll(".summary .card__value").forEach((el, i) => {
      el.textContent = i === 4 ? `${values[i] > 0 ? "+" : ""}${values[i].toFixed(2)}%` : `$${values[i].toFixed(2)}`;
      if (i > 0) {
        const difference = i === 4 ? values[i] : values[i] - data.average_price;
        el.style.color = difference > 0 ? "#e53935" : difference < 0 ? "#1e88e5" : "#757575";
        if (difference !== 0) el.textContent += difference > 0 ? " ▲" : " ▼";
        el.title = i === 4 ? "기간 첫 가격 대비 변화율" : "저장 기간 평균가 대비 높음/낮음";
      }
    });
    $("dataStatus").textContent = `${symbol} 저장 데이터: ${data.start_date} ~ ${data.end_date} (${data.count}개). 실시간 시세가 아닙니다. 등락률은 기간 첫 가격 대비입니다.`;
  } catch (err) { if (symbol === currentSymbol) {clearSummary(); $("dataStatus").textContent = `요약 조회 실패: ${err.message}`;} }
}
async function loadChart(symbol = currentSymbol) {
  try {
    const data = await request(`/api/data/history?symbol=${symbol}`);
    if (symbol !== currentSymbol) return;
    if (priceChart) { priceChart.destroy(); priceChart = null; }
    if (typeof Chart === "undefined") throw new Error("차트 라이브러리를 불러오지 못했습니다.");
    const color = document.body.classList.contains("dark") ? "#ddd" : "#333";
    priceChart = new Chart($("priceChart"), {type:"line", data:{labels:data.dates, datasets:[{label:symbol+" 저장 종가",data:data.prices,borderColor:"#4f7cff",pointRadius:0,tension:0.3}]}, options:{responsive:true,plugins:{legend:{display:false}},scales:{x:{ticks:{color}},y:{ticks:{color}}}}});
    $("chartStatus").textContent = data.dates.length ? "" : "차트에 표시할 데이터가 없습니다.";
  } catch (err) { if(symbol === currentSymbol) $("chartStatus").textContent = err.message; }
}
function selectStock(symbol) {
  currentSymbol = symbol;
  document.querySelectorAll(".stock-buttons button").forEach(btn => btn.classList.toggle("active", btn.dataset.symbol === symbol));
  resetForm(); clearSummary();
  if(priceChart) {priceChart.destroy(); priceChart = null;}
  $("dataStatus").textContent = "불러오는 중...";
  loadStock(symbol); loadChart(symbol); loadDataList();
}
async function refreshData() { await Promise.all([loadDataList(), loadStock(), loadChart()]); }
function showPopup(id) {
  const box = $(id);
  box.classList.remove(id === "chatBox" ? "chat--hidden" : "data-manage--hidden");
  box.style.zIndex = ++popupLevel;
}
function closePopup(id) {
  const box = $(id);
  box.classList.add(id === "chatBox" ? "chat--hidden" : "data-manage--hidden");
  box.style.left = ""; box.style.top = ""; box.style.transform = "";
}
for (const [toggle, close, box, load] of [
  ["chatToggleBtn", "chatCloseBtn", "chatBox", () => scrollToBottom()],
  ["dataToggleBtn", "dataCloseBtn", "dataBox", loadDataList],
  ["convToggleBtn", "convCloseBtn", "convBox", loadConversations]
]) {
  $(toggle).addEventListener("click", () => {showPopup(box); load();});
  $(close).addEventListener("click", () => closePopup(box));
  $(box).addEventListener("pointerdown", () => {$(box).style.zIndex = ++popupLevel;});
  makeDraggable($(box), $(box).querySelector(".chat__header, .data-manage__header"));
}
function makeDraggable(box, header) {
  let start = null;
  header.addEventListener("pointerdown", e => {
    if(e.target.closest("button") || e.button !== 0) return;
    const rect = box.getBoundingClientRect();
    start = {x:e.clientX - rect.left, y:e.clientY - rect.top};
    box.style.transform = "none"; box.style.left = `${rect.left}px`; box.style.top = `${rect.top}px`;
    header.setPointerCapture(e.pointerId);
  });
  header.addEventListener("pointermove", e => {
    if(!start) return;
    box.style.left = `${Math.max(0, Math.min(window.innerWidth - box.offsetWidth, e.clientX - start.x))}px`;
    box.style.top = `${Math.max(0, Math.min(window.innerHeight - header.offsetHeight, e.clientY - start.y))}px`;
  });
  header.addEventListener("pointerup", () => {start = null;});
  header.addEventListener("pointercancel", () => {start = null;});
}
async function sendMessage() {
  const text = $("messageInput").value.trim();
  if(sending || !text) return;
  if(text.length > 500) {alert("메시지는 최대 500자입니다."); return;}
  sending = true; $("sendBtn").disabled = true; $("newChatBtn").disabled = true;
  chatMessages.appendChild(messageRow("user", text));
  $("messageInput").value = "";
  const loading = messageRow("ai", "답변을 기다리는 중...");
  chatMessages.appendChild(loading); scrollToBottom();
  try {
    const data = await request("/chat", jsonRequest("POST", {message:text, symbol:currentSymbol}));
    loading.replaceWith(messageRow("ai", data.reply + (data.saved === false ? "\n※ 답변은 받았지만 기록 저장에 실패했습니다." : "")));
    if(!$("convBox").classList.contains("data-manage--hidden")) loadConversations();
  } catch (err) {loading.replaceWith(messageRow("ai", `답변 실패: ${err.message}`));}
  finally {sending = false; $("sendBtn").disabled = false; $("newChatBtn").disabled = false; scrollToBottom();}
}
$("sendBtn").addEventListener("click", sendMessage);
$("messageInput").addEventListener("keydown", e => {if(e.key === "Enter" && !e.isComposing) {e.preventDefault(); sendMessage();}});
$("newChatBtn").addEventListener("click", () => {
  if(sending || !confirm("새 대화를 시작할까요? 기존 기록은 유지됩니다.")) return;
  chatMessages.replaceChildren(messageRow("ai", "안녕하세요. 선택한 종목의 저장 데이터를 바탕으로 질문해 주세요."));
});
async function loadHistory() {
  try {
    const data = await request("/chat/history");
    if(chatMessages.children.length > 1 || sending) return;
    for(const item of data.history) {chatMessages.appendChild(messageRow("user", item.message, formatDate(item.created_at)));chatMessages.appendChild(messageRow("ai", item.reply));}
    scrollToBottom();
  } catch(err) {chatMessages.appendChild(messageRow("ai", `기록 조회 실패: ${err.message}`));}
}
function formatDate(value) {
  if(!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "-" : date.toLocaleString("ko-KR");
}
function conversationStatus(text) {
  const note = document.createElement("p");
  note.className = "conversation-empty"; note.textContent = text;
  $("convTableBody").replaceChildren(note);
}
async function loadConversations() {
  conversationStatus("불러오는 중...");
  $("convCount").textContent = "";
  try {
    const list = await request("/api/conversations");
    $("convTableBody").replaceChildren();
    $("convCount").textContent = `${list.length}개`;
    if(!list.length) return conversationStatus("저장된 대화가 없습니다.");
    for(const item of list) {
      const card = document.createElement("article"); card.className = "conversation-card";
      const open = document.createElement("button"); open.className = "conversation-open";
      open.type = "button";
      const meta = document.createElement("span"); meta.className = "conversation-meta";
      meta.textContent = `${formatDate(item.created_at)}${item.symbol ? " · " + item.symbol : ""}`;
      const question = document.createElement("strong"); question.className = "conversation-question";
      question.textContent = item.message || "질문 없음";
      const preview = document.createElement("span"); preview.className = "conversation-preview";
      preview.textContent = String(item.reply || "답변 없음").replace(/^#+\s*/gm, "").replace(/\*\*/g, "");
      open.append(meta, question, preview);
      open.setAttribute("aria-label", `대화 열기: ${item.message || "질문 없음"}`);
      open.addEventListener("click", () => openConversation(item.id));
      const del = document.createElement("button"); del.type = "button";
      del.className = "conversation-delete"; del.textContent = "삭제";
      del.setAttribute("aria-label", `대화 삭제: ${item.message || "질문 없음"}`);
      del.addEventListener("click", () => deleteConversation(item.id));
      card.append(open, del); $("convTableBody").appendChild(card);
    }
  } catch(err) {conversationStatus(`대화 조회 실패: ${err.message}`);}
}
async function openConversation(id) {
  if(sending) {alert("AI 답변이 끝난 후 기록을 열어 주세요."); return;}
  try {
    const item = await request(`/api/conversations/${encodeURIComponent(id)}`);
    chatMessages.replaceChildren(messageRow("user", item.message, formatDate(item.created_at)), messageRow("ai", item.reply));
    closePopup("convBox"); showPopup("chatBox"); scrollToBottom();
  } catch(err) {alert(err.message);}
}
async function deleteConversation(id) {
  if(!confirm("이 대화를 삭제할까요?")) return;
  try {await request(`/api/conversations/${encodeURIComponent(id)}`, {method:"DELETE"}); await loadConversations();}
  catch(err) {alert(`삭제 실패: ${err.message}`);}
}
function resetForm() {
  editingId = null; $("dataForm").reset(); $("dataSymbol").value = currentSymbol;
  $("dataSubmitBtn").textContent = "추가"; $("dataCancelBtn").hidden = true;
}
async function loadDataList() {
  const symbol = currentSymbol;
  tableStatus("dataTableBody", 5, "불러오는 중...");
  try {
    const list = await request(`/api/data?symbol=${symbol}`);
    if(symbol !== currentSymbol) return;
    $("dataTableBody").replaceChildren();
    if(!list.length) return tableStatus("dataTableBody", 5, "데이터가 없습니다.");
    for(const item of list) {
      const row = document.createElement("tr");
      for(const value of [item.symbol, item.date, `$${item.value}`, item.memo]) {
        const cell = document.createElement("td"); cell.textContent = value || "-"; row.appendChild(cell);
      }
      const actions = document.createElement("td");
      const edit = document.createElement("button"); edit.textContent = "수정";
      edit.addEventListener("click", () => {
        editingId = item.id;
        for(const [id, value] of [["dataSymbol",item.symbol],["dataDate",item.date],["dataValue",item.value],["dataMemo",item.memo]]) $(id).value = value || "";
        $("dataSubmitBtn").textContent = "저장"; $("dataCancelBtn").hidden = false; $("dataMemo").focus();
      });
      const del = document.createElement("button"); del.textContent = "삭제";
      del.addEventListener("click", async () => {
        if(!confirm("이 데이터를 삭제할까요?")) return;
        try {await request(`/api/data/${encodeURIComponent(item.id)}`, {method:"DELETE"}); if(editingId === item.id) resetForm(); await refreshData();}
        catch(err) {alert(`삭제 실패: ${err.message}`);}
      });
      actions.append(edit, del); row.appendChild(actions); $("dataTableBody").appendChild(row);
    }
  } catch(err) {if(symbol === currentSymbol) tableStatus("dataTableBody", 5, `조회 실패: ${err.message}`);}
}
$("dataCancelBtn").addEventListener("click", resetForm);
$("dataForm").addEventListener("submit", async e => {
  e.preventDefault();
  const body = {symbol:$("dataSymbol").value,date:$("dataDate").value,value:Number($("dataValue").value),memo:$("dataMemo").value};
  $("dataSubmitBtn").disabled = true;
  try {
    await request(editingId ? `/api/data/${encodeURIComponent(editingId)}` : "/api/data", jsonRequest(editingId ? "PUT" : "POST", body));
    resetForm(); await refreshData();
  } catch(err) {alert(`저장 실패: ${err.message}`);}
  finally {$("dataSubmitBtn").disabled = false;}
});
$("syncBtn").addEventListener("click", async () => {
  const symbol = currentSymbol;
  $("syncBtn").disabled = true; $("syncStatus").textContent = `${symbol} 갱신 중...`;
  try {
    const data = await request(`/api/stocks/${symbol}/sync`, {method:"POST"});
    $("syncStatus").textContent = `${symbol}: ${data.added}개 추가, 제공된 마지막 거래일 ${data.latest_date}`;
    await refreshData();
  } catch(err) {$("syncStatus").textContent = `갱신 실패: ${err.message}`;}
  finally {$("syncBtn").disabled = false;}
});
function updateDarkBtn() {$("darkBtn").textContent = document.body.classList.contains("dark") ? "☀️ 라이트모드" : "🌙 다크모드";}
try {if(localStorage.getItem("darkMode") === "true") document.body.classList.add("dark");} catch (_) {}
$("darkBtn").addEventListener("click", () => {
  document.body.classList.toggle("dark");
  try {localStorage.setItem("darkMode", document.body.classList.contains("dark"));} catch (_) {}
  updateDarkBtn(); loadChart();
});
updateDarkBtn(); resetForm(); loadStock(); loadChart(); loadHistory();
