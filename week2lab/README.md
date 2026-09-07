# Week 2 Lab GUI (`week2lab/`)

A small web app for the Week 2 data-visualisation lab. **Upload `week2.csv`**
(download it from this GitHub repo first) and work through the three Week 2
charts — **bar chart → histogram → scatter** — as a **guided notebook**: one
cell at a time, exactly like vibe-coding in `W2_S2_data_visualization.ipynb`.

For every code cell you get, **before it runs**:

- the **plain-language explanation** of what the code does (plus pseudocode),
- the **Copilot-style `#` comment** (the prompt you would type),
- the **real Python code** that will run,
- a **multiple-choice check** on your understanding.

Only after you answer do you press **▶ Run cell** — and the output appears
like a Jupyter `Out[n]` block (printed output + chart).

The code that does the analysis is `week2lab/analyze.py` — read it. It was
adapted from the DataGuru recipe pattern (deterministic Python, JSON out),
simplified for GCAP 3226.

> The server does **not** contain a copy of the data — there is no demo mode.
> You must upload the file yourself. That is the point: in Week 2 you practise
> getting `week2.csv` from GitHub and working with **your own copy**.

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

5. **Upload the data**: download `week2.csv` from the repo
   (the GUI has a one-click link) — or use any other CSV — then drag it onto
   the page or click **Choose week2.csv**.

6. Stop the server when done: click in the terminal and press **Ctrl+C**.

> **First time slow?** Codespaces is still installing the Python packages the
> first time you open it. If a chart says imports failed, wait for the setup to
> finish, then restart the server (`Ctrl+C`, run step 3 again).

## What to try

1. Upload `week2.csv` — the same survey you use in
   `W2_S2_data_visualization.ipynb`.
2. Take it one cell at a time: **read the explanation → answer the quick
   check → ▶ Run cell → check the output**, like a notebook. Do **not** skip
   ahead — predicting the output is where the learning happens.
3. The cells mirror the notebook tasks: load → support bar chart (Task 2) →
   distance histogram (Task 3) → scatter distance vs recycling effort
   (Task 4) → the anti-claim check.
4. Save any chart as a PNG when you reach it (like Task 5), then repeat the
   same cells for real in `W2_S2_data_visualization.ipynb`.

## Files

| File | Role |
|---|---|
| `server.py` | Web server (Python standard library only). Routes: `/` (GUI), `/api/health`, `POST /api/analyze` (CSV body required). |
| `analyze.py` | The analysis code behind the scenes: load CSV → pick columns → 3 charts → JSON with base64 PNGs + code + workflow + pseudocode. |
| `static/` | The GUI (HTML/CSS/JS, no build step). |

## Notes

- Everything runs **locally in your browser + Codespace** — no data leaves your
  machine (good for privacy when students use their own data).
- `POST /api/analyze` accepts the raw CSV as the request body
  (`Content-Type: text/csv`). An empty request returns an error asking you to
  upload the file.
