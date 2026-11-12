const rows = document.getElementById("rows");
const statsEl = document.getElementById("stats");

async function load() {
  const [leadsRes, statsRes] = await Promise.all([
    fetch("/api/leads"),
    fetch("/api/stats"),
  ]);
  if (!leadsRes.ok || !statsRes.ok) {
    statsEl.textContent = "CRM API недоступен. Подними сервер: python -m funnel api";
    return;
  }
  const leads = await leadsRes.json();
  const stats = await statsRes.json();

  statsEl.innerHTML = `
    <div class="stat"><b>${stats.leads_total}</b><span>всего</span></div>
    <div class="stat"><b>${stats.leads_new}</b><span>новые</span></div>
    <div class="stat"><b>${stats.leads_qualified}</b><span>qualified</span></div>
  `;

  rows.innerHTML = "";
  if (!leads.length) {
    rows.innerHTML = `<tr><td colspan="6">Здесь пока пусто. Прогони чат на главной или бота.</td></tr>`;
    return;
  }

  for (const lead of leads) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${lead.id}</td>
      <td>${escapeHtml(lead.source)}</td>
      <td>${escapeHtml(lead.name || "—")}</td>
      <td>${escapeHtml(lead.contact)}</td>
      <td>${escapeHtml(lead.interest || lead.summary || "—")}</td>
      <td>
        <select data-id="${lead.id}">
          ${["new", "qualified", "won", "lost", "spam"]
            .map((s) => `<option value="${s}" ${s === lead.status ? "selected" : ""}>${s}</option>`)
            .join("")}
        </select>
      </td>
    `;
    rows.appendChild(tr);
  }

  rows.querySelectorAll("select").forEach((select) => {
    select.addEventListener("change", async () => {
      const id = select.dataset.id;
      const res = await fetch(`/api/leads/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: select.value }),
      });
      if (!res.ok) {
        alert("Статус не сохранился. Проверь API.");
        return;
      }
      await load();
    });
  });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

load();
setInterval(load, 8000);
