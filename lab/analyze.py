#!/usr/bin/env python3
"""analyze.py — the code that runs "behind the scenes" in the Week 2 Lab GUI.

Given a CSV (the default is the Week 2 survey, week2.csv), this script:
  1. loads the data with pandas
  2. chooses sensible columns (support question, distance, recycling effort)
  3. makes the three Week 2 charts (bar · histogram · scatter)
  4. returns one JSON object: chart images (base64 PNG) + summary stats +
     the exact code that produced each chart + workflow + pseudocode.

Design note: this is deliberately borrowed from the DataGuru "Mode A recipe"
pattern (tesolchina/dataguru — deterministic Python, JSON out, no LLM), then
simplified for the GCAP 3226 Week 2 lab. Every chart is drawn by running the
very code string that is shown to students, so "what you see is what ran".

Run directly (prints JSON to stdout):
    python3 analyze.py path/to/data.csv
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
# Chart code builders
# --------------------------------------------------------------------------
# Each builder returns (code_string, namespace). The server (or this script)
# executes code_string inside namespace to produce the figure — the code shown
# to students is literally the code that ran.

BAR_SUPPORT_CODE = """\
# --- Chart 1 · Bar chart of the support question (categorical) ---
import matplotlib.pyplot as plt
import pandas as pd

counts = df[{col!r}].value_counts().sort_index()
print(counts)

fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(counts.index.astype(str), counts.values, color="steelblue")
ax.set_xlabel({xlabel!r})
ax.set_ylabel("Count")
ax.set_title({title!r})
ax.set_ylim(0, counts.max() * 1.15)
plt.tight_layout()
"""

HISTOGRAM_CODE = """\
# --- Chart 2 · Histogram of a continuous column ---
import matplotlib.pyplot as plt
import pandas as pd

print(df[{col!r}].describe())

fig, ax = plt.subplots(figsize=(6, 4))
ax.hist(df[{col!r}].dropna(), bins=15, color="seagreen", edgecolor="white")
ax.set_xlabel({xlabel!r})
ax.set_ylabel("Count")
ax.set_title({title!r})
plt.tight_layout()
"""

SCATTER_CODE = """\
# --- Chart 3 · Scatter: relationship between two columns ---
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
    """Execute chart code in a namespace; return (fig, code, printed).
    The namespace carries df + column choices; exec'ing in the *same*
    namespace the template was formatted from guarantees the shown code
    is exactly the code that ran. The code's own print() output is
    captured (not mixed into the JSON the server returns)."""
    ns = ns or {}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(code, ns)  # noqa: S102 — code is our own fixed string, never user input
    return ns["fig"], code, buf.getvalue()


def _fig_to_png(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110)
    buf.seek(0)
    return "data:image/png;base64," + base64.b64encode(buf.read()).decode("ascii")


# --------------------------------------------------------------------------
# Column picking (works on week2.csv AND on a student's own CSV)
# --------------------------------------------------------------------------

def _find(df, exact, contains=(), prefer_low_card=True, max_card=None):
    """Find a column by exact name, then by substring; None if absent."""
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
    """Return dict with support / numeric / outcome column choices + notes."""
    notes: list[str] = []

    support = _find(df, ("support_info", "support", "attitude", "opinion"),
                    contains=("support", "attitude"), max_card=12)

    numeric = _find(df, ("distance_artificial", "distance", "dist_m", "distance_m"),
                    contains=("distance",))
    if numeric is None:
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        num_cols = [c for c in num_cols if df[c].nunique(dropna=True) >= 5]
        if num_cols:
            numeric = num_cols[0]
            notes.append(f"No distance column found — used first continuous column '{numeric}'.")

    outcome = _find(df, ("recycling_effort", "effort", "recycle_frequency", "frequency"),
                    contains=("effort", "frequency", "recycle"), max_card=9)
    if outcome is None and numeric is not None:
        int_like = [c for c in df.columns
                    if c != numeric and pd.api.types.is_numeric_dtype(df[c])
                    and df[c].nunique(dropna=True) <= 9 and c != support]
        if int_like:
            outcome = int_like[0]
            notes.append(f"No recycling-effort column found — used '{outcome}' for the relationship chart.")

    if support is None:
        support = outcome
        notes.append("No support-style question found — bar chart shows the lowest-cardinality column used.")
    return {
        "support": support,
        "numeric": numeric,
        "outcome": outcome,
        "notes": notes,
    }


# --------------------------------------------------------------------------
# Support labels (Week 2 survey wording)
# --------------------------------------------------------------------------

SUPPORT_LABELS = {
    1: "1 Strongly oppose",
    2: "2 Oppose",
    3: "3 Neutral",
    4: "4 Support",
    5: "5 Strongly support",
}


def _axis_label(col: str) -> str:
    """Human-readable axis label for a known Week 2 column."""
    if col and "distance" in col.lower():
        return "Distance to nearest recycling facility (m)"
    if col and "support" in col.lower():
        return "Support level (1–5)"
    if col and "effort" in col.lower():
        return "Recycling effort (1–4)"
    return str(col)


# --------------------------------------------------------------------------
# Workflow + pseudocode cards (plain language for students)
# --------------------------------------------------------------------------

WORKFLOW_BAR = [
    "Read the CSV with pandas — pandas is Python's spreadsheet tool.",
    "Find the support question column (a category with a few possible answers).",
    "Count how many people chose each answer with value_counts().",
    "Draw one bar per answer — the bar height is the number of people.",
    "Read the chart: which answer is most/least common in this sample?",
]
PSEUDOCODE_BAR = """for each person in the survey:
    find which support level they chose (1–5)
count how many people are in each level
draw one bar per level, height = that count"""

WORKFLOW_HIST = [
    "Take the continuous column (e.g. distance in metres) — many different numbers.",
    "Ask pandas for summary statistics: count, mean, min, max, quartiles.",
    "Group the numbers into 15 bins so the spread is visible.",
    "Draw one bar per bin — the bar height is how many people fall in that range.",
    "Read the chart: are most people near the facility or far from it?",
]
PSEUDOCODE_HIST = """for each person in the survey:
    take their distance (a number)
divide the whole distance range into 15 bins
for each bin:
    count how many people fall inside it
draw one bar per bin, height = that count"""

WORKFLOW_SCATTER = [
    "Put distance on the x-axis (a continuous number).",
    "Put recycling effort on the y-axis (1–4, a small whole number).",
    "Draw one dot per person — jitter spreads overlapping dots slightly.",
    "Look for a pattern: do dots trend up, down, or spread flat?",
    "Remember: a pattern here is association, not proof of cause and effect.",
]
PSEUDOCODE_SCATTER = """for each person in the survey:
    draw one dot at (distance, recycling effort)
    add a tiny random jitter so dots do not hide each other
look at the cloud of dots: any clear direction?"""

CAUTIONS = [
    "These charts describe this sample only — they are not proof about all of Hong Kong.",
    "A scatter pattern does not prove that distance causes less recycling.",
    "Check column meanings and definitions (e.g. how 'distance' was derived) before over-claiming.",
    "Small samples and non-random sampling limit what you can conclude.",
]


# --------------------------------------------------------------------------
# Main analysis
# --------------------------------------------------------------------------

def analyse(path: str, filename: str = "week2.csv") -> dict:
    try:
        df = pd.read_csv(path)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"Could not read CSV: {exc}"}
    if df.empty:
        return {"ok": False, "error": "CSV has no data rows."}

    picked = pick_columns(df)
    support, numeric, outcome = picked["support"], picked["numeric"], picked["outcome"]
    problems = []
    if numeric is None:
        problems.append("No continuous (number) column found — histogram and scatter need one.")
    if support is None and outcome is None:
        problems.append("No low-cardinality category column found — bar chart needs one.")

    charts: list[dict] = []
    try:
        if support is not None:
            is_support = "support" in str(support).lower()
            if is_support and set(df[support].dropna().unique()) <= set(SUPPORT_LABELS):
                xlabel = "Support level (1–5)"
                title = "Support for the policy (survey sample)"
                ns = {"df": df, "col": support, "xlabel": xlabel, "title": title}
            else:
                xlabel = _axis_label(support)
                title = f"Distribution of '{support}'"
                ns = {"df": df, "col": support, "xlabel": xlabel, "title": title}
            fig, code, printed = _render(BAR_SUPPORT_CODE.format(**ns), ns)
            counts = df[support].value_counts().sort_index()
            labels = {str(k): (SUPPORT_LABELS.get(int(k)) or str(k)) for k in counts.index}
            charts.append({
                "id": "support",
                "title": title,
                "column": support,
                "img": _fig_to_png(fig),
                "code": code,
                "output": printed.strip(),
                "workflow": WORKFLOW_BAR,
                "pseudocode": PSEUDOCODE_BAR,
                "read": ("Counts per answer. The tallest bar is the most common answer "
                         "in this sample — a distribution of opinions, not proof a policy works."),
                "table": [{"level": labels.get(str(k), str(k)), "count": int(v)} for k, v in counts.items()],
            })
    except Exception as exc:  # noqa: BLE001
        charts.append({"id": "support", "error": f"Bar chart failed: {exc}"})

    try:
        if numeric is not None:
            is_dist = "distance" in str(numeric).lower()
            xlabel = _axis_label(numeric)
            title = ("Distribution of distance to recycling facility" if is_dist
                     else f"Distribution of '{numeric}'")
            ns = {"df": df, "col": numeric, "xlabel": xlabel, "title": title}
            fig, code, printed = _render(HISTOGRAM_CODE.format(**ns), ns)
            s = df[numeric].describe()
            charts.append({
                "id": "histogram",
                "title": title,
                "column": numeric,
                "img": _fig_to_png(fig),
                "code": code,
                "output": printed.strip(),
                "workflow": WORKFLOW_HIST,
                "pseudocode": PSEUDOCODE_HIST,
                "read": ("The spread of the continuous column. Most values cluster near "
                         "the centre if the bars are tall in the middle and short at the edges."),
                "summary": {k: (round(float(v), 3) if k != "count" else int(v)) for k, v in s.items()},
            })
    except Exception as exc:  # noqa: BLE001
        charts.append({"id": "histogram", "error": f"Histogram failed: {exc}"})

    try:
        if numeric is not None and outcome is not None and outcome != numeric:
            xlabel = _axis_label(numeric)
            ylabel = _axis_label(outcome)
            title = f"{_axis_label(outcome)} vs {_axis_label(numeric)}"
            ns = {"df": df, "x_col": numeric, "y_col": outcome,
                  "xlabel": xlabel, "ylabel": ylabel, "title": title}
            fig, code, printed = _render(SCATTER_CODE.format(**ns), ns)
            charts.append({
                "id": "scatter",
                "title": title,
                "x_column": numeric,
                "y_column": outcome,
                "img": _fig_to_png(fig),
                "code": code,
                "output": printed.strip(),
                "workflow": WORKFLOW_SCATTER,
                "pseudocode": PSEUDOCODE_SCATTER,
                "read": ("One dot per person. If the cloud slopes, the two columns move "
                         "together — an association. It does not prove that one causes the other."),
            })
    except Exception as exc:  # noqa: BLE001
        charts.append({"id": "scatter", "error": f"Scatter failed: {exc}"})

    return {
        "ok": True,
        "dataset": {
            "filename": filename,
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "columnNames": [str(c) for c in df.columns],
        },
        "columnsUsed": picked,
        "problems": problems,
        "charts": charts,
        "cautions": CAUTIONS,
    }


def main() -> None:
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "Usage: python3 analyze.py data.csv"}))
        sys.exit(1)
    print(json.dumps(analyse(sys.argv[1], os.path.basename(sys.argv[1])), ensure_ascii=False))


if __name__ == "__main__":
    main()
