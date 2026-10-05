"""Assemble the replication repository (code, derived data, figures, metadata)."""
import os, shutil, json, datetime, re

SRC = r'J:/我的雲端硬碟/2026工作區/指導學生/柳宇軒/'
CODE = SRC + '資訊階梯分析_程式與圖表/'
REPO = SRC + 'repo_volatility_decomposition/'
TITLE = 'Information or architecture? A decomposition protocol for evaluating deep learning gains in volatility forecasting'

for d in ('', 'code/', 'data/', 'data/predictions/', 'figures/', 'results/'):
    os.makedirs(REPO + d, exist_ok=True)

# --- code
for f in sorted(os.listdir(CODE)):
    if f.endswith('.py'): shutil.copy(CODE + f, REPO + 'code/' + f)
# --- derived data and results
for f in sorted(os.listdir(CODE)):
    if f.startswith(('res_', 'granger_')) and f.endswith(('.csv', '.json')):
        shutil.copy(CODE + f, REPO + 'results/' + f)
    elif f.endswith(('.csv', '.json')) and f not in ('groups.json',):
        shutil.copy(CODE + f, REPO + 'results/' + f)
shutil.copy(CODE + 'groups.json', REPO + 'data/groups.json')
for f in os.listdir(CODE + 'data'):
    if f.endswith(('.csv', '.json')): shutil.copy(CODE + 'data/' + f, REPO + 'data/' + f)
for f in os.listdir(CODE + 'predictions'):
    if f.endswith(('.csv', '.md')): shutil.copy(CODE + 'predictions/' + f, REPO + 'data/predictions/' + f)
FIGS = ['f1_overview.png', 'r1_ladder.png', 'r2_decomp.png', 'r3_pred.png', 'r4_regime.png',
        'r5_econ.png', 'r7_asset2.png', 'r8_spec.png', 'r6_shap_granger.png']
for i, f in enumerate(FIGS, 1): shutil.copy(CODE + 'fig/' + f, REPO + f'figures/Figure{i}.png')
shutil.copy(CODE + 'ENVIRONMENT.md', REPO + 'ENVIRONMENT.md')

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

## Layout

```
code/        every script, from raw data to the final document
data/        daily derived series, predictor groups, forecast series by model and seed
results/     all result tables (CSV/JSON) reported in the paper
figures/     Figure 1-9 as published
ENVIRONMENT.md   locked software environment, including the two PyTorch builds compared in Section 7
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

Code: MIT. Data and figures: CC BY 4.0.
"""
open(REPO + 'README.md', 'w', encoding='utf-8').write(readme)

year = datetime.date.today().year
open(REPO + 'CITATION.cff', 'w', encoding='utf-8').write(f"""cff-version: 1.2.0
title: "{TITLE}"
message: "If you use this material, please cite the paper and this archive."
type: software
authors:
  - family-names: Chou
    given-names: Jerome Chih-Lung
    affiliation: "Graduate Institute of Finance, National Taiwan University of Science and Technology"
    email: jerome.chou@mail.ntust.edu.tw
keywords:
  - realized volatility
  - forecast evaluation
  - information set parity
  - Transformer
  - HAR model
  - reproducibility
license: MIT
date-released: "{datetime.date.today()}"
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
    "__pycache__/\n*.pyc\n*.parquet\n*.pkl\n*.docx\nrender/\nscratch/\n")

n = sum(len(fs) for _, _, fs in os.walk(REPO))
sz = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(REPO) for f in fs)
print(f'repository prepared: {n} files, {sz/1e6:.1f} MB at {REPO}')
for d in sorted(os.listdir(REPO)):
    p = REPO + d
    if os.path.isdir(p): print(f'  {d}/  {len(os.listdir(p))} files')
    else: print(f'  {d}')
