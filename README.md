# GCAP3226 — Week 2: GitHub, Codespaces & first plots

**Purpose:** Get every student **lab ready** before Week 3.  

By the end of Week 2 you should be **lab ready**: fork → Codespace → load `week2.csv` → make a plot.

---

## What you will learn

1. What a **repo** is and how to work in **your own copy** on GitHub.  
2. Use **Codespaces** (our online classroom computer).  
3. Load a **CSV from the course folder**.  
4. Make a **first plot** with Python; use **GitHub Copilot** if enabled — and **verify** the result (CILO4).

## Start here: what is a **repo**?

### Repository (**repo**) — plain meaning

A **repo** is a **project folder on the internet** that holds everything for one assignment or one week:

- notebooks (`.ipynb`)
- data files (`.csv`)
- instructions (`README.md`)

**This week’s repo** is named as `GCAP3226_week2`. Your instructor puts materials there; you open it through **your fork** (below).

### Then: GitHub, fork, Codespace

| Word | Plain meaning |
|------|----------------|
| **GitHub** | The website that **hosts** repos — like the platform behind the shared folder. |
| **Fork** (verb) | Click **Fork** to **make your own copy** of the instructor’s repo under **your** GitHub account. |
| **Fork** (noun) | **Your fork** = **your own copy of the course folder** on github.com. You work there; the instructor’s original stays unchanged. |
| **Codespace** | A **classroom computer in the browser** that already has your repo open — you run notebooks there. |
| **Save** (in the notebook) | Keeps your edits on the **Codespace** while it is open (`File → Save`) — like saving a Word doc on the classroom computer you are using. |
| **Commit** | **Stamp this version on the Codespace** — a named snapshot in Git history (e.g. “Finished Week 2 plots”). Still on the Codespace until you Push. |
| **Push** | **Send those stamped versions to your fork (your own copy of the course folder) on github.com** so they are stored online. |


**Analogies**

| Idea | Analogy |
|------|---------|
| **Repo** | One client’s project folder (all assets in one place). |
| **Fork** | Duplicate the folder into **your** drive; you edit your duplicate. |
| **Codespace** | A lab computer that already has the folder open — no USB, no “wrong Desktop path”. |
| **Save** | Save the file on that lab computer. |
| **Commit** | Stamp a named version **on the Codespace** (not yet on github.com). |
| **Push** | Send those stamped versions to **your fork (your own copy of the course folder) on github.com**. |


---

## Class 1 — fork and Codespace

### Step 1 — GitHub account

You should already have a GitHub account from **Week 1** (register, turn on **2FA**, apply for **GitHub Education**).

If you do not have an account yet, create one now at [github.com](https://github.com), then continue.

### Step 2 — Fork the instructor’s Week 2 repo

1. Open the link your instructor shares (e.g. `GCAP3226_week2`).  
2. Click **Fork** (top right) → create under **your** username.  
3. Check the URL: `yourusername/GCAP3226_week2` — **your** name must appear.

You now have **your own repo** — a copy of the course folder.

### Step 3 — Start a Codespace from **your fork**

1. Open **your fork** (not only the instructor’s page).  
2. Click green **Code** → tab **Codespaces** → **Create codespace on main**.  
3. **Wait.** The first time often takes **1–3 minutes** (sometimes longer). The page may show “Setting up your codespace” or a loading screen — this is normal. **Do not** expect it to open instantly; do not keep clicking Create.

GitHub will **automatically name** each Codespace (e.g. `cuddly-sniffle` or similar). You do not choose the name.

**Next time you work:** open the **same** Codespace from **Code → Codespaces** (click its name). Reopening is usually **faster** than the first create, but can still take **under a minute to a few minutes**. Do **not** create a new Codespace every class unless the old one was deleted — a new one may need extensions installed again.

### Step 4 — Open Class 1 notebook

1. Open `W2_S1_github_lab_ready.ipynb`.  
2. Click **Run** on the first cell. When asked to **Select Kernel**:
   - Choose **Python Environments** (not “Jupyter Kernel”, not “Existing Jupyter Server”).
   - Then choose **Python 3.12.x** whose path looks like **`/usr/local/.../python`**  
     (e.g. `/usr/local/bin/python` or `/usr/local/python/3.12.1/bin/python`).
   - **Do not** choose **+ Create Python Environment** (extra setup students do not need).
   - If several “Python 3.12.1” lines appear, they are usually the **same course Python** under different paths — pick one under `/usr/local/` and continue.
3. Run cells from top to bottom.

If Codespace asks to **Install/Enable** Python + Jupyter first, say yes, wait, then:

`Ctrl+Shift+P` (Windows) or `Cmd+Shift+P` (Mac) → type **Reload Window** → Enter → open the notebook again → Select Kernel as above.

### Step 5 — Green-light check (lab ready)

You are **lab ready** when you can:

- `import pandas` and `matplotlib` without error  
- Load `week2.csv` and see `shape`  
- Display at least **one plot**

If you see `FileNotFoundError`: the CSV must come from **the repo in Codespace** — do not paste a path from your laptop.

### Step 6 — GitHub Copilot (if enabled)

Sign in to Copilot in Codespaces. After it suggests code: **run** → **read output** → **edit or reject** if wrong.

---

## Class 2 — data visualization notebook

1. In the **same Codespace** (from **your fork**), open `W2_S2_data_visualization.ipynb`.  
2. Run tasks: support bar chart → distance histogram → scatter → save one figure.  
3. Survey question wording is on the **slides**; column names are in the notebook.  
4. **Save** when you finish (`File → Save`).

---

## Troubleshooting

| Problem | What to do |
|---------|------------|
| `.ipynb` looks like text (actually json) **on the GitHub website** | Do not edit there. Open a **Codespace**, then open the notebook. |
| `.ipynb` looks like text (actually json) **inside Codespace** | Install extensions (see below), then reload. |
| Error: `markdown-it-renderer` / Failed to fetch … notebook-out/index.js | Install **Python** + **Jupyter** + **Jupyter Notebook Renderers**, then **Reload Window** (see below). |
| Prompt: install recommended **Python** extension? | Choose **Yes** (Microsoft). |
| Error: cannot open … notebook editor type `jupyter-notebook` | Install **Jupyter** (Microsoft), Reload Window, then open the file again (see below). Do **not** choose “Open in Text Editor” for class work. |
| `FileNotFoundError` for CSV | Codespace from **your fork**; file must be inside the repo. |
| `ModuleNotFoundError: pandas` (or matplotlib) | Wait until Codespace **finishes building**. Then in the Codespace terminal run: `pip install -r requirements.txt` → **Restart kernel** → run import again. |
| Import error **not** `ModuleNotFoundError` (e.g. connection failed, SSL) | See **Kernel / import errors** below. |
| Opened instructor’s repo by mistake | Open **your fork** (`yourusername/GCAP3226_week2`) and create Codespace there. |
| Lost my Codespace / everything feels new again | You may have created a **new** Codespace. On your fork: **Code → Codespaces** → open the **existing** named one (auto-named, e.g. `cuddly-sniffle`), don’t always click Create. |
| Codespace is “stuck” loading | Wait **a few minutes**; first setup is slow. If it fails after ~5–10 minutes, refresh once or ask a TA — avoid creating many Codespaces in a row. |

### Notebook shows as JSON, or `markdown-it-renderer` error (in Codespace)

1. Click **Extensions** (four squares on the left).  
2. Install (publisher: **Microsoft**):
   - **Python**
   - **Jupyter**
   - **Jupyter Notebook Renderers**  
3. If Codespace asks *Install the recommended Python extension?* → **Yes**.  
4. Press `Ctrl+Shift+P` (Windows) or `Cmd+Shift+P` (Mac) → run **Developer: Reload Window**.  
5. Close the notebook tab → open `W2_S1_github_lab_ready.ipynb` again.  
6. If it is still JSON: right-click the file → **Open With…** → **Jupyter Notebook**.  
7. Still broken? `Ctrl/Cmd+Shift+P` → **Codespaces: Rebuild Container** (wait a few minutes), then try steps 5–6 again.

### Error: cannot open resource with notebook editor type `jupyter-notebook`

1. Click **Cancel** (do **not** use **Open in Text Editor** for labs).  
2. Extensions → install **Jupyter** (Microsoft). Also install **Python** and **Jupyter Notebook Renderers** if missing.  
3. Wait until status bar shows extensions finished installing.  
4. `Ctrl/Cmd+Shift+P` → **Developer: Reload Window**.  
5. Open the `.ipynb` again.  
6. If still blocked: `Ctrl/Cmd+Shift+P` → **Codespaces: Rebuild Container**.

| Confused by many Python 3.12 options when selecting kernel | Choose **Python Environments** → a **Python 3.12** under **`/usr/local/`**. Skip **Create Python Environment**. See below. |

### Where is “Reload Window”?

1. Press **`Ctrl+Shift+P`** (Windows/Linux) or **`Cmd+Shift+P`** (Mac).  
2. A search box appears at the top.  
3. Type **`Reload Window`**.  
4. Click **Developer: Reload Window**.

There is usually **no** big “Reload” button on the screen — it is always via this command palette.

### Select Kernel — what students usually see

**First screen (3 choices):**

| Option | What to do |
|--------|------------|
| **Python Environments** | **Choose this** (normal for our course). |
| **Jupyter Kernel** | Skip unless an instructor tells you otherwise. |
| **Existing Jupyter Server** | Skip (advanced; not for this class). |

**Second screen (several Pythons):**

| Option | What to do |
|--------|------------|
| **+ Create Python Environment** | **Do not choose** — creates a new empty environment; packages may be missing. |
| **Python 3.12.x … `/usr/local/...`** | **Choose this** (any `/usr/local/` Python 3.12 line is fine). |
| **Python 3.12.x … `~/.python/current/...`** | Also OK if `/usr/local/` is not listed; often the same Codespace Python. |

Why so many? Codespace lists **every Python it finds**. They look different but often point to the **same** course setup. Students will see this; it is normal.

After choosing, Run again. If `import pandas` fails, run `pip install -r requirements.txt` in the terminal, then **Restart Kernel** and retry.


---

## Optional — Commit and Push (backup on GitHub)

Not required for most Week 2 work.

Remember: **Commit** = stamp this version on the Codespace; **Push** = send those stamped versions to your fork (your own copy of the course folder) on github.com. Commit alone does **not** update the GitHub website.

1. **Save** the notebook.  
2. **Source Control** (branch icon, left sidebar) → **+** to stage your file.  
3. Write a message → **Commit** (stamp on Codespace) → **Sync / Push** (send to github.com).  
4. Refresh **your fork** on github.com — you should see the update only after Push.

You only push to **your fork**, never the instructor’s original repo.
---

## Optional — Week 2 Lab GUI (make the three charts without typing code)

There is also a small **web GUI** in the `week2lab/` folder. It makes the same
three charts as this notebook (support bar → distance histogram → scatter) from
a CSV you upload — and, for each chart, shows you the **real Python code that
ran**, the **workflow**, and the **pseudocode**. Useful for checking your own
notebook output and for trying your own CSV.

### Run it in your Codespace (3 steps)

1. **Open a terminal**: `Terminal → New Terminal` (bottom panel).
2. **Start the lab**:

   ```bash
   python3 week2lab/server.py
   ```

   You should see: `Week 2 Lab GUI → http://localhost:8123`

3. **Open in browser**: Codespaces shows *"Your application running on port
   8123 is available"* → click **Open in Browser**. No pop-up? Click the
   **Ports** tab in the bottom panel → find **8123** → click the 🌐 icon.

4. **Upload the data**: in the lab page, click **Download week2.csv from the
   repo** (or use your own CSV), then drag the file onto the page or click
   **Choose week2.csv**.

5. **Work through the guided notebook**: the lab takes you through the code
   **one cell at a time** — read the explanation, answer the quick-check
   question, then press **▶ Run cell** to see the output, just like vibe-coding
   in your notebook. Do not skip ahead!

Stop it when done: click the terminal and press **Ctrl+C**.

> **Trouble?** Wait for the first-time setup to finish (`pip install …` runs
> automatically). If a chart says imports failed, restart the server:
> `Ctrl+C`, then run step 2 again.

Full details: [`week2lab/README.md`](week2lab/README.md). The analysis code is
`week2lab/analyze.py` — read it to see what the GUI does.

---

## Next week (Week 3)

Fork the **Week 3 repo** → Codespace → regression notebooks.  
Week 3 assumes you already know **repo, fork, and Codespace** — it will not re-teach from scratch.
