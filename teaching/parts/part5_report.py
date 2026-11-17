# -*- coding: utf-8 -*-
"""Units D1-D2 and the literature map: the reproduction report and what went wrong."""
from parts._helpers import bi, code, md, mono, unit_header

CELLS = [
    unit_header("D1", "重現報告", "Reproduction report",
                "repro.py, findings.csv", "—", "every preceding unit"),
    bi(
        zh=(
            "### 原理\n\n"
            "前面每個單元都在各自的位置上呼叫了 `check`。這個單元把所有結果收攏成一張表："
            "稿件位置、稿件報告值、筆記本算出的值、狀態。\n\n"
            "三種狀態的意義必須清楚：**重現**是在印出位數的容許範圍內相符；**不一致**是超出容許範圍，"
            "或符號、星號、排序不符；**無法驗證**是缺少某樣東西（專屬資料、沒記錄的種子、裝不起來的版本），"
            "而且必須寫清楚缺的是什麼。**無法驗證永遠不是通過。**\n\n"
            "### 程式設計邏輯\n\n"
            "`report()` 會列出登錄簿裡的**每一列**，包含沒有被任何 `check` 呼叫碰過的那些——"
            "漏掉的檢查如果不顯示出來，最後的摘要就會謊稱「全部重現」。"
        ),
        en=(
            "### Principle\n\n"
            "Every unit so far called `check` in place. This unit collects the results into one table: "
            "manuscript location, reported value, notebook value, status.\n\n"
            "The three statuses mean precisely: **reproduced** agrees within the tolerance implied by the "
            "printed digits; **differs** is outside that tolerance, or a sign, star or ranking disagrees; "
            "**not verifiable** means something needed is missing (proprietary data, an unrecorded seed, a "
            "version that cannot be installed), and exactly what is missing must be stated. **Not verifiable "
            "is never a pass.**\n\n"
            "### Program logic\n\n"
            "`report()` lists **every row** of the register, including those no `check` call ever touched: a "
            "missing check that is not displayed turns the final summary into a false claim that everything "
            "reproduced."
        ),
    ),
    code(
        """
report = reg.report()
pd.set_option("display.max_rows", 200)
pd.set_option("display.max_colwidth", 46)
report
"""
    ),
    code(
        """
summary = report["status"].value_counts()
print(summary.to_string())
print()
bad = report[report["status"].isin(["differs", "unchecked"])]
if len(bad):
    print("items needing the researcher's decision before submission:")
    print(bad[["id", "location", "manuscript", "notebook", "detail"]].to_string(index=False))
else:
    print("no differing or unchecked findings")

fig, ax = plt.subplots(figsize=(5.4, 2.2))
order = ["reproduced", "reproduced_note", "not_verifiable", "differs", "unchecked"]
vals = [int(summary.get(k, 0)) for k in order]
ax.barh(order, vals, color=["#2c7a3f", "#7fa87f", "#b0b0b0", "#c0392b", "#8e44ad"])
for i, v in enumerate(vals):
    if v:
        ax.text(v + 0.5, i, str(v), va="center", fontsize=8)
ax.set_xlabel("number of registered findings")
ax.set_title("Reproduction status over the findings register")
plt.show()
"""
    ),
    unit_header("D2", "差異分析與真實錯誤史", "Discrepancies and the project's real bugs",
                "—", "teaching-notebook: the integrity unit", "D1"),
    bi(
        zh=(
            "### 原理\n\n"
            "方法論課程教的是怎麼把事情做對，幾乎不教**做錯的時候從裡面看起來是什麼樣子**。"
            "但真正危險的錯誤不會丟出例外、不會讓程式停下來，它們產生看起來完全合理的數字。"
            "這個單元拆解本專案真實發生過的幾個錯誤——每一個都通過了當時的檢查。\n\n"
            "每個案例問四個問題：症狀是什麼、根因是什麼、為什麼沒被抓到、"
            "以及**在不知道正確答案的前提下，什麼檢查可以抓到它**。最後一項才是可以帶走的東西。"
        ),
        en=(
            "### Principle\n\n"
            "Methods courses teach how to get things right and are nearly silent on **what being wrong looks "
            "like from the inside**. The dangerous errors raise no exception and stop nothing; they produce "
            "numbers that look entirely reasonable. This unit dissects real failures from this project, each "
            "of which passed the checks in place at the time.\n\n"
            "Each case asks four questions: the symptom, the root cause, why it evaded detection, and **what "
            "check would have caught it without knowing the right answer in advance**. Only the last one "
            "transfers."
        ),
    ),
    bi(
        zh=(
            "### 案例一：樞紐表悄悄平均了兩個目標\n\n"
            "**症狀**：$\\Delta_{arch}$ 算出 −0.0132、DM 統計量 −1.13，而正確值是 −0.0244 與 −2.79。"
            "數量級合理、符號正確，看不出異常。\n\n"
            "**根因**：`pred_main_SPY.csv` 是長格式，同時堆疊 `y_hf` 與 `y_cc` 兩個目標。"
            "`pivot_table` 的預設彙總函數是平均，所以沒有先篩選 `target` 時，"
            "它把兩個不同目標的預測**平均**成一欄。\n\n"
            "**為什麼沒被抓到**：沒有例外、沒有警告，結果落在合理區間內。\n\n"
            "**可帶走的檢查**：覆蓋率斷言。樞紐表的列數必須等於預期的評估天數，"
            "而且每一組 (日期, 模型) 只能出現一次。本筆記本的 `forecasts()` 就寫了這兩行 `assert`——"
            "它們不需要知道正確答案，只需要知道資料應該長什麼樣子。"
        ),
        en=(
            "### Case 1: a pivot that silently averaged two targets\n\n"
            "**Symptom.** $\\Delta_{arch}$ came out as −0.0132 with a DM statistic of −1.13, where the correct "
            "values are −0.0244 and −2.79. The magnitude was plausible and the sign was right, so nothing "
            "looked wrong.\n\n"
            "**Root cause.** `pred_main_SPY.csv` is in long format and stacks two targets, `y_hf` and `y_cc`. "
            "The default aggregation of `pivot_table` is the mean, so without first filtering on `target` it "
            "**averaged forecasts of two different quantities** into one column.\n\n"
            "**Why it evaded detection.** No exception, no warning, and a result inside the plausible range.\n\n"
            "**The transferable check.** Coverage assertions. The pivot must have exactly as many rows as "
            "evaluation days, and each (date, model) pair must appear once. Both `assert` lines live in this "
            "notebook's `forecasts()`; neither needs to know the right answer, only what the data should look "
            "like."
        ),
    ),
    bi(
        zh=(
            "### 案例二：十七個表標題都帶著 markdown 的粗體符號\n\n"
            "**症狀**：Word 檔裡每個表標題印成「Table 1. ** Sample split…」。\n\n"
            "**根因**：標題在原始檔裡寫成 `**Table 5.1** 說明文字`，轉檔程式只剝掉開頭的 `**`，"
            "留下中間那一組。\n\n"
            "**為什麼沒被抓到**：原本的投稿前檢查只驗「表編號是否連續」與「每張表是否被引用」，"
            "沒有人去看標題**文字本身**。\n\n"
            "**可帶走的檢查**：對最終產物做檢查，而不是對中間檔。"
            "把 Word 檔讀回來，掃描所有以 Table 或 Figure 開頭的段落，發現任何 markdown 標記就失敗。\n\n"
            "### 案例三：十七張表裡有十一張從未在正文被引用\n\n"
            "**症狀**：表格存在、編號正確，但正文從頭到尾沒有一句話叫到它們。\n\n"
            "**根因**：寫作時以散文描述結果，忘了插入「表 N 報告…」這類指路句。\n\n"
            "**為什麼沒被抓到**：舊的檢查問的是「這個表編號有沒有出現過」，而標題本身就讓它出現了一次。\n\n"
            "**可帶走的檢查**：把門檻訂在**出現兩次以上**（標題一次、正文至少一次），"
            "而不是「出現過」。判準的強度決定了檢查有沒有用。"
        ),
        en=(
            "### Case 2: seventeen table captions carrying markdown bold markers\n\n"
            "**Symptom.** Every caption in the Word file printed as \"Table 1. ** Sample split...\".\n\n"
            "**Root cause.** Captions are written as `**Table 5.1** caption text` in the source, and the "
            "converter stripped only the leading `**`, leaving the inner pair.\n\n"
            "**Why it evaded detection.** The pre-submission check verified that table numbers ran "
            "consecutively and that each table was cited; nobody inspected the caption **text**.\n\n"
            "**The transferable check.** Check the final artefact, not the intermediate file. Read the Word "
            "document back, scan every paragraph beginning with Table or Figure, and fail on any markdown "
            "marker.\n\n"
            "### Case 3: eleven of seventeen tables were never called out in the text\n\n"
            "**Symptom.** The tables existed and were numbered correctly, but no sentence referred to them.\n\n"
            "**Root cause.** The results were described in prose and the pointer sentences (\"Table N "
            "reports...\") were never inserted.\n\n"
            "**Why it evaded detection.** The old check asked whether the table number appeared anywhere, and "
            "the caption itself made it appear once.\n\n"
            "**The transferable check.** Set the threshold at **two or more occurrences** (caption plus at "
            "least one callout) rather than at \"appears\". How demanding the criterion is decides whether "
            "the check is worth running."
        ),
    ),
    bi(
        zh=(
            "### 案例四：線上先行年份變成文獻年份\n\n"
            "**症狀**：參考文獻清單把 Corsi 印成 2008，內文引用卻是 2009；"
            "Christensen 等人清單 2022、內文 2023。\n\n"
            "**根因**：從 Crossref 取 `issued` 欄位，那是**線上先行**日期，不是卷期年份。\n\n"
            "**為什麼沒被抓到**：兩個年份都「看起來像對的年份」。\n\n"
            "**可帶走的檢查**：交叉比對。內文引用的年份與文獻清單的年份必須一致——"
            "這個檢查不需要知道哪一個才是對的，只要知道兩者必須相同。\n\n"
            "### 案例五：同一欄混了兩種報酬定義（本筆記本在 K4 發現）\n\n"
            "**症狀**：表 6.2 的七個模型列報酬為幾何年化（18.9% 等），"
            "買進持有列卻是算術年化（20.7%；幾何為 21.6%）。\n\n"
            "**根因**：買進持有列由另一段程式計算，沿用了不同的慣例。\n\n"
            "**為什麼沒被抓到**：兩個數字各自都正確，只有放在同一欄比較時才有問題。"
            "而且 Sharpe 全欄都用算術定義，所以論文的主要論證（排序）不受影響。\n\n"
            "**可帶走的檢查**：守恆／一致性斷言。同一欄的每個數字必須由同一個函數產生；"
            "若必須由不同程式產生，就把定義當作參數明確傳入。"
            "**結局**：作者選擇兩種慣例並列，表 6.2 改為幾何與算術各一欄，讀者自己看得到差距約一個百分點。\n\n"
            "### 案例六：VIF 沒說是在哪個設計下算的（本筆記本在 F2 發現）\n\n"
            "**症狀**：重現 VIF 得到 7.4 與 1.9，稿件是 6.3 與 1.6。\n\n"
            "**根因**：稿件的數字算在「HAR＋選擇權區塊」五變數設計上，"
            "重現時預設用了全部 18 個變數。兩者都正確，但稿件沒寫是哪一個。\n\n"
            "**可帶走的檢查**：把設定列舉出來比對，而不是調整到吻合為止。"
            "吻合的那一個設定就是答案，而「稿件沒寫清楚」本身就是要回報給作者的發現。"
            "**結局**：稿件已補上設計說明，並把第二個參數化選擇的理由也從相關係數改為 VIF，兩處現在用同一個指標。"
        ),
        en=(
            "### Case 4: an online-first date became the reference year\n\n"
            "**Symptom.** The reference list printed Corsi as 2008 while the text cited 2009; Christensen et "
            "al. appeared as 2022 in the list and 2023 in the text.\n\n"
            "**Root cause.** The year was taken from Crossref's `issued` field, which is the **online-first** "
            "date rather than the issue year.\n\n"
            "**Why it evaded detection.** Both years look like plausible years.\n\n"
            "**The transferable check.** Cross-check: the year in an in-text citation and the year in the "
            "reference list must agree. The check does not need to know which is correct, only that the two "
            "must match.\n\n"
            "### Case 5: two return conventions in one column (found by this notebook in K4)\n\n"
            "**Symptom.** In Table 6.2 the seven model rows report geometric annualized returns (18.9% and so "
            "on) while the buy-and-hold row reports an arithmetic one (20.7%; geometric would be 21.6%).\n\n"
            "**Root cause.** The buy-and-hold row is computed by a separate piece of code that kept a "
            "different convention.\n\n"
            "**Why it evaded detection.** Each number is correct on its own; only the comparison inside one "
            "column is not. The Sharpe column is arithmetic throughout, so the paper's actual argument — the "
            "ranking — is unaffected.\n\n"
            "**The transferable check.** A consistency assertion: every number in a column should come from "
            "one function, and where it cannot, the convention should be passed in explicitly as an "
            "argument. **Outcome:** the author chose to report both, so Table 6.2 now carries a geometric and an arithmetic return column and the reader can see the gap of about one percentage point.\n\n"
            "### Case 6: the VIF design was never stated (found by this notebook in F2)\n\n"
            "**Symptom.** Reproducing the inflation factors gave 7.4 and 1.9 against the manuscript's 6.3 and "
            "1.6.\n\n"
            "**Root cause.** The manuscript's figures come from the five-variable HAR-plus-option design, "
            "while the reproduction defaulted to all eighteen predictors. Both are correct; the manuscript "
            "does not say which.\n\n"
            "**The transferable check.** Enumerate the defensible designs and compare, rather than tuning "
            "until something matches. The design that agrees exactly is the answer, and the fact that the "
            "manuscript did not state it is itself a finding to report to the author. **Outcome:** the manuscript now names the design, and the second parameterization choice is justified with inflation factors too, so both use one measure."
        ),
    ),
    code(
        """
# The checks from the cases above, as runnable assertions over this project's own artefacts.
checks = {}

g = P[P["target"] == "y_hf"]
checks["coverage: 752 evaluation days"] = len(g["date"].unique()) == 752
checks["coverage: one row per (date, model)"] = g.groupby(["date", "model"]).size().max() == 1
checks["targets kept separate"] = set(P["target"].unique()) == {"y_hf", "y_cc"}

parts_sum = dec_A["value"].iloc[:3].sum()
checks["additivity: parts sum to the total"] = abs(parts_sum - dec_A["value"].iloc[3]) < 1e-10
checks["ladder losses are positive"] = bool((pd.Series({m: qlike(Y, W[m]).mean() for m in MODELS}) > 0).all())
checks["no forecast is non-positive"] = bool((W[MODELS] > 0).all().all())

for k, v in checks.items():
    print(f"  [{'OK' if v else 'FAIL'}] {k}")
assert all(checks.values()), "an integrity check failed"
"""
    ),
    bi(
        zh=(
            "### 文獻地圖\n\n"
            "最後把文獻按技能樹的節點排好。研究生讀論文時常見的困難是不知道**哪一篇對應哪一步**；"
            "按節點排列之後，要補哪一塊就去讀哪一篇。\n\n"
            "| 節點 | 核心文獻 | 讀它是為了 |\n"
            "|---|---|---|\n"
            "| F1 | Andersen, Bollerslev, Diebold and Labys (2003) | 已實現波動率作為近乎無誤差的代理 |\n"
            "| F1 | Barndorff-Nielsen and Shephard (2004) | 以雙冪變異分離跳躍 |\n"
            "| F2 | Patton and Sheppard (2015) | 有號半變異數帶來的增額資訊 |\n"
            "| F3 | Chassot and Audrino (2026) | 配適方案如何決定線性基準會不會被打敗 |\n"
            "| F3 | Feng and Zhang (2025) | 視窗長度與損失的 U 形關係 |\n"
            "| C1 | Patton (2011) | 代理變數下仍保持排序的損失函數族 |\n"
            "| C1 | Taylor (2026) | 以對數模型建構、用相對損失評估時的轉換修正 |\n"
            "| C2 | Corsi (2009) | 異質自迴歸模型 |\n"
            "| C3 | Engle (1982); Glosten, Jagannathan and Runkle (1993) | ARCH 與非對稱效果 |\n"
            "| C3 | Hansen and Lunde (2005) | 沒有模型顯著勝過 GARCH(1,1) |\n"
            "| C4 | Diebold and Mariano (1995); Harvey, Leybourne and Newbold (1997) | 預測準確度檢定與小樣本校正 |\n"
            "| C5 | Clark and West (2007) | 巢狀模型的樣本外檢定 |\n"
            "| C6 | Künsch (1989) | 相依資料的區塊拔靴法 |\n"
            "| C7 | Hansen, Lunde and Nason (2011) | 模型信賴集合 |\n"
            "| K1 | Gu, Kelly and Xiu (2020) | 機器學習在資產定價的實證標竿 |\n"
            "| K1 | Zeng et al. (2023) | 簡單線性模型可與 Transformer 匹敵 |\n"
            "| K4 | Fleming, Kirby and Ostdiek (2003) | 以投資組合衡量波動擇時的經濟價值 |\n"
            "| K4 | Kupiec (1995); Christoffersen (1998) | 風險值的覆蓋與獨立性檢定 |\n"
            "| K5 | Gundersen and Kjensmo (2018); Kapoor and Narayanan (2023) | 機器學習研究的重現性 |\n"
            "| R4 | Granger (1969); Toda and Yamamoto (1995) | 預測先後與落後項擴增 |\n"
            "| R4 | Kumar et al. (2020); Aas, Jullum and Løland (2021) | 特徵相依時 Shapley 值的限制 |\n"
        ),
        en=(
            "### Literature map\n\n"
            "Finally, the references arranged by node of the skill tree. A common difficulty for graduate "
            "students is not knowing **which paper belongs to which step**; arranged this way, the gap tells "
            "you what to read.\n\n"
            "| Node | Core reference | Read it for |\n"
            "|---|---|---|\n"
            "| F1 | Andersen, Bollerslev, Diebold and Labys (2003) | realized volatility as a near error-free proxy |\n"
            "| F1 | Barndorff-Nielsen and Shephard (2004) | separating jumps with bipower variation |\n"
            "| F2 | Patton and Sheppard (2015) | the extra information in signed semivariances |\n"
            "| F3 | Chassot and Audrino (2026) | how the fitting scheme decides whether the linear benchmark is beaten |\n"
            "| F3 | Feng and Zhang (2025) | the U-shaped relation between window length and loss |\n"
            "| C1 | Patton (2011) | the family of losses whose ranking survives a noisy proxy |\n"
            "| C1 | Taylor (2026) | the back-transformation when a log model meets a relative loss |\n"
            "| C2 | Corsi (2009) | the heterogeneous autoregressive model |\n"
            "| C3 | Engle (1982); Glosten, Jagannathan and Runkle (1993) | ARCH and the asymmetric effect |\n"
            "| C3 | Hansen and Lunde (2005) | no specification significantly beats GARCH(1,1) |\n"
            "| C4 | Diebold and Mariano (1995); Harvey, Leybourne and Newbold (1997) | predictive accuracy and its small-sample correction |\n"
            "| C5 | Clark and West (2007) | out-of-sample testing for nested models |\n"
            "| C6 | Künsch (1989) | the block bootstrap for dependent data |\n"
            "| C7 | Hansen, Lunde and Nason (2011) | the model confidence set |\n"
            "| K1 | Gu, Kelly and Xiu (2020) | the empirical benchmark for machine learning in asset pricing |\n"
            "| K1 | Zeng et al. (2023) | simple linear models matching Transformers |\n"
            "| K4 | Fleming, Kirby and Ostdiek (2003) | measuring the economic value of volatility timing |\n"
            "| K4 | Kupiec (1995); Christoffersen (1998) | coverage and independence tests for value-at-risk |\n"
            "| K5 | Gundersen and Kjensmo (2018); Kapoor and Narayanan (2023) | reproducibility in machine learning research |\n"
            "| R4 | Granger (1969); Toda and Yamamoto (1995) | predictive precedence and lag augmentation |\n"
            "| R4 | Kumar et al. (2020); Aas, Jullum and Løland (2021) | the limits of Shapley values under dependence |\n"
        ),
    ),
    bi(
        zh=(
            "### 給研究生的四條帶得走的規則\n\n"
            "1. **先問資訊集合，再問模型。** 看到「深度學習勝過計量模型」時，第一個問題永遠是："
            "兩邊看到的輸入一樣嗎？不一樣的話，報告的增益沒辦法歸因。\n"
            "2. **報告種子離散度，不只報最佳種子。** 五個種子不足以支撐顯著性宣稱；"
            "十個種子的集成要連同全距一起報。\n"
            "3. **鎖定並揭露套件版本。** 若一個效果小於換版本造成的位移，它就還沒有被識別。\n"
            "4. **統計損失之外，至少做一個決策評估。** 排序在兩種評估下不一致，本身就是結果。\n\n"
            "最後一句話留給保留樣本：**事先承諾只用一次，然後照實報告**。"
            "本研究的架構項在保留年變號，論文因此把結論削弱到資料能支撐的程度——"
            "這比任何一個顯著的星號都更值得學。"
        ),
        en=(
            "### Four rules a student can take away\n\n"
            "1. **Ask about the information set before asking about the model.** When a paper reports that "
            "deep learning beat an econometric benchmark, the first question is whether both sides saw the "
            "same inputs. If not, the reported gain cannot be attributed.\n"
            "2. **Report the dispersion across seeds, not only the best one.** Five seeds cannot support a "
            "significance claim; a ten-seed ensemble should be reported together with its range.\n"
            "3. **Pin and disclose the library version.** An effect smaller than the shift caused by changing "
            "versions has not been identified.\n"
            "4. **Add at least one decision-based evaluation beside the statistical loss.** A ranking that "
            "disagrees between the two is itself a result.\n\n"
            "The last word belongs to the hold-out: **commit in advance to using it once, then report what it "
            "shows**. The architecture component changes sign in this study's reserved year, and the paper "
            "weakens its conclusion to what the data support. That is worth more than any significant star."
        ),
    ),
]
