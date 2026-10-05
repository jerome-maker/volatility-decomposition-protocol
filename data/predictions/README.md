# 預測序列資料夾

用途：不必重跑 1 分鐘原始資料，即可重製全部表格、圖與統計檢定。
產生日期：2026-10-04　產生程式：export_preds.py

## 檔案

| 檔案 | 內容 | 列數 |
|---|---|---|
| pred_main_SPY.csv | 主分析：測試期 2023–2025 每日、每個模型的預測值與實際值；target 欄 y_hf＝5 分鐘已實現波動、y_cc＝日報酬已實現波動 | 15,040 |
| pred_transformer_by_seed_SPY.csv | Transformer 各隨機種子的個別預測（主分析報告用的是 5 個種子的平均） | 15,040 |
| pred_asset2_QQQ_SPY.csv | 第二標的穩健性分析：QQQ 與 SPY 在日頻資訊集下的預測與實際值 | 10,528 |
| ../data/analysis_daily_SPY.csv | 主分析的日頻特徵與目標（2011–2026） | 3,946 |
| ../data/daily_QQQ.csv、daily_SPY.csv | 第二標的分析的日頻特徵與目標 | 各 3,771 |

## 欄位

- `date`：預測作成日（第 t 日收盤）。預測對象為第 t+1 至 t+5 日。
- `forecast`、`actual`：年化波動率，**小數**（0.15 ＝ 15%）。報告中的誤差以年化百分點表示，需乘以 100。
- `model`：L0–L4 對應資訊階梯的層級。
- 主分析的模型清單：L0 Naive, L1 GARCH(1,1), L1 GJR-GARCH, L2 HAR-RV, L2 SHAR, L3 GARCH-X, L3 HAR-RV-X (full), L3 HAR-RV-X (opt only), L3 SHAR-X, L4 LSTM, L4 Transformer

## 注意

- 2026 年為最終保留樣本，依研究設計尚未動用，故不在本資料夾內。
- 原始 1 分鐘資料因供應商授權未隨附；上述日頻檔案已足以重製全部結果。
