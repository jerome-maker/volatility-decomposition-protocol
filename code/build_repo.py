"""Assemble the replication repository (code, derived data, figures, metadata)."""
import os, shutil, json, datetime, re

B = chr(92)

SRC = r'./'
CODE = SRC + '資訊階梯分析_程式與圖表/'
REPO = SRC + 'repo_volatility_decomposition/'
TITLE = 'Information or architecture? A decomposition protocol for evaluating deep learning gains in volatility forecasting'

# The project root appears in the scripts' own path constants and in the stored
# outputs of the notebook. Published as-is it tells everyone the author's drive
# layout, which here includes a student's name. Every TEXT file is therefore
# copied through copy_text(), which rewrites the prefix to './', and the guard at
# the end of this script refuses to leave a copy that still carries it.
PREFIXES = [SRC, SRC.replace("/", B), SRC.replace("/", B + B)]
HOME = os.path.expanduser("~")
PRIVATE = [SRC.split("/")[-2], HOME, HOME.replace(B, "/")]
TEXT_EXT = (".py", ".ipynb", ".md", ".csv", ".json", ".txt", ".cff", ".yml", ".yaml")


def copy_text(src, dst):
    """Copy a text file, stripping the author's project prefix.

    Byte-level, so line endings and everything else stay identical: a copy that
    normalised newlines would show every text file as modified and bury the one
    change that matters.
    """
    b = open(src, "rb").read()
    for pre in PREFIXES:
        b = b.replace(pre.encode("utf-8"), b"./")
    open(dst, "wb").write(b)


def copy_any(src, dst):
    (copy_text if src.endswith(TEXT_EXT) else shutil.copy)(src, dst)


def guard_no_private_paths(root):
    bad = []
    for r, _, fs in os.walk(root):
        if os.sep + ".git" in r + os.sep:
            continue
        for f in fs:
            if not f.endswith(TEXT_EXT):
                continue
            fp = os.path.join(r, f)
            try:
                s = open(fp, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            for hit in PREFIXES + PRIVATE:
                if hit in s:
                    bad.append((os.path.relpath(fp, root), hit))
    if bad:
        print("\nERROR: files in the published tree still carry a local path or name:")
        for f, hit in bad:
            print(f"  {f}: {hit!r}")
        raise SystemExit(f"{len(bad)} file(s); copy them through copy_text()")
    print("  no local paths or private names in the published tree")


for d in ('', 'code/', 'data/', 'data/predictions/', 'figures/', 'results/'):
    os.makedirs(REPO + d, exist_ok=True)

# --- code
for f in sorted(os.listdir(CODE)):
    if f.endswith('.py'): copy_any(CODE + f, REPO + 'code/' + f)
# --- derived data and results
for f in sorted(os.listdir(CODE)):
    if f.startswith(('res_', 'granger_')) and f.endswith(('.csv', '.json')):
        copy_any(CODE + f, REPO + 'results/' + f)
    elif f.endswith(('.csv', '.json')) and f not in ('groups.json',):
        copy_any(CODE + f, REPO + 'results/' + f)
copy_any(CODE + 'groups.json', REPO + 'data/groups.json')
for f in os.listdir(CODE + 'data'):
    if f.endswith(('.csv', '.json')): copy_any(CODE + 'data/' + f, REPO + 'data/' + f)
for f in os.listdir(CODE + 'predictions'):
    if f.endswith(('.csv', '.md')): copy_any(CODE + 'predictions/' + f, REPO + 'data/predictions/' + f)
FIGS = ['f1_overview.png', 'r1_ladder.png', 'r2_decomp.png', 'r3_pred.png', 'r4_regime.png',
        'r5_econ.png', 'r7_asset2.png', 'r8_spec.png', 'r6_shap_granger.png']
for i, f in enumerate(FIGS, 1): shutil.copy(CODE + 'fig/' + f, REPO + f'figures/Figure{i}.png')
copy_any(CODE + 'ENVIRONMENT.md', REPO + 'ENVIRONMENT.md')
if os.path.isfile(CODE + 'requirements.txt'):
    copy_any(CODE + 'requirements.txt', REPO + 'requirements.txt')

# teaching material and its reproduction report
TEACH = SRC + 'teaching/'
if os.path.isdir(TEACH):
    os.makedirs(REPO + 'teaching/parts/', exist_ok=True)
    for f in ('volatility_ladder_tutorial.ipynb', 'findings.csv', 'repro_results.json', 'README.md',
              'repro.py', 'check_reproduction.py', 'build_notebook.py', 'check_notebook_render.py'):
        if os.path.isfile(TEACH + f): copy_any(TEACH + f, REPO + 'teaching/' + f)
    for f in os.listdir(TEACH + 'parts'):
        if f.endswith('.py'): copy_any(TEACH + 'parts/' + f, REPO + 'teaching/parts/' + f)

readme = f"""# {TITLE}

Replication material for the paper. Every table and figure can be rebuilt from the files here;
the one-minute source data are not redistributable in full and are not included (see **Data**).

## What the paper does

Deep learning models in volatility forecasting are usually given more inputs than the econometric
benchmarks they are compared against, so a reported gain mixes the value of the information with the
value of the model. The paper builds a ladder of models whose rungs differ in the information they may
use, requires the deep learning model and its linear counterpart to receive identical inputs, and splits
the out-of-sample gain into three components that sum to it exactly:

- `Δ_HF` — the value of intraday information (GARCH-type models → HAR),
- `Δ_info` — the value of exogenous forward-looking information (HAR → HAR-X),
- `Δ_arch` — the value of the nonlinear architecture at a fixed information set (HAR-X → Transformer).

Applied to five-day realized volatility of SPY, with a second application to QQQ: `Δ_info` is the only
component that is positive and significant; neither a Transformer nor an LSTM improves on the linear
model with the same inputs; and the architecture component is of the same order as the variation caused
by the number of random seeds and by the version of the deep learning library.

## Teaching material

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jerome-maker/volatility-decomposition-protocol/blob/main/teaching/volatility_ladder_tutorial.ipynb)
[![Launch Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/jerome-maker/volatility-decomposition-protocol/main?labpath=teaching%2Fvolatility_ladder_tutorial.ipynb)

The notebook's first cell clones this repository and installs the pinned packages only when they
are missing, so it opens and runs on Colab or Binder with nothing added, and does nothing at all
when run from a local clone (`pip install -r requirements.txt`).

`teaching/volatility_ladder_tutorial.ipynb` walks the whole method up a skill tree, from data
construction to the decomposition, in Chinese and English side by side. Every technique is covered
in four layers — principle, formulas, algorithm, program logic — with this study's own data as the
worked example, and every number the paper reports is re-derived in the notebook and compared with
the manuscript. The final units give the reproduction report and dissect the project's real bugs.

Of the 109 registered findings, 102 reproduce and 7 are marked not verifiable with the reason
stated (they need GPU retraining or two versions of the deep learning library); none differ. The
first pass found one discrepancy and two unstated definitions, all since corrected in the
manuscript. See `teaching/README.md`.

## Layout

```
code/        every script, from raw data to the final document
data/        daily derived series, predictor groups, forecast series by model and seed
results/     all result tables (CSV/JSON) reported in the paper
figures/     Figure 1-9 as published
teaching/    bilingual skill-tree tutorial and the reproduction report
ENVIRONMENT.md   locked software environment, including the two PyTorch builds compared in Section 7
requirements.txt the six packages the teaching notebook needs, pinned to Environment A
```

## Reproducing the results

The pipeline runs in two environments: econometrics (`arch`, `statsmodels`) and deep learning
(CUDA-enabled PyTorch). `ENVIRONMENT.md` lists exact versions; mixing the two PyTorch builds changes
the measured loss by about 0.01 in QLIKE, which the paper documents.

```bash
python code/get_data.py        # Cboe VIX/VIX9D/VIX3M, FRED series, ETF prices
python code/features.py        # daily realized measures from one-minute bars
python code/build_dataset.py   # merge into the 18-variable analysis set
python code/ladder.py          # Levels 1-3
python code/l4_main10.py       # Level 4 Transformer, ten seeds       (GPU)
python code/lstm_final.py      # Level 4 LSTM control, ten seeds      (GPU)
python code/run_eval.py        # losses, DM/CW/MCS, regimes
python code/econ2.py           # value-at-risk and volatility targeting
python code/granger.py         # predictive precedence tests
python code/shap_l4.py         # attributions                         (GPU)
python code/holdout.py econ|nets|eval   # the reserved 2026 year
python code/figs_en.py         # all figures
```

Starting from `data/analysis_daily_SPY.csv` and `data/predictions/`, every table in the paper can be
recomputed without the one-minute source.

## Data

One-minute bars come from the HF Data Library (hfdatalibrary.com). The portion from March 2022 onward
derives from IEX Exchange HIST and is freely redistributable under the IEX Historical Data Terms of Use;
the earlier portion comes from a commercial feed and is not redistributable. This repository therefore
ships the daily derived series rather than the raw bars. Option-implied indices are Cboe public files,
interest rates and the dollar index come from FRED, and ETF prices from Yahoo Finance.

## Citing

See `CITATION.cff`.

## Licence

Code: MIT (`LICENSE`). Data and figures: CC BY 4.0 (`LICENSE-DATA.md`).
"""
open(REPO + 'README.md', 'w', encoding='utf-8').write(readme)

RELEASED = "2026-10-06"          # first public release, not the day this runs
year = datetime.date.today().year
open(REPO + 'CITATION.cff', 'w', encoding='utf-8').write(f"""cff-version: 1.2.0
title: "{TITLE}"
message: "If you use this material, please cite the paper and this archive."
type: software
authors:
  - family-names: Chou
    given-names: Jerome Chih-Lung
    affiliation: "Graduate Institute of Finance, National Taiwan University of Science and Technology"
    email: jerome.chou@ntust.edu.tw
keywords:
  - realized volatility
  - forecast evaluation
  - information set parity
  - Transformer
  - HAR model
  - reproducibility
license: MIT
date-released: "{RELEASED}"
""")

open(REPO + 'LICENSE', 'w', encoding='utf-8').write(f"""MIT License

Copyright (c) {year} Jerome Chih-Lung Chou

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
associated documentation files (the "Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the
following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial
portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO
EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
THE USE OR OTHER DEALINGS IN THE SOFTWARE.

The data files and figures in this repository are licensed under CC BY 4.0.
""")

open(REPO + '.gitignore', 'w', encoding='utf-8').write(
    "__pycache__/\n*.pyc\n*.parquet\n*.pkl\n*.docx\nrender/\nscratch/\ndesktop.ini\n")

guard_no_private_paths(REPO)

n = sum(len(fs) for _, _, fs in os.walk(REPO))
sz = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(REPO) for f in fs)
print(f'repository prepared: {n} files, {sz/1e6:.1f} MB at {REPO}')
for d in sorted(os.listdir(REPO)):
    p = REPO + d
    if os.path.isdir(p): print(f'  {d}/  {len(os.listdir(p))} files')
    else: print(f'  {d}')
