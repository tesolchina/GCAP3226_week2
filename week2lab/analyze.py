#!/usr/bin/env python3
"""analyze.py — the code that runs "behind the scenes" in the Week 2 Lab GUI.

Given an uploaded CSV (students download week2.csv from the GitHub repo), this
script:

  1. loads the data with pandas
  2. chooses sensible columns (support question, distance, recycling effort)
  3. builds a *guided notebook*: a list of steps that mirror the Week 2 vibe-
     coding flow — each code cell shows the Copilot-style prompt, the code,
     a multiple-choice check, and the output that running the cell produces
     (printed output + chart, exactly like a Jupyter notebook cell).
  4. returns ONE JSON object: { dataset, steps, problems }.

The charts are drawn by executing the very code strings shown to students
("what you see is what ran"), with each step's print() output captured so the
JSON stays clean.

Design notes:
- Adapted from the DataGuru "Mode A recipe" pattern (deterministic Python,
  JSON out, no LLM), simplified for the GCAP 3226 Week 2 lab.
- The GUI reveals steps ONE AT A TIME (explain -> MC -> run -> next cell) to
  simulate running cells in a notebook, instead of dumping everything at once.
"""

from __future__ import annotations

import base64
import contextlib
import io
import json
import os
import sys

import pandas as pd

# Headless charts, always — even when this module is imported from a web-server
# worker thread (matplotlib would otherwise try to start a GUI backend).
import matplotlib  # noqa: E402

matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt  # noqa: E402 — init in main thread; worker exec reuses cache

# --------------------------------------------------------------------------
# The code students see (and that actually runs)
# --------------------------------------------------------------------------

CELL_LOAD_CODE = """\
# --- Week 2 notebook · Cell 1 ---------------------------------------------
# Prompt to Copilot:
#   # Load week2.csv and show its shape
import pandas as pd

df = pd.read_csv("week2.csv")
print("Shape:", df.shape)
"""

CELL_SUPPORT_CODE = """\
# --- Week 2 notebook · Cell 2 ---------------------------------------------
# Prompt to Copilot:
#   # Count the support_info answers and draw a bar chart with labels
counts = df[{support!r}].value_counts().sort_index()
print(counts)

import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(counts.index.astype(str), counts.values, color="steelblue")
ax.set_xlabel({xlabel!r})
ax.set_ylabel("Count")
ax.set_title({title!r})
ax.set_ylim(0, counts.max() * 1.15)
plt.tight_layout()
"""

CELL_HIST_CODE = """\
# --- Week 2 notebook · Cell 3 ---------------------------------------------
# Prompt to Copilot:
#   # Histogram of distance to the recycling facility
print(df[{col!r}].describe())

import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(6, 4))
ax.hist(df[{col!r}].dropna(), bins=15, color="seagreen", edgecolor="white")
ax.set_xlabel({xlabel!r})
ax.set_ylabel("Count")
ax.set_title({title!r})
plt.tight_layout()
"""

CELL_SCATTER_CODE = """\
# --- Week 2 notebook · Cell 4 ---------------------------------------------
# Prompt to Copilot:
#   # Scatter plot of recycling effort vs distance
import matplotlib.pyplot as plt
import pandas as pd

# light jitter so overlapping answers are easier to see
y_jitter = df[{y_col!r}] + (pd.Series(range(len(df))) % 5) * 0.05

fig, ax = plt.subplots(figsize=(6, 4))
ax.scatter(df[{x_col!r}], y_jitter, alpha=0.7)
ax.set_xlabel({xlabel!r})
ax.set_ylabel({ylabel!r})
ax.set_title({title!r})
plt.tight_layout()
"""


def _render(code: str, ns: dict | None = None) -> tuple:
    """Execute code in a namespace; return (fig, code, printed_output)."""
    ns = ns or {}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(code, ns)  # noqa: S102 — code is our own fixed string, never user input
    return ns.get("fig"), code, buf.getvalue()


def _fig_to_png(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110)
    buf.seek(0)
    return "data:image/png;base64," + base64.b64encode(buf.read()).decode("ascii")


# --------------------------------------------------------------------------
# Column picking (works on week2.csv AND on a student's own CSV)
# --------------------------------------------------------------------------

def _find(df, exact, contains=(), max_card=None):
    cols = {str(c).strip().lower(): c for c in df.columns}
    for name in exact:
        if str(name).lower() in cols:
            col = cols[str(name).lower()]
            if max_card is None or df[col].nunique(dropna=True) <= max_card:
                return col
    for part in contains:
        for low, col in cols.items():
            if part in low:
                if max_card is None or df[col].nunique(dropna=True) <= max_card:
                    return col
    return None


def pick_columns(df: pd.DataFrame) -> dict:
    notes: list[str] = []
    support = _find(df, ("support_info", "support", "attitude", "opinion"),
                    contains=("support", "attitude"), max_card=12)
    numeric = _find(df, ("distance_artificial", "distance", "dist_m", "distance_m"),
                    contains=("distance",))
    if numeric is None:
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])
                    and df[c].nunique(dropna=True) >= 5]
        if num_cols:
            numeric = num_cols[0]
            notes.append(f"No distance column found — using continuous column '{numeric}'.")
    outcome = _find(df, ("recycling_effort", "effort", "recycle_frequency", "frequency"),
                    contains=("effort", "frequency", "recycle"), max_card=9)
    if outcome is None and numeric is not None:
        int_like = [c for c in df.columns
                    if c != numeric and pd.api.types.is_numeric_dtype(df[c])
                    and df[c].nunique(dropna=True) <= 9 and c != support]
        if int_like:
            outcome = int_like[0]
            notes.append(f"No recycling-effort column found — using '{outcome}' for the relationship.")
    if support is None:
        support = outcome
        if support is not None:
            notes.append("No support-style question found — bar chart uses the category column found.")
    return {"support": support, "numeric": numeric, "outcome": outcome, "notes": notes}


SUPPORT_LABELS = {
    1: "1 Strongly oppose",
    2: "2 Oppose",
    3: "3 Neutral",
    4: "4 Support",
    5: "5 Strongly support",
}


def _axis_label(col: str) -> str:
    if col and "distance" in col.lower():
        return "Distance to nearest recycling facility (m)"
    if col and "support" in col.lower():
        return "Support level (1–5)"
    if col and "effort" in col.lower():
        return "Recycling effort (1–4)"
    return str(col)


def _mc(question: str, options: list[str], answer: int, explain: str) -> dict:
    return {"question": question, "options": options, "answer": answer, "explain": explain}


# --------------------------------------------------------------------------
# Guided-notebook builders
# --------------------------------------------------------------------------

def build_load_step(rows: int, cols: int, columns: list[str]) -> dict:
    first = ", ".join(str(c) for c in columns[:5])
    return {
        "cell": "In [1]",
        "title": "Load the survey",
        "md": [
            "Every analysis starts the same way: **read the CSV into a pandas DataFrame** "
            "(`df`). A DataFrame is Python's spreadsheet — a table of rows and columns.",
            "Your file has been read from your upload. In your Codespace notebook the code "
            "looks like the cell on the right (the file `week2.csv` lives in the repo).",
        ],
        "prompt": "# Load week2.csv and show its shape",
        "code": CELL_LOAD_CODE,
        "mc": _mc(
            "What does `df.shape` print?",
            ["the number of rows and columns, e.g. (97, 43)",
             "the number of columns and rows, e.g. (43, 97)",
             "the first five rows of the table",
             "the column names"],
            0,
            "`df.shape` is a tuple `(rows, columns)` — here your upload has "
            f"{rows} rows and {cols} columns."),
        "output": {
            "text": f"Shape: ({rows}, {cols})\n\nFirst columns: {first}, …",
            "note": "One row = one survey respondent. "
                    f"{rows} rows × {cols} columns = your data table.",
        },
        "after": (f"Data ready: **{rows} rows × {cols} columns**. Now we vibe-code the first chart."),
    }


def build_vibe_md_step() -> dict:
    return {
        "type": "md",
        "title": "How we will work — the vibe-coding loop",
        "md": [
            "You do **not** type code from memory. You vibe-code with GitHub Copilot:",
            "**1.** You write a plain-English wish as a `#` comment.  "
            "**2.** Copilot writes the Python for you.  "
            "**3.** You **read** the code before running it.  "
            "**4.** You run the cell and **verify** the output looks right (CILO4).",
            "That is exactly what we simulate next — one notebook cell at a time. "
            "Each cell: explain → answer a quick check → press **Run cell**.",
        ],
        "pseudo": "for each cell:\n    read the plain-English comment\n    read the code Copilot wrote\n    answer the quick check\n    run the cell\n    verify the output makes sense",
    }


def build_support_step(df: pd.DataFrame, support: str, chart_idx: int) -> dict:
    is_support = support is not None and "support" in str(support).lower()
    if support is not None and is_support and set(df[support].dropna().unique()) <= set(SUPPORT_LABELS):
        xlabel, title = "Support level (1–5)", "Support for the policy (survey sample)"
    else:
        xlabel, title = _axis_label(support), f"Distribution of '{support}'"
    ns = {"df": df, "support": support, "xlabel": xlabel, "title": title}
    fig, code, printed = _render(CELL_SUPPORT_CODE.format(**ns), ns)
    counts = df[support].value_counts().sort_index()
    table = [{"level": SUPPORT_LABELS.get(int(k), str(k)), "count": int(v)} for k, v in counts.items()]
    return {
        "cell": f"In [{chart_idx}]",
        "title": f"Chart 1 — bar chart of “{support}”",
        "md": [
            "A **categorical** column has a few possible answers (here: support level 1–5). "
            "To summarise it we **count** how many people chose each answer.",
            "Read the code: `value_counts()` counts the answers, `.sort_index()` puts them in "
            "order 1→5, then one **bar** per answer is drawn with height = count.",
        ],
        "pseudo": "count how many people chose each answer\ndraw one bar per answer (1–5)\nbar height = number of people",
        "prompt": "# Count the support_info answers and draw a bar chart with labels",
        "code": code,
        "mc": _mc(
            "What does `df['support_info'].value_counts()` return?",
            ["a count of people for each answer level",
             "the average support level",
             "a sorted list of every person's answer",
             "a bar chart"],
            0,
            "`value_counts()` counts how many rows have each value — one number per answer level. "
            "The chart then turns those counts into bars."),
        "output": {"text": printed.strip(), "table": table, "img": _fig_to_png(fig)},
        "after": "The tallest bar is the most common answer **in this sample** — a distribution "
                 "of opinions, not proof that the policy works.",
    }


def build_hist_step(df: pd.DataFrame, numeric: str, chart_idx: int) -> dict:
    is_dist = "distance" in str(numeric).lower()
    xlabel = _axis_label(numeric)
    title = ("Distribution of distance to recycling facility" if is_dist
             else f"Distribution of '{numeric}'")
    ns = {"df": df, "col": numeric, "xlabel": xlabel, "title": title}
    fig, code, printed = _render(CELL_HIST_CODE.format(**ns), ns)
    s = df[numeric].describe()
    summary = {k: (round(float(v), 3) if k != "count" else int(v)) for k, v in s.items()}
    return {
        "cell": f"In [{chart_idx}]",
        "title": f"Chart 2 — histogram of “{numeric}”",
        "md": [
            "A **continuous** column (like distance in metres) has many different values, so "
            "counting each value is not useful. Instead we look at the **spread**.",
            "Read the code: `describe()` prints summary statistics (count, mean, min, max, "
            "quartiles); the histogram groups the values into 15 bins — bar height = how many "
            "people fall in that range.",
        ],
        "pseudo": "for each person: take their distance (a number)\nsplit the range into 15 bins\nfor each bin: count the people inside it\ndraw one bar per bin",
        "prompt": "# Histogram of distance to the recycling facility",
        "code": code,
        "mc": _mc(
            "Why do we use a histogram here and not a bar chart of every single distance?",
            ["distances are continuous with many values — a histogram shows their spread",
             "bar charts only work for text columns",
             "because Copilot suggested it",
             "a histogram proves cause and effect"],
            0,
            "With dozens of different distances, one bar per value would be unreadable. "
            "Binning into 15 ranges shows where most people are (e.g. close vs far)."),
        "output": {"text": printed.strip(), "summary": summary, "img": _fig_to_png(fig)},
        "after": "Most values cluster near the centre if bars are tall in the middle — read the "
                 "shape before describing it.",
    }


def build_scatter_step(df: pd.DataFrame, numeric: str, outcome: str, chart_idx: int) -> dict:
    xlabel, ylabel = _axis_label(numeric), _axis_label(outcome)
    title = f"{ylabel} vs {xlabel}"
    ns = {"df": df, "x_col": numeric, "y_col": outcome,
          "xlabel": xlabel, "ylabel": ylabel, "title": title}
    fig, code, printed = _render(CELL_SCATTER_CODE.format(**ns), ns)
    return {
        "cell": f"In [{chart_idx}]",
        "title": f"Chart 3 — scatter: “{outcome}” vs “{numeric}”",
        "md": [
            "Now we ask a **relationship** question: do people who live farther from a recycling "
            "facility report more recycling effort?",
            "Read the code: each person is **one dot** at `(distance, effort)`. The tiny jitter "
            "spreads overlapping dots so you can see them.",
        ],
        "pseudo": "for each person: draw one dot at (distance, effort)\nadd a tiny jitter so dots do not hide each other\nlook: does the cloud slope up, down, or flat?",
        "prompt": "# Scatter plot of recycling effort vs distance",
        "code": code,
        "mc": _mc(
            "Looking at a scatter pattern, which statement is SAFE to write?",
            ["“in this sample, the two columns appear related — but this is not proof of cause and effect”",
             "“living farther from a facility causes people to recycle less”",
             "“this proves what all Hong Kong people do”",
             "“we can ignore the data because surveys are never useful”"],
            0,
            "A scatter shows **association in your sample**. It does not prove causation, and "
            "your sample is not the whole population."),
        "output": {"text": printed.strip(), "img": _fig_to_png(fig)},
        "after": "Pattern ≠ proof. Write the cautious version: “appears related in this sample — "
                 "we would not claim distance causes less recycling from this alone.”",
    }


def build_anticlaim_step() -> dict:
    return {
        "type": "question",
        "title": "Quick check — don't over-claim",
        "md": ["Your notebook asks you to write one line: *“We would not claim … because …”*. "
               "Which completion is the most honest?"],
        "mc": _mc(
            "Complete: “We would not claim that distance causes less recycling because …”",
            ["…this is one sample; other factors (habits, facilities) also matter and correlation is not causation",
             "…our charts are probably wrong",
             "…AI wrote the code so we cannot trust it",
             "…we did not use enough colours"],
            0,
            "Exactly — one sample + correlation cannot prove a cause. Naming the reason is the "
            "CILO4 skill your teachers are looking for."),
    }


def build_wrap_step(cautions: list[str]) -> dict:
    bullets = "\n".join(f"- {c}" for c in cautions)
    return {
        "type": "md",
        "title": "Lab complete 🎉",
        "md": [
            "You have vibe-coded four notebook cells: **load → count/bar → histogram → scatter** "
            "— and you can read each line of code before you ran it.",
            "**Try next:** open `W2_S2_data_visualization.ipynb` in this Codespace and repeat "
            "the same cells for real, then download a PNG (Task 5) and write your 80–100 word "
            "reflection (Task 6).",
            "**Before you over-claim — cautions:**",
            bullets,
            "Next week (Week 3) you build a regression on the same survey — same fork + "
            "Codespace workflow.",
        ],
    }


# --------------------------------------------------------------------------
# Main analysis
# --------------------------------------------------------------------------

CAUTIONS = [
    "These charts describe this sample only — not proof about all of Hong Kong.",
    "A scatter pattern does not prove that distance causes less recycling.",
    "Check column meanings/definitions (e.g. how 'distance' was derived) before over-claiming.",
    "Small samples and non-random sampling limit what you can conclude.",
]


def analyse(path: str, filename: str = "week2.csv") -> dict:
    try:
        df = pd.read_csv(path)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"Could not read CSV: {exc}"}
    if df.empty:
        return {"ok": False, "error": "CSV has no data rows."}

    rows, cols = int(len(df)), int(len(df.columns))
    column_names = [str(c) for c in df.columns]
    picked = pick_columns(df)
    support, numeric, outcome = picked["support"], picked["numeric"], picked["outcome"]

    problems = list(picked["notes"])
    if numeric is None:
        problems.append("No continuous (number) column found — chart 2 and 3 will be skipped.")
    if support is None and outcome is None:
        problems.append("No low-cardinality category column found — chart 1 will be skipped.")

    steps: list[dict] = [build_load_step(rows, cols, column_names), build_vibe_md_step()]

    chart_idx = 1  # cell numbering for code cells that run (load was In[1])
    if support is not None:
        chart_idx += 1
        steps.append(build_support_step(df, support, chart_idx))
    if numeric is not None:
        chart_idx += 1
        steps.append(build_hist_step(df, numeric, chart_idx))
    if numeric is not None and outcome is not None and outcome != numeric:
        chart_idx += 1
        steps.append(build_scatter_step(df, numeric, outcome, chart_idx))

    steps.append(build_anticlaim_step())
    steps.append(build_wrap_step(CAUTIONS))

    return {
        "ok": True,
        "dataset": {"filename": filename, "rows": rows, "columns": cols},
        "columnsUsed": picked,
        "problems": problems,
        "steps": steps,
    }


def main() -> None:
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "Usage: python3 analyze.py data.csv"}))
        sys.exit(1)
    print(json.dumps(analyse(sys.argv[1], os.path.basename(sys.argv[1])), ensure_ascii=False))


if __name__ == "__main__":
    main()
