"""Export every out-of-sample forecast series to CSV so the analysis can be redone without the raw 1-minute data."""
import pandas as pd, numpy as np, pickle, json, os

OUT = r'J:/我的雲端硬碟/2026工作區/指導學生/柳宇軒/資訊階梯分析_程式與圖表/predictions'
os.makedirs(OUT, exist_ok=True)

# ---------- main analysis (SPY, 5-minute information set)
D = pd.read_parquet('analysis_daily.parquet')
P = pickle.load(open('pred_l123.pkl', 'rb'))
L4 = pickle.load(open('l4_final10.pkl', 'rb'))
TEST = (D.index >= '2023-01-01') & (D.index <= '2025-12-31'); idx = D.index[TEST]

seed_rows = []
for tgt in ['y_hf', 'y_cc']:
    per = {}
    for (Y, cfg, seed, t), r in L4['runs']:
        if t != tgt: continue
        s = pd.Series(r['pred'], D.index[r['te']])
        per.setdefault(Y, []).append(s)
        seed_rows.append(pd.DataFrame({'date': s.index, 'target': tgt, 'year': Y, 'seed': seed, 'forecast': s.values}))
    P[(tgt, 'L4 Transformer')] = pd.concat([pd.concat(v, axis=1).mean(axis=1) for v in per.values()]).sort_index()

# SHAR / SHAR-X robustness models (target A only)
try:
    PA = pickle.load(open('pred_all.pkl', 'rb'))
    for k in [('y_hf', 'L2 SHAR'), ('y_hf', 'L3 SHAR-X'), ('y_hf', 'L4 LSTM'), ('y_cc', 'L4 LSTM')]:
        if k in PA: P[k] = PA[k]
except FileNotFoundError:
    print('warning: pred_all.pkl missing, SHAR models not exported')

rows = []
for (tgt, model), s in P.items():
    f = s.reindex(idx)
    rows.append(pd.DataFrame({'date': idx, 'target': tgt, 'model': model, 'forecast': f.values,
                              'actual': D[tgt].values[TEST]}))
M = pd.concat(rows).sort_values(['target', 'model', 'date'])
M.to_csv(f'{OUT}/pred_main_SPY.csv', index=False, encoding='utf-8-sig')

S = pd.concat(seed_rows).sort_values(['target', 'seed', 'date'])
S.to_csv(f'{OUT}/pred_transformer_by_seed_SPY.csv', index=False, encoding='utf-8-sig')


# ---------- second asset (QQQ / SPY, daily information set)
PA2 = pickle.load(open('pred_asset2_all.pkl', 'rb'))
rows = []
for tkr in ['QQQ', 'SPY']:
    Dt = pd.read_parquet(f'daily_{tkr}.parquet')
    m = (Dt.index >= '2023-01-01') & (Dt.index <= '2025-12-31'); ix = Dt.index[m]
    for model, s in PA2[tkr].items():
        rows.append(pd.DataFrame({'date': ix, 'asset': tkr, 'model': model,
                                  'forecast': s.reindex(ix).values, 'actual': Dt.y.values[m]}))
A2 = pd.concat(rows).sort_values(['asset', 'model', 'date'])
A2.to_csv(f'{OUT}/pred_asset2_QQQ_SPY.csv', index=False, encoding='utf-8-sig')

# ---------- daily feature datasets (inputs) for reproducibility
D.to_csv(f'{OUT}/../data/analysis_daily_SPY.csv', encoding='utf-8-sig')
for tkr in ['QQQ', 'SPY']:
    pd.read_parquet(f'daily_{tkr}.parquet').to_csv(f'{OUT}/../data/daily_{tkr}.csv', encoding='utf-8-sig')

readme = f"""# 預測序列資料夾

用途：不必重跑 1 分鐘原始資料，即可重製全部表格、圖與統計檢定。
產生日期：{pd.Timestamp.today().date()}　產生程式：export_preds.py

## 檔案

| 檔案 | 內容 | 列數 |
|---|---|---|
| pred_main_SPY.csv | 主分析：測試期 2023–2025 每日、每個模型的預測值與實際值；target 欄 y_hf＝5 分鐘已實現波動、y_cc＝日報酬已實現波動 | {len(M):,} |
| pred_transformer_by_seed_SPY.csv | Transformer 各隨機種子的個別預測（主分析報告用的是 5 個種子的平均） | {len(S):,} |
| pred_asset2_QQQ_SPY.csv | 第二標的穩健性分析：QQQ 與 SPY 在日頻資訊集下的預測與實際值 | {len(A2):,} |
| ../data/analysis_daily_SPY.csv | 主分析的日頻特徵與目標（2011–2026） | {len(D):,} |
| ../data/daily_QQQ.csv、daily_SPY.csv | 第二標的分析的日頻特徵與目標 | 各 3,771 |

## 欄位

- `date`：預測作成日（第 t 日收盤）。預測對象為第 t+1 至 t+5 日。
- `forecast`、`actual`：年化波動率，**小數**（0.15 ＝ 15%）。報告中的誤差以年化百分點表示，需乘以 100。
- `model`：L0–L4 對應資訊階梯的層級。
- 主分析的模型清單：{', '.join(sorted({m for _, m in P}))}

## 注意

- 2026 年為最終保留樣本，依研究設計尚未動用，故不在本資料夾內。
- 原始 1 分鐘資料因供應商授權未隨附；上述日頻檔案已足以重製全部結果。
"""
open(f'{OUT}/README.md', 'w', encoding='utf-8').write(readme)
print('main', M.shape, '| seeds', S.shape, '| asset2', A2.shape)
print('models:', sorted({m for _, m in P}))
