const sessionKey = `web:${crypto.randomUUID()}`;
const log = document.getElementById("log");
const form = document.getElementById("chat-form");
const input = document.getElementById("message");
const submitBtn = document.getElementById("submit-lead");
const statusEl = document.getElementById("status");

let lastDraft = null;

function addBubble(role, text) {
  const el = document.createElement("div");
  el.className = `bubble ${role}`;
  el.textContent = text;
  log.appendChild(el);
  log.scrollTop = log.scrollHeight;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) return;
  addBubble("user", message);
  input.value = "";
  statusEl.textContent = "Думаю...";

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_key: sessionKey, message, source: "landing" }),
    });
    if (!res.ok) throw new Error(`chat ${res.status}`);
    const data = await res.json();
    addBubble("bot", data.reply);
    lastDraft = data.draft_lead;
    submitBtn.disabled = !(data.ready_to_submit && data.draft_lead?.contact);
    statusEl.textContent = data.ready_to_submit
      ? "Черновик готов — можно отправить в CRM"
      : "Можно уточнить задачу или добавить контакт";
  } catch (err) {
    statusEl.textContent = "Чат не ответил. Проверь, что API запущен.";
    console.error(err);
  }
});

submitBtn.addEventListener("click", async () => {
  if (!lastDraft?.contact) return;
  statusEl.textContent = "Пишу заявку...";
  try {
    const res = await fetch("/api/leads", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(lastDraft),
    });
    if (!res.ok) throw new Error(`lead ${res.status}`);
    const lead = await res.json();
    statusEl.textContent = `Заявка #${lead.id} в CRM`;
    submitBtn.disabled = true;
    addBubble("bot", `Готово. Заявка #${lead.id} лежит в /crm`);
  } catch (err) {
    statusEl.textContent = "Не удалось сохранить заявку. Обнови страницу и попробуй ещё раз.";
    console.error(err);
  }
});

addBubble(
  "bot",
  "Привет. Я mock-ассистент воронки. Спроси про услуги или напиши «оставь заявку» и контакт."
);
