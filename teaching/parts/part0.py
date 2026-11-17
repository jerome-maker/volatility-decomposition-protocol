# -*- coding: utf-8 -*-
"""Unit 0: how to read this notebook, the skill tree, the environment and the data."""
from parts._helpers import bi, code, md, mono

CELLS = [
    mono(
        "# 波動率預測的資訊階梯：技能樹教材\n"
        "# The information ladder in volatility forecasting: a skill-tree tutorial\n\n"
        "本筆記本是論文 *Decomposing deep learning gains in volatility forecasting: "
        "Information, architecture and reproducibility* 的教材與投稿前自我查核。\n\n"
        "This notebook is both the teaching material for the paper above and its "
        "pre-submission self-check.\n\n"
        "---"
    ),
    bi(
        zh=(
            "### 這份教材要做兩件事\n\n"
            "**第一是教學。** 把論文用到的每一項技術排成一棵技能樹，從最基礎的資料建構開始，"
            "一路走到論文自己的方法。每個節點都用四層講：原理、公式、演算法、程式設計邏輯，"
            "而且**全部以本研究的資料為範例**，不用玩具資料。\n\n"
            "**第二是查核。** 稿件報告的每一個數字，都在這裡用資料重新算一次，再和稿件比對，"
            "最後一個單元列出每一項是「重現」「不一致」還是「無法驗證」。\n\n"
            "第二件事是這份教材要在投稿前完成的原因。把一個步驟講清楚，是發現它其實做錯了的最可靠方法；"
            "在這裡發現差異只花一個下午，被審稿人發現則昂貴得多。\n\n"
            "### 怎麼讀\n\n"
            "每個單元開頭會先說**前一個節點做不到什麼**——這是把一串技術變成一個論證的關鍵。"
            "程式碼分兩種：**示範型**讀既有輸出並解讀，**從零實作型**把公式寫成最精簡的程式，"
            "再和套件的結果對照。兩者相符時，讀者就親眼看到公式變成了程式。\n\n"
            "閱讀順序就是單元順序；每個單元的先備節點都排在它前面。"
        ),
        en=(
            "### This notebook does two jobs\n\n"
            "**Teaching.** Every technique the paper uses is placed in a skill tree, from data "
            "construction up to the paper's own method. Each node is taught in four layers — "
            "principle, formulas, algorithm, program logic — and **every worked example uses this "
            "study's own data**, never a toy dataset.\n\n"
            "**Checking.** Every number the manuscript reports is re-derived here from the data and "
            "compared with the manuscript. The last unit lists each one as reproduced, differing, or "
            "not verifiable.\n\n"
            "The second job is why this runs before submission. Explaining a step is the most reliable "
            "way to discover it was done differently from how the paper says; a discrepancy found here "
            "costs an afternoon, the same discrepancy found by a referee costs much more.\n\n"
            "### How to read it\n\n"
            "Each unit opens by naming **what its prerequisite nodes cannot do** — that is what turns a "
            "list of techniques into an argument. Code cells come in two kinds: **demonstration** cells "
            "read existing output and interpret it, **from-scratch** cells turn a formula into the "
            "fewest lines that still show its structure and then reconcile with the library version.\n\n"
            "Read the units in order; every unit's prerequisites come before it."
        ),
    ),
    mono(
        "### 技能樹 / The skill tree\n\n"
        "```text\n"
        "[F1] Realized variance and the forecast target      (N, Table 4.1)\n"
        " |\n"
        " +--[F2] Predictor blocks and collinearity          (Table 4.2)\n"
        " +--[F3] Out-of-sample protocol                     (Table 4.1 split)\n"
        " |    |\n"
        " |    +--[C1] Proxy-robust loss functions           (Table 5.1 QLIKE)\n"
        " |    |    |\n"
        " |    |    +--[C4] Diebold-Mariano with HLN and HAC (Table 5.3)\n"
        " |    |    |    +--[C5] Clark-West for nested models (Section 5.2)\n"
        " |    |    |    +--[C7] Model confidence set         (Section 5.3)\n"
        " |    |    +--[C6] Moving block bootstrap            (Table 5.2 intervals)\n"
        " |    |\n"
        " |    +--[C2] HAR-RV, OLS on log variance           (Table 5.1 L2, L3)\n"
        " |    +--[C3] GARCH(1,1) and GJR-GARCH, Student-t   (Table 5.1 L1)\n"
        " |         |\n"
        " |         +--[K1] Information-set parity, the ladder L0-L4  (Tables 5.1, 5.4, 5.5)\n"
        " |              |\n"
        " |              +--[K2] Three-way decomposition      (Table 5.2, abstract)\n"
        " |              |    +--[R1] Second asset, daily-only set    (Tables 8.1, 8.2)\n"
        " |              |    +--[R2] Reserved hold-out year          (Tables 8.3, 8.4)\n"
        " |              |    +--[R3] Fitting scheme                  (Tables 8.5, 8.6)\n"
        " |              +--[K3] GARCH-X by custom MLE        (Table 5.1 GARCH-X)\n"
        " |              +--[K4] Economic evaluation          (Tables 6.1, 6.2)\n"
        " |              +--[K5] Seeds and version pinning    (Section 7, abstract)\n"
        " |              +--[R4] Block Granger tests and attribution (Tables 9.1, 9.2)\n"
        " |\n"
        "[D1] Reproduction report   [D2] Discrepancies and real bugs\n"
        "```"
    ),
    bi(
        zh=(
            "### 節點對照表\n\n"
            "節點 id 會出現在每個單元的標題，也出現在 `findings.csv` 的 `unit` 欄，"
            "所以每一個稿件數字都能追到負責重現它的單元。\n\n"
            "| id | 中文名稱 | English | 先備 | 重現的結果 |\n"
            "|---|---|---|---|---|\n"
            "| F1 | 已實現變異數與預測目標 | Realized variance and target | — | 樣本數、表 4.1 |\n"
            "| F2 | 預測變數區塊與共線性 | Predictor blocks and collinearity | F1 | 表 4.2 |\n"
            "| F3 | 樣本外評估協定 | Out-of-sample protocol | F1 | 表 4.1 切分 |\n"
            "| C1 | 代理變數穩健損失 | Proxy-robust losses | F1 | 表 5.1 QLIKE |\n"
            "| C2 | HAR-RV 與對數尺度迴歸 | HAR-RV, OLS on log variance | F1, F3 | 表 5.1 L2 L3 |\n"
            "| C3 | GARCH 與 GJR-GARCH | GARCH and GJR-GARCH | F1, F3 | 表 5.1 L1 |\n"
            "| C4 | DM 檢定與 HLN 校正 | Diebold-Mariano with HLN | C1 | 表 5.3 |\n"
            "| C5 | Clark-West 巢狀檢定 | Clark-West for nested models | C4 | 第 5.2 節 |\n"
            "| C6 | 移動區塊拔靴法 | Moving block bootstrap | C1 | 表 5.2 區間 |\n"
            "| C7 | 模型信賴集合 | Model confidence set | C4, C6 | 第 5.3 節 |\n"
            "| K1 | 資訊集合對等與階梯 | Information-set parity | C2, C3 | 表 5.1 5.4 5.5 |\n"
            "| K2 | 三項完全分解 | Three-way decomposition | K1, C4, C6 | 表 5.2、摘要 |\n"
            "| K3 | GARCH-X 自訂最大概似 | GARCH-X by custom MLE | C3, K1 | 表 5.1 GARCH-X |\n"
            "| K4 | 經濟評估 | Economic evaluation | K1 | 表 6.1 6.2 |\n"
            "| K5 | 種子與版本的重現性 | Seeds and version pinning | K1 | 第 7 節、摘要 |\n"
            "| R1 | 第二標的 | Second asset | K2 | 表 8.1 8.2 |\n"
            "| R2 | 保留樣本年 | Reserved hold-out | K2 | 表 8.3 8.4 |\n"
            "| R3 | 配適方案 | Fitting scheme | K2, C2 | 表 8.5 8.6 |\n"
            "| R4 | 區塊 Granger 檢定與歸因 | Block Granger tests | K1 | 表 9.1 9.2 |\n"
        ),
        en=(
            "### Node table\n\n"
            "The node id appears in every unit header and in the `unit` column of `findings.csv`, so "
            "each manuscript number can be traced to the unit that reproduces it. The Chinese names "
            "are in the table above.\n\n"
            "| id | Name | Needs | Reproduces |\n"
            "|---|---|---|---|\n"
            "| F1 | Realized variance and the forecast target | — | sample counts, Table 4.1 |\n"
            "| F2 | Predictor blocks and collinearity | F1 | Table 4.2 discussion |\n"
            "| F3 | Out-of-sample protocol | F1 | Table 4.1 split |\n"
            "| C1 | Proxy-robust loss functions | F1 | Table 5.1 QLIKE |\n"
            "| C2 | HAR-RV, OLS on the log variance | F1, F3 | Table 5.1 levels 2 and 3 |\n"
            "| C3 | GARCH and GJR-GARCH | F1, F3 | Table 5.1 level 1 |\n"
            "| C4 | Diebold-Mariano with the HLN correction | C1 | Table 5.3 |\n"
            "| C5 | Clark-West for nested models | C4 | Section 5.2 |\n"
            "| C6 | Moving block bootstrap | C1 | Table 5.2 intervals |\n"
            "| C7 | Model confidence set | C4, C6 | Section 5.3 |\n"
            "| K1 | Information-set parity and the ladder | C2, C3 | Tables 5.1, 5.4, 5.5 |\n"
            "| K2 | Three-way decomposition | K1, C4, C6 | Table 5.2, abstract |\n"
            "| K3 | GARCH-X by custom maximum likelihood | C3, K1 | Table 5.1 GARCH-X |\n"
            "| K4 | Economic evaluation | K1 | Tables 6.1, 6.2 |\n"
            "| K5 | Seeds and version pinning | K1 | Section 7, abstract |\n"
            "| R1 | Second asset | K2 | Tables 8.1, 8.2 |\n"
            "| R2 | Reserved hold-out year | K2 | Tables 8.3, 8.4 |\n"
            "| R3 | Fitting scheme | K2, C2 | Tables 8.5, 8.6 |\n"
            "| R4 | Block Granger tests and attribution | K1 | Tables 9.1, 9.2 |\n"
        ),
    ),
    bi(
        zh=(
            "### 環境與資料\n\n"
            "這份筆記本只用 numpy、pandas、scipy、statsmodels、arch 與 matplotlib，**不需要 GPU 也不需要 PyTorch**。"
            "原因是：線性模型與 GARCH 的重估都是小規模線性代數與序列相依的最大概似疊代，"
            "搬上 GPU 的傳輸成本高於計算本身；而 Level 4 的神經網路**無法在筆記本裡重訓**"
            "（需要數小時的 GPU 時間），所以它們一律讀既有的預測序列，並在重現報告裡誠實標示。\n\n"
            "資料檔在倉庫的 `data/`，預測序列在 `data/predictions/`。"
            "下面的 `find_dir` 讓這份筆記本在專案資料夾與 GitHub 倉庫兩種位置都能執行。"
        ),
        en=(
            "### Environment and data\n\n"
            "This notebook uses only numpy, pandas, scipy, statsmodels, arch and matplotlib: **no GPU "
            "and no PyTorch**. The reason is that refitting the linear models and the GARCH family is "
            "small-scale linear algebra and a sequentially dependent likelihood iteration, where moving "
            "data to a GPU costs more than the arithmetic saves; and the Level 4 networks **cannot be "
            "retrained inside a notebook** (hours of GPU time), so their forecasts are read from the "
            "stored series and flagged as such in the reproduction report.\n\n"
            "The data live in `data/` in the repository and the forecast series in `data/predictions/`. "
            "`find_dir` below lets the notebook run from either the project folder or the repository."
        ),
    ),
    code(
        """
import json, sys, warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 40)
plt.rcParams.update({"figure.dpi": 110, "font.size": 9, "axes.grid": True,
                     "grid.color": "#e6e5e0", "grid.linewidth": 0.6,
                     "savefig.bbox": "tight", "legend.frameon": False})

HERE = Path.cwd()


def find_dir(*names):
    \"\"\"Locate a data folder whether the notebook sits in the repo or in the project tree.\"\"\"
    roots = [HERE, HERE.parent, HERE.parent.parent]
    for root in roots:
        for name in names:
            p = root / name
            if p.is_dir():
                return p
    raise FileNotFoundError(f"none of {names} found under {[str(r) for r in roots]}")


DATA = find_dir("data", "資訊階梯分析_程式與圖表/data")
PRED = find_dir("data/predictions", "資訊階梯分析_程式與圖表/predictions")
RES = find_dir("results", "資訊階梯分析_程式與圖表")

D = pd.read_csv(DATA / "analysis_daily.csv", parse_dates=["date"]).set_index("date")
def find_file(name):
    # groups.json sits in data/ in the repository and beside the scripts in the project tree
    for base in (DATA, RES, DATA.parent, RES.parent):
        p = base / name
        if p.is_file():
            return p
    raise FileNotFoundError(name)


GROUPS = json.load(open(find_file("groups.json"), encoding="utf-8"))

print("python     :", sys.version.split()[0])
print("pandas     :", pd.__version__, "| numpy:", np.__version__)
print("data       :", DATA.relative_to(DATA.parent.parent))   # relative: an absolute path would publish the author's folder tree
print("rows       :", len(D), "|", D.index.min().date(), "->", D.index.max().date())
print("columns    :", list(D.columns))
"""
    ),
    bi(
        zh=(
            "### 查核登錄簿\n\n"
            "`findings.csv` 是稿件裡每一個可查核數字的清單——表格的每個欄位、摘要的每個數字、"
            "正文裡每一句有數字的主張。重現比對是**對照這份清單**，不是對照我們對論文的印象："
            "沒有被登錄的數字，就是沒有人查過的數字。\n\n"
            "容許誤差來自稿件印出的位數：印到小數第四位，就是在主張小數第四位。"
            "`check()` 只接受會四捨五入成那個印出值的計算結果。"
        ),
        en=(
            "### The findings register\n\n"
            "`findings.csv` lists every checkable number in the manuscript: each table cell, each number "
            "in the abstract, each numeric claim in the text. The reproduction is checked **against that "
            "file**, not against our memory of the paper: a number left out of the register is a number "
            "nobody checked.\n\n"
            "Tolerance comes from the printed precision. A value printed to four decimals is a claim about "
            "four decimals, and `check()` accepts only computed values that round to it."
        ),
    ),
    code(
        """
sys.path.insert(0, str(HERE))
from repro import Register                      # noqa: E402

reg = Register(HERE / "findings.csv")
print(f"registered findings: {len(reg.rows)}")
print(pd.Series([r["unit"] for r in reg.rows.values()]).value_counts().to_frame("findings").T)
"""
    ),
]
