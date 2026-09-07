/* Week 2 Lab GUI — client logic (vanilla JS, mirrors DataGuru's minimal UI). */
"use strict";

const $ = (id) => document.getElementById(id);
const fileInput = $("fileInput");
const drop = $("drop");
const fileHint = $("fileHint");
const note = $("note");
const results = $("results");
const cardsEl = $("cards");
const problemsEl = $("problems");
const cautionsEl = $("cautions");
const datasetChips = $("datasetChips");
const demoBtn = $("demoBtn");

let busy = false;

/* ---------- health ---------- */
async function health() {
  try {
    const r = await fetch("api/health");
    const j = await r.json();
    $("healthBadge").textContent = `demo ready: ${j.demo}`;
    $("healthBadge").classList.add("ok");
  } catch {
    $("healthBadge").textContent = "server offline";
  }
}

/* ---------- run analysis ---------- */
async function analyse(body, filename) {
  setBusy(true);
  note.classList.remove("err");
  note.textContent = `Analysing ${filename || "demo week2.csv"} …`;
  try {
    const r = await fetch("api/analyze", {
      method: "POST",
      headers: body ? { "Content-Type": "text/csv" } : undefined,
      body: body || undefined,
    });
    const j = await r.json();
    render(j, filename);
    note.textContent = "";
  } catch (err) {
    note.classList.add("err");
    note.textContent = `Request failed: ${err.message}`;
  } finally {
    setBusy(false);
  }
}

function setBusy(b) {
  busy = b;
  demoBtn.disabled = b;
  demoBtn.style.opacity = b ? 0.6 : 1;
}

/* ---------- events ---------- */
demoBtn.addEventListener("click", () => analyse(null, "week2.csv"));
fileInput.addEventListener("change", () => {
  const f = fileInput.files && fileInput.files[0];
  if (!f) return;
  fileHint.textContent = f.name;
  const reader = new FileReader();
  reader.onload = () => analyse(reader.result, f.name);
  reader.readAsText(f);
});
["dragenter", "dragover"].forEach((ev) =>
  drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); })
);
["dragleave", "drop"].forEach((ev) =>
  drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); })
);
drop.addEventListener("drop", (e) => {
  const f = e.dataTransfer.files && e.dataTransfer.files[0];
  if (!f) return;
  fileHint.textContent = f.name;
  const reader = new FileReader();
  reader.onload = () => analyse(reader.result, f.name);
  reader.readAsText(f);
});

/* ---------- rendering ---------- */
function render(j, filename) {
  if (!j.ok) {
    note.classList.add("err");
    note.textContent = j.error || "Analysis failed.";
    return;
  }
  results.hidden = false;
  note.textContent = "";

  datasetChips.innerHTML = "";
  const d = j.dataset || {};
  [
    `${d.filename || filename}`, `${d.rows} rows`, `${d.columns} columns`,
    j.columnsUsed && j.columnsUsed.support ? `bar: ${j.columnsUsed.support}` : null,
    j.columnsUsed && j.columnsUsed.numeric ? `histogram: ${j.columnsUsed.numeric}` : null,
    j.columnsUsed && j.columnsUsed.outcome ? `scatter y: ${j.columnsUsed.outcome}` : null,
  ].filter(Boolean).forEach((t) => {
    const s = document.createElement("span");
    s.textContent = t;
    datasetChips.appendChild(s);
  });

  problemsEl.hidden = !(j.problems && j.problems.length);
  problemsEl.innerHTML = "";
  (j.problems || []).forEach((p) => {
    const div = document.createElement("div");
    div.textContent = "⚠ " + p;
    problemsEl.appendChild(div);
  });

  cautionsEl.hidden = !(j.cautions && j.cautions.length);
  cautionsEl.innerHTML = "<h3>Before you over-claim — cautions</h3><ul></ul>";
  const ul = cautionsEl.querySelector("ul");
  (j.cautions || []).forEach((c) => {
    const li = document.createElement("li");
    li.textContent = c;
    ul.appendChild(li);
  });

  cardsEl.innerHTML = "";
  (j.charts || []).forEach((c, i) => cardsEl.appendChild(chartCard(c, i)));
}

function chartCard(c, i) {
  const card = document.createElement("article");
  card.className = "card chart-card";

  if (c.error) {
    card.innerHTML = `<h3>Chart ${i + 1}</h3><p class="chart-err">${c.error}</p>`;
    return card;
  }

  const col = c.x_column ? `${c.y_column} vs ${c.x_column}` : c.column;

  card.innerHTML = `
    <div class="head">
      <div>
        <h3>${i + 1}. ${escapeHtml(c.title)}</h3>
        <p class="read">${escapeHtml(c.read)}</p>
      </div>
      <div style="text-align:right">
        <a class="dl" href="${c.img}" download="week2_chart_${c.id}.png">⬇ PNG</a>
      </div>
    </div>
    <div class="chart-img"><img alt="${escapeHtml(c.title)}" src="${c.img}"></div>
    <details>
      <summary>Code that made this chart (the real Python that ran)</summary>
      <div class="body">
        <pre><code></code></pre>
        ${statsBlock(c)}
      </div>
    </details>
    <details>
      <summary>Workflow — what the code does, step by step</summary>
      <div class="body"><ol class="steps">${(c.workflow || []).map((s) => `<li>${escapeHtml(s)}</li>`).join("")}</ol></div>
    </details>
    <details>
      <summary>Pseudocode — the same steps in plain language</summary>
      <div class="body"><pre><code class="plain">${escapeHtml(c.pseudocode || "")}</code></pre></div>
    </details>`;

  const codeBox = card.querySelector("details .pre code, details pre code");
  const pre = card.querySelector("details .body pre");
  pre.textContent = c.code; // textContent: safe, preserves exact code
  if (c.output) {
    const out = document.createElement("pre");
    out.className = "printed";
    out.textContent = c.output;
    pre.after(out);
  }
  return card;
}

function statsBlock(c) {
  let html = "";
  if (c.table) {
    html += "<h4>Counts</h4><table><tr><th>Answer</th><th>People</th></tr>";
    c.table.forEach((r) => { html += `<tr><td>${escapeHtml(r.level)}</td><td>${r.count}</td></tr>`; });
    html += "</table>";
  }
  if (c.summary) {
    const rows = Object.entries(c.summary).map(([k, v]) =>
      `<tr><td>${escapeHtml(k)}</td><td>${v}</td></tr>`).join("");
    html += `<h4>Summary statistics</h4><table><tr><th>Statistic</th><th>Value</th></tr>${rows}</table>`;
  }
  return html;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[ch]);
}

health();
analyse(null, "week2.csv"); // auto-run the demo so the page is never empty
