/* Week 2 Lab GUI — guided vibe-coding notebook (vanilla JS).
 * Upload CSV → step through notebook cells one at a time:
 * explain the code → answer a quick check (MC) → run the cell → see output.
 */
"use strict";

const $ = (id) => document.getElementById(id);
const fileInput = $("fileInput");
const drop = $("drop");
const fileHint = $("fileHint");
const note = $("note");
const results = $("results");
const notebookEl = $("notebook");
const progressEl = $("progress");
const problemsEl = $("problems");
const datasetChips = $("datasetChips");

let busy = false;
let state = { steps: [], idx: 0, answered: false, ran: false };
let lastUpload = { text: null, name: null };

/* ---------- health ---------- */
async function health() {
  try {
    const r = await fetch("api/health");
    const j = await r.json();
    if (j.ok) {
      $("healthBadge").textContent = "lab ready";
      $("healthBadge").classList.add("ok");
    }
  } catch {
    $("healthBadge").textContent = "server offline";
  }
}

/* ---------- upload + analyse (CSV body required — no demo) ---------- */
async function analyse(csvText, filename) {
  if (!csvText) {
    note.classList.add("err");
    note.textContent = "Please choose a CSV file first (week2.csv downloaded from the repo).";
    return;
  }
  setBusy(true);
  note.classList.remove("err");
  note.textContent = `Reading ${filename || "your CSV"} …`;
  try {
    const r = await fetch("api/analyze", {
      method: "POST",
      headers: { "Content-Type": "text/csv" },
      body: csvText,
    });
    const j = await r.json();
    if (!j.ok) {
      note.classList.add("err");
      note.textContent = j.error || "Analysis failed.";
      return;
    }
    lastUpload = { text: csvText, name: filename };
    startNotebook(j, filename);
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
  fileInput.disabled = b;
  drop.style.opacity = b ? 0.6 : 1;
}

/* ---------- start / step state ---------- */
function startNotebook(j, filename) {
  results.hidden = false;
  state = { steps: j.steps || [], idx: 0, answered: false, ran: false };
  notebookEl.innerHTML = "";
  datasetChips.innerHTML = "";
  const d = j.dataset || {};
  [`${d.filename || filename}`, `${d.rows} rows`, `${d.columns} columns`]
    .forEach((t) => {
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
  showStep();
}

function showStep() {
  const { steps, idx } = state;
  notebookEl.innerHTML = "";
  const s = steps[idx];
  if (!s) return;
  progressEl.textContent = `Cell ${idx + 1} of ${steps.length}`;
  // history: compact list of completed cells above the active one
  steps.slice(0, idx).forEach((done) => notebookEl.appendChild(doneChip(done, idx)));
  notebookEl.appendChild(buildCell(s, idx));
  notebookEl.scrollIntoView({ behavior: "smooth", block: "start" });
}

function doneChip(step) {
  const div = document.createElement("div");
  div.className = "cell done";
  div.innerHTML = `<span class="tick">✓</span> ${escapeHtml(step.title || "")}`;
  return div;
}

/* ---------- build one cell ---------- */
function buildCell(step, idx) {
  const isMd = step.type === "md";
  const isQ = step.type === "question";
  const wrap = document.createElement("article");
  wrap.className = `cell ${isMd ? "md" : isQ ? "question" : "code"}`;

  const head = document.createElement("div");
  head.className = "cell-head";
  head.innerHTML =
    `<span class="cellid">${isMd ? "✎" : escapeHtml(step.cell || "")}</span>` +
    `<span class="cell-title">${escapeHtml(step.title || "")}</span>`;
  wrap.appendChild(head);

  if (isMd) {
    wrap.appendChild(mdBody(step));
    wrap.appendChild(nextBtn("I've read this — next cell ▸", () => nextStep()));
    return wrap;
  }

  // explanation paragraphs (markdown-lite)
  wrap.appendChild(mdBody(step));

  if (step.pseudo) wrap.appendChild(pseudoBox(step.pseudo));

  if (step.code) {
    wrap.appendChild(promptBox(step.prompt));
    wrap.appendChild(codeBox(step.code));
  }

  const actions = document.createElement("div");
  actions.className = "actions";

  if (step.mc) {
    actions.appendChild(mcBox(step.mc, (correct) => {
      state.answered = true;
      if (step.code) {
        actions.appendChild(runBtn(() => runCell(step, actions, wrap)));
      } else {
        actions.appendChild(nextBtn("Next cell ▸", () => nextStep()));
      }
    }));
  }

  if (!step.code && !step.mc) {
    actions.appendChild(nextBtn("Next cell ▸", () => nextStep()));
  }

  wrap.appendChild(actions);
  return wrap;
}

/* ---------- markdown-lite renderer (bold, code, bullets, paragraphs) ---------- */
function mdBody(step) {
  const box = document.createElement("div");
  box.className = "md-body";
  const raw = Array.isArray(step.md) ? step.md.join("\n\n") : String(step.md || "");
  raw.split(/\n\s*\n/).forEach((block) => {
    if (!block.trim()) return;
    const lines = block.split("\n");
    const isBullets = lines.some((l) => l.trim().startsWith("- "));
    if (isBullets) {
      const ul = document.createElement("ul");
      lines.forEach((line) => {
        const t = line.trim();
        if (!t) return;
        if (t.startsWith("- ")) {
          const li = document.createElement("li");
          li.innerHTML = inlineMd(t.slice(2));
          ul.appendChild(li);
        } else {
          const p = document.createElement("p");
          p.innerHTML = inlineMd(t);
          box.appendChild(p);
        }
      });
      if (ul.children.length) box.appendChild(ul);
    } else {
      const el = document.createElement("p");
      el.innerHTML = inlineMd(block);
      box.appendChild(el);
    }
  });
  return box;
}

function inlineMd(text) {
  let h = escapeHtml(text);
  h = h.replace(/`([^`]+)`/g, "<code>$1</code>");
  h = h.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  h = h.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  return h;
}

function pseudoBox(pseudo) {
  const d = document.createElement("details");
  d.innerHTML = "<summary>Pseudocode — the same steps in plain language</summary>";
  const pre = document.createElement("pre");
  pre.className = "pseudo";
  pre.textContent = pseudo;
  d.appendChild(pre);
  return d;
}

function promptBox(prompt) {
  const d = document.createElement("div");
  d.className = "prompt";
  d.innerHTML = "<span class='plabel'>💬 Copilot prompt (the # comment)</span>";
  const pre = document.createElement("pre");
  pre.textContent = prompt || "";
  d.appendChild(pre);
  return d;
}

function codeBox(code) {
  const d = document.createElement("div");
  d.className = "code-wrap";
  const pre = document.createElement("pre");
  pre.textContent = code; // textContent: exact, safe
  d.appendChild(pre);
  return d;
}

/* ---------- MC widget ---------- */
function mcBox(mc, onAnswered) {
  const box = document.createElement("div");
  box.className = "mc";
  const q = document.createElement("p");
  q.className = "mc-q";
  q.textContent = "❓ " + mc.question;
  box.appendChild(q);

  let picked = -1;
  mc.options.forEach((opt, i) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "opt";
    b.textContent = opt;
    b.addEventListener("click", () => {
      picked = i;
      box.querySelectorAll(".opt").forEach((x) => x.classList.remove("picked"));
      b.classList.add("picked");
      submit.disabled = false;
    });
    box.appendChild(b);
  });

  const submit = document.createElement("button");
  submit.type = "button";
  submit.className = "btn submit";
  submit.textContent = "Check my answer";
  submit.disabled = true;
  submit.addEventListener("click", () => {
    if (picked < 0) return;
    const ok = picked === mc.answer;
    const fb = document.createElement("div");
    fb.className = `feedback ${ok ? "ok" : "bad"}`;
    fb.innerHTML =
      `<strong>${ok ? "✓ Correct" : "✗ Not quite"}</strong> — ${inlineMd(mc.explain || "")}`;
    box.appendChild(fb);
    submit.remove();
    box.querySelectorAll(".opt").forEach((x, i) => {
      x.disabled = true;
      if (i === mc.answer) x.classList.add("right");
      if (i === picked && !ok) x.classList.add("wrong");
    });
    onAnswered(ok);
  });
  box.appendChild(submit);
  return box;
}

/* ---------- run a code cell (notebook-style reveal) ---------- */
function runCell(step, actions, wrap) {
  if (state.ran) return;
  state.ran = true;
  const run = actions.querySelector(".run");
  if (run) run.disabled = true;
  run.textContent = "Running…";
  setTimeout(() => {
    run.textContent = "✓ Cell ran";
    run.style.opacity = 0.7;
    const out = step.output || {};
    const outBox = document.createElement("div");
    outBox.className = "outbox";
    const outLabel = document.createElement("div");
    outLabel.className = "outid";
    outLabel.textContent = (step.cell || "Out").replace("In [", "Out [");
    outBox.appendChild(outLabel);

    if (out.text) {
      const pre = document.createElement("pre");
      pre.className = "out-text";
      pre.textContent = out.text;
      outBox.appendChild(pre);
    }
    if (out.table) {
      const t = document.createElement("table");
      t.innerHTML = "<tr><th>Answer</th><th>People</th></tr>" +
        out.table.map((r) => `<tr><td>${escapeHtml(r.level)}</td><td>${r.count}</td></tr>`).join("");
      outBox.appendChild(t);
    }
    if (out.summary) {
      const t = document.createElement("table");
      t.innerHTML = "<tr><th>Statistic</th><th>Value</th></tr>" +
        Object.entries(out.summary).map(([k, v]) => `<tr><td>${escapeHtml(k)}</td><td>${v}</td></tr>`).join("");
      outBox.appendChild(t);
    }
    if (out.img) {
      const fig = document.createElement("div");
      fig.className = "fig";
      fig.innerHTML = `<img alt="chart output" src="${out.img}">
        <a class="dl" href="${out.img}" download="week2_chart.png">⬇ Save PNG</a>`;
      outBox.appendChild(fig);
    }
    if (step.after) {
      const p = document.createElement("p");
      p.className = "after";
      p.innerHTML = "💡 " + inlineMd(step.after);
      outBox.appendChild(p);
    }
    wrap.appendChild(outBox);
    actions.appendChild(nextBtn("Next cell ▸", () => nextStep()));
  }, 700);
}

/* ---------- buttons ---------- */
function runBtn(fn) {
  const b = document.createElement("button");
  b.type = "button";
  b.className = "btn run";
  b.textContent = "▶ Run cell";
  b.addEventListener("click", fn);
  return b;
}

function nextBtn(label, fn) {
  const b = document.createElement("button");
  b.type = "button";
  b.className = "btn next";
  b.textContent = label;
  b.addEventListener("click", fn);
  return b;
}

function nextStep() {
  state.answered = false;
  state.ran = false;
  state.idx += 1;
  const { steps, idx } = state;
  if (idx >= steps.length) return finishLab();
  showStep();
}

function finishLab() {
  notebookEl.innerHTML = "";
  progressEl.textContent = `Lab complete — all ${state.steps.length} cells done`;
  const card = document.createElement("div");
  card.className = "card done-card";
  card.innerHTML = `<h3>✅ Notebook complete</h3>
    <p>You explained, checked and ran every cell. Now open
    <code>W2_S2_data_visualization.ipynb</code> in your Codespace and repeat the same
    cells for real — then download a PNG and write your 80–100 word reflection.</p>`;
  const restart = document.createElement("button");
  restart.type = "button";
  restart.className = "btn";
  restart.textContent = "↻ Restart the walkthrough";
  restart.addEventListener("click", () => {
    if (lastUpload.text) analyse(lastUpload.text, lastUpload.name);
  });
  card.appendChild(restart);
  notebookEl.appendChild(card);
}

/* ---------- events ---------- */
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

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[ch]);
}

health();
note.textContent = "Upload week2.csv above to start the guided notebook.";
