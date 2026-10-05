# Information or architecture? A decomposition protocol for evaluating deep learning gains in volatility forecasting

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
ENVIRONMENT.md   locked software environment, including the two PyTorch builds compared in Section 7.2
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

See `CITATION.cff`. The archived release carries a DOI issued by Zenodo.

## Licence

Code: MIT. Data and figures: CC BY 4.0.
