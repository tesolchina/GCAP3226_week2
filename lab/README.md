# Week 2 Lab GUI (`lab/`)

A small web app for the Week 2 data-visualisation lab. Upload the course survey
(or your own CSV) and get the three Week 2 charts instantly — **bar chart →
histogram → scatter** — plus, for every chart:

- the **real Python code that ran** (open it and you can copy it into your notebook),
- the **workflow** (what the code does, step by step),
- the **pseudocode** (the same steps in plain language).

The code that does the analysis is `lab/analyze.py` — read it. It was adapted
from the DataGuru recipe pattern (deterministic Python, JSON out), simplified for
GCAP 3226.

## Run it in your Codespace

```bash
python3 lab/server.py
```

Then open **http://localhost:8123** in your browser (Codespaces shows a
"Forwarded Ports" pop-up — click *Open in Browser*).

That's it: no extra install. The server uses only the Python standard library;
`pandas` and `matplotlib` come from this repo's `requirements.txt`, which your
Codespace already installed (`postCreateCommand`).

## What to try

1. The page auto-runs the demo (`week2.csv`) — the same survey you use in
   `W2_S2_data_visualization.ipynb`.
2. Compare each chart with the notebook tasks:
   - Chart 1 = Task 2 (support bar chart)
   - Chart 2 = Task 3 (distance histogram)
   - Chart 3 = Task 4 (scatter: distance vs recycling effort)
3. Upload your **own** CSV — the GUI picks sensible columns automatically and
   tells you which columns it used.
4. Download any chart as a PNG (like Task 5) and use the code in the notebook.

## Files

| File | Role |
|---|---|
| `server.py` | Web server (Python stdlib only). Routes: `/` (GUI), `/api/health`, `POST /api/analyze` (CSV body, or empty → demo). |
| `analyze.py` | The analysis code behind the scenes: load CSV → pick columns → 3 charts → JSON with base64 PNGs + code + workflow + pseudocode. |
| `static/` | The GUI (HTML/CSS/JS, no build step). |
| `data/week2.csv` | Copy of the demo survey (so the lab also runs standalone). |

## Notes

- Everything runs **locally in your browser + Codespace** — no data leaves your
  machine (unlike hosted tools). Good for privacy when students use their own data.
- `POST /api/analyze` accepts the raw CSV as the request body
  (`Content-Type: text/csv`), or an empty body for the demo dataset.
