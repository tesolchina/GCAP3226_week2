# Week 2 Lab GUI (`week2lab/`)

A small web app for the Week 2 data-visualisation lab. Upload the course survey
(or your own CSV) and get the three Week 2 charts instantly — **bar chart →
histogram → scatter** — plus, for every chart:

- the **real Python code that ran** (open it and you can copy it into your notebook),
- the **workflow** (what the code does, step by step),
- the **pseudocode** (the same steps in plain language).

The code that does the analysis is `week2lab/analyze.py` — read it. It was
adapted from the DataGuru recipe pattern (deterministic Python, JSON out),
simplified for GCAP 3226.

## Run it in your Codespace

1. Make sure you are in a **Codespace from your fork** of this repo
   (if you are new: Code → Codespaces → Create codespace on main).
   Wait until setup finishes — `pip install -r requirements.txt` runs
   automatically the first time.
2. Open a terminal: **Terminal → New Terminal**.
3. Start the lab:

   ```bash
   python3 week2lab/server.py
   ```

   You should see:
   `Week 2 Lab GUI → http://localhost:8123`
4. Open the browser: Codespaces usually pops up *"Your application running on
   port 8123 is available"* → click **Open in Browser**.
   No pop-up? Click the **Ports** tab in the bottom panel (or
   **Terminal → Ports**), find **8123**, and click the 🌐 icon.

5. Stop the server when done: click in the terminal and press **Ctrl+C**.

> **First time slow?** Codespaces is still installing the Python packages the
> first time you open it. If `import pandas` fails inside the lab, wait for the
> setup to finish, then restart the server (`Ctrl+C`, run step 3 again).

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
| `server.py` | Web server (Python standard library only). Routes: `/` (GUI), `/api/health`, `POST /api/analyze` (CSV body, or empty → demo). |
| `analyze.py` | The analysis code behind the scenes: load CSV → pick columns → 3 charts → JSON with base64 PNGs + code + workflow + pseudocode. |
| `static/` | The GUI (HTML/CSS/JS, no build step). |
| `data/week2.csv` | Copy of the demo survey (so the lab also runs standalone). |

## Notes

- Everything runs **locally in your browser + Codespace** — no data leaves your
  machine (good for privacy when students use their own data).
- `POST /api/analyze` accepts the raw CSV as the request body
  (`Content-Type: text/csv`), or an empty body for the demo dataset.
