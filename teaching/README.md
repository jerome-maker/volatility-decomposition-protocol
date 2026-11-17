# 技能樹教材與重現報告 / Skill-tree tutorial and reproduction report

`volatility_ladder_tutorial.ipynb` 是這篇論文的中英雙語教材，同時是投稿前的數字查核。
每一個稿件報告的數字都在筆記本裡用資料重新算一次，結果列在最後一個單元。

`volatility_ladder_tutorial.ipynb` is the bilingual tutorial for the paper and, at the same time,
its pre-submission check: every number the manuscript reports is re-derived from the data inside
the notebook, with the comparison listed in the final unit.

## 怎麼讀 / How to read it

技能樹從資料建構開始，走到論文自己的方法，每個節點分四層講解：原理、公式、演算法、程式設計邏輯。
單元順序是技能樹的拓撲排序，每個單元開頭會說明前一個節點做不到什麼。

The skill tree runs from data construction up to the paper's own method. Each node is taught in
four layers — principle, formulas, algorithm, program logic — and the units follow a topological
order of the tree, each opening with what its prerequisites cannot do.

| 單元 Unit | 節點 Node |
|---|---|
| 1-3 | F1 已實現變異數與目標、F2 預測變數區塊與共線性、F3 樣本外協定 |
| 4-10 | C1 穩健損失、C2 HAR-RV、C3 GARCH、C4 DM 檢定、C5 Clark-West、C6 區塊拔靴法、C7 模型信賴集合 |
| 11-15 | K1 資訊集合對等、K2 三項分解、K3 GARCH-X、K4 經濟評估、K5 種子與版本 |
| 16-19 | R1 第二標的、R2 保留樣本、R3 配適方案、R4 Granger 與歸因 |
| 20-21 | D1 重現報告、D2 差異分析與真實錯誤史 |

## 重現狀態 / Reproduction status

| 狀態 Status | 數量 Count |
|---|---|
| 重現 reproduced | 93 |
| 重現（附註） reproduced with note | 9 |
| 無法驗證 not verifiable | 7 |
| 不一致 differs | 0 |

無法驗證的七項都是需要 GPU 重訓神經網路、或需要同時安裝兩個版本的深度學習套件，
筆記本裡逐項寫明缺的是什麼。第一輪查核找到的一項不一致（相關係數的正負號）與兩處定義未說明，
作者已在稿件中處理，D2 單元記錄了處理方式。

The seven not-verifiable items all need either GPU retraining of the networks or two versions of
the deep learning library installed at once; the notebook states exactly what is missing for each.
The one differing item from the first pass (the sign of a correlation) and two unstated definitions
were corrected in the manuscript; unit D2 records how.

## 一鍵執行 / Run it without installing anything

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jerome-maker/volatility-decomposition-protocol/blob/main/teaching/volatility_ladder_tutorial.ipynb)
[![Launch Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/jerome-maker/volatility-decomposition-protocol/main?labpath=teaching%2Fvolatility_ladder_tutorial.ipynb)

筆記本第一格會自行處理環境：**找不到資料時**才複製倉庫並切換目錄，**缺套件時**才安裝。
在自己電腦上執行時兩件事都不會觸發，學生不需要先加任何指令。

The first cell handles the environment by itself: it clones the repository and changes directory
**only when the data cannot be found**, and installs packages **only when one is missing**. Running
locally, neither fires, and a student adds nothing.

本機安裝 / Local install:

```bash
pip install -r requirements.txt
jupyter lab teaching/volatility_ladder_tutorial.ipynb
```

套件版本釘在論文 `ENVIRONMENT.md` 的 Environment A，也就是這份筆記本實際執行的版本。
The pinned versions are Environment A of the paper's `ENVIRONMENT.md`, which is what the notebook
was executed with.

## 重新產生 / Rebuilding

```bash
pip install -r ../requirements.txt nbformat nbclient ipykernel
python build_notebook.py --execute          # assemble, run every cell, store outputs
python check_notebook_render.py volatility_ladder_tutorial.ipynb
python check_reproduction.py findings.csv repro_results.json
```

筆記本不需要 GPU 也不需要 PyTorch：線性模型與 GARCH 都在筆記本裡重新估計，
神經網路則讀既有的預測序列（`data/predictions/`）。

The notebook needs neither a GPU nor PyTorch: the linear models and the GARCH family are
re-estimated inside it, while the networks' forecasts are read from the stored series in
`data/predictions/`.

## 檔案 / Files

| 檔案 File | 用途 Purpose |
|---|---|
| `volatility_ladder_tutorial.ipynb` | 教材與重現報告（已執行，含輸出） |
| `findings.csv` | 稿件中每一個可查核數字的登錄簿，109 筆 |
| `repro_results.json` | 每一項檢查的結果，由筆記本寫出 |
| `parts/` | 教材各部分的原始模組；筆記本由它們組裝而成 |
| `build_notebook.py` | 組裝、執行並檢查圖文的建構程式 |
| `check_notebook_render.py` | 四項渲染檢查，含 GitHub 數學式往返測試 |
| `check_reproduction.py` | 獨立的重現覆蓋率與一致性檢查 |

教材由作者在生成式 AI 協助下製作；研究設計、結果與詮釋為作者所有。
The tutorial was produced with generative AI assistance; the research design, results and
interpretation remain the author's.
