# -*- coding: utf-8 -*-
"""Units R1-R4: the robustness branches hanging off the contribution."""
from parts._helpers import bi, code, md, mono, unit_header

CELLS = [
    unit_header("R1", "第二標的與日頻資訊集合", "Second asset on a daily-only information set",
                "asset2_final.py", "Garman and Klass (1980)", "K2"),
    bi(
        zh=(
            "### 原理\n\n"
            "K2 的分解只在一檔 ETF 上算過一次。單一標的的結果可能是該標的的特性，"
            "也可能是某一段時期的偶然。最直接的穩健性檢查是**換一檔標的再做一次**。\n\n"
            "問題是 QQQ 在本研究的樣本裡沒有日內資料。解法不是放棄，而是**把兩檔標的都降到日頻資訊集合**："
            "用 Garman-Klass 全距估計量取代已實現變異數，對 SPY 也套用同一個日頻設計。"
            "這樣兩欄之間唯一的差別就是標的，而不是資料品質。\n\n"
            "### 公式\n\n"
            "Garman-Klass 用當日最高、最低、開盤與收盤價估計變異數：\n\n"
            "$$\\hat{\\sigma}^2_{GK} = 0.5 (\\log(H/L))^2 - (2\\log 2 - 1)(\\log(C/O))^2$$\n\n"
            "在報酬為無漂移布朗運動的假設下，它的效率約為日報酬平方的五倍。\n\n"
            "### 演算法\n\n"
            "與 K1 的階梯完全相同，只是 L2 的三個 HAR 變數換成 Garman-Klass 的日、週、月平均，"
            "跨資產變數改用**相對報酬**（F2 已說明理由）。\n\n"
            "### 程式設計邏輯\n\n"
            "重點在於**重複使用 K2 的 `decompose`**，而不是另寫一份。"
            "穩健性檢查若用不同的程式重算，就無法保證比較的是同一件事。"
        ),
        en=(
            "### Principle\n\n"
            "The decomposition of K2 was computed once, on one ETF. A single-asset result could be a property "
            "of that asset, or an accident of the period. The most direct robustness check is to **do it "
            "again on another asset**.\n\n"
            "QQQ has no intraday data in this sample. The answer is not to give up but to **bring both assets "
            "down to a daily-only information set**: a Garman-Klass range estimator replaces realized "
            "variance, and the same daily design is applied to SPY as well. The two columns then differ only "
            "in the asset, not in data quality.\n\n"
            "### Formulas\n\n"
            "Garman-Klass estimates the variance from the day's high, low, open and close:\n\n"
            "$$\\hat{\\sigma}^2_{GK} = 0.5 (\\log(H/L))^2 - (2\\log 2 - 1)(\\log(C/O))^2$$\n\n"
            "Under driftless Brownian motion it is roughly five times as efficient as the squared daily "
            "return.\n\n"
            "### Algorithm\n\n"
            "Identical to the ladder of K1, except that the three HAR variables at L2 become the daily, "
            "weekly and monthly averages of the Garman-Klass estimator, and the cross-asset variable is the "
            "**relative return** for the reason given in F2.\n\n"
            "### Program logic\n\n"
            "The point is to **reuse `decompose` from K2** rather than write a second copy. A robustness "
            "check recomputed by different code cannot guarantee it is comparing the same thing."
        ),
    ),
    code(
        """
Q = pd.read_csv(PRED / "pred_asset2_QQQ_SPY.csv")
Q.columns = [c.lstrip("\\ufeff") for c in Q.columns]

a2_tab, a2_dec = {}, {}
for asset in ["QQQ", "SPY"]:
    g = Q[Q["asset"] == asset]
    w = g.pivot_table(index="date", columns="model", values="forecast")
    w.index = pd.to_datetime(w.index)
    yy = g.groupby("date")["actual"].first()
    yy.index = pd.to_datetime(yy.index)
    a2_tab[asset] = {m: qlike(yy, w[m]).mean() for m in w.columns}
    a2_dec[asset] = decompose(yy, w["L1 GJR-GARCH"], w["L2 HAR-GK"],
                              w["L3 HAR-GK-X (full)"], w["L4 Transformer"])

print(pd.DataFrame(a2_tab).round(4).to_string())
for asset in ["QQQ", "SPY"]:
    print(f"\\n{asset} decomposition")
    print(a2_dec[asset].round(4).to_string(index=False))

reg.check("T81_qqq_harx", a2_tab["QQQ"]["L3 HAR-GK-X (full)"])
reg.check("T81_spy_harx", a2_tab["SPY"]["L3 HAR-GK-X (full)"])
reg.check("T82_dinfo_qqq", a2_dec["QQQ"]["value"].iloc[1])
reg.check("T82_p_dinfo_qqq", a2_dec["QQQ"]["dm_p"].iloc[1])
reg.check("T82_dinfo_spy", a2_dec["SPY"]["value"].iloc[1])
reg.check("T82_darch_qqq", a2_dec["QQQ"]["value"].iloc[2])
"""
    ),
    unit_header("R2", "保留樣本年", "The reserved hold-out year",
                "holdout.py", "Section 8.5", "K2"),
    bi(
        zh=(
            "### 原理\n\n"
            "R1 換了標的，但用的仍是同一段時期。更嚴格的檢查是**另一段時間**，而且必須是"
            "在所有設計決定做完之前就先封存的那一段——否則「保留樣本」只是另一次嘗試。\n\n"
            "本研究把 2026 年整年封存，在設計定案後只用一次，而且事先承諾**不論結果如何都照實報告**。"
            "這一點值得研究生特別注意：保留樣本的價值完全來自「只用一次」這個承諾，"
            "用完之後再回頭調模型，它就失去意義了。\n\n"
            "### 公式\n\n"
            "無新公式：同樣的階梯、同樣的 $\\Delta$ 定義，只是估計樣本延長到 2025 年底、評估期換成 2026 年。\n\n"
            "### 演算法\n\n"
            "1. 以 2011 至 2025 年重估（同樣去尾五日）。\n"
            "2. 對 2026 年 1 月至 9 月逐日預測，共 170 天有完整目標。\n"
            "3. 算三項分解，照實報告。\n\n"
            "### 程式設計邏輯\n\n"
            "線性階梯可以在這裡完整重估，神經網路不行（沒有儲存 2026 年的預測序列），"
            "所以涉及 L4 的保留樣本數字在報告裡標為**無法驗證**，"
            "而 $\\Delta_{info}$ 這類只牽涉線性模型的數字則是獨立重算的。\n\n"
            "結果本身是這篇論文最誠實的一段：**架構項在保留年變號**。"
            "這不是失敗，而是結論必須被削弱到資料能支撐的程度——論文因此把架構結論寫成"
            "「沒有可靠證據指向任一方向」，而不是「架構有害」。"
        ),
        en=(
            "### Principle\n\n"
            "R1 changed the asset but kept the period. A stricter check uses **another period**, and it must "
            "be one sealed before the design decisions were made — otherwise a hold-out is just another "
            "attempt.\n\n"
            "The study reserved all of 2026, used it once after the design was frozen, and committed in "
            "advance to **reporting whatever it showed**. Students should note this carefully: the value of a "
            "hold-out comes entirely from the promise to use it once. Going back to tune the model after "
            "seeing it destroys that value.\n\n"
            "### Formulas\n\n"
            "No new formula: the same ladder and the same $\\Delta$ definitions, with the estimation sample "
            "extended to the end of 2025 and the evaluation period replaced by 2026.\n\n"
            "### Algorithm\n\n"
            "1. Re-estimate on 2011 to 2025, with the same five-day purge.\n"
            "2. Forecast each day of January to September 2026; 170 days carry a complete target.\n"
            "3. Compute the three components and report them as they come.\n\n"
            "### Program logic\n\n"
            "The linear ladder can be fully re-estimated here; the networks cannot, because no 2026 forecast "
            "series was stored. Hold-out numbers that involve Level 4 are therefore marked **not verifiable** "
            "in the report, while quantities such as $\\Delta_{info}$, which involve only linear models, are "
            "recomputed independently.\n\n"
            "The result is the most honest passage in the paper: **the architecture component changes sign in "
            "the hold-out year**. That is not a failure but a finding that forces the conclusion down to what "
            "the data support, which is why the paper reports an absence of reliable evidence in either "
            "direction rather than a claim that architecture hurts."
        ),
    ),
    code(
        """
te_h = np.where((D.index >= "2026-01-01") & np.isfinite(D["y_hf"].values))[0]
tr_h = np.where((D.index >= "2011-01-04") & (D.index <= "2025-12-31"))[0][:-5]
y_h = D["y_hf"].values[te_h]
print(f"hold-out evaluation days with a complete target: {len(te_h)} "
      f"({D.index[te_h[0]].date()} to {D.index[te_h[-1]].date()})")
reg.check_count("N_holdout_used", len(te_h))

hold = {}
for name, cols in [("HAR-RV", HAR), ("HAR-RV-X (opt only)", HAR + OPT), ("HAR-RV-X (full)", FEATS)]:
    f = linreg("y_hf", cols, tr_h, te_h)
    hold[name] = dict(RMSE=rmse_vol(y_h, f), QLIKE=qlike(y_h, f).mean(), f=f)
print(pd.DataFrame({k: {kk: vv for kk, vv in v.items() if kk != "f"} for k, v in hold.items()}).T.round(4).to_string())

d_info_h = hold["HAR-RV"]["QLIKE"] - hold["HAR-RV-X (full)"]["QLIKE"]
print(f"\\nDelta_info on the hold-out = {d_info_h:+.4f}   manuscript +0.033")
reg.check("T83_qlike_har_A", hold["HAR-RV"]["QLIKE"])
reg.check("T83_qlike_harx_A", hold["HAR-RV-X (full)"]["QLIKE"])
reg.check("T84_dinfo_A", d_info_h)
reg.not_verifiable("T83_qlike_trf_A",
                   "the 2026 Transformer forecasts were not stored, and retraining needs GPU time")
reg.not_verifiable("T84_darch_trf_A",
                   "depends on the 2026 Transformer forecasts, which are not in the repository")
"""
    ),
    unit_header("R3", "配適方案", "The fitting scheme",
                "fitscheme.py", "Chassot and Audrino (2026); Feng and Zhang (2025)", "K2, C2"),
    bi(
        zh=(
            "### 原理\n\n"
            "R1 與 R2 換了標的與時期，但**估計方式**一直沒動：每年重估一次、視窗向前展開。"
            "Chassot and Audrino (2026) 指出，HAR 的表現對配適方案非常敏感，"
            "而「重估頻率低」正是容易讓機器學習看起來勝出的設定——換句話說，"
            "本研究對線性基準可能不夠公平。\n\n"
            "這個單元就是把這個反對意見**先做給讀者看**：把線性模型改成每日重估，再加一個滾動視窗版本。\n\n"
            "### 公式\n\n"
            "無新公式，只是改變估計樣本的定義：\n\n"
            "$$\\lbrace t_0, \\ldots, i-5 \\rbrace \\qquad \\text{vs} \\qquad \\lbrace i-5-\\ell, \\ldots, i-5 \\rbrace$$\n\n"
            "左為展開視窗、右為滾動視窗；$i$ 為要預測的那一天、$\\ell = 630$。\n\n"
            "### 演算法\n\n"
            "1. 對評估期每一天各重估一次（752 次迴歸）。\n"
            "2. 神經網路維持每年重估——因為重訓代價太高，而且這樣只會讓比較偏向線性模型。\n"
            "3. 重新計算分解，看結論是否改變。\n\n"
            "### 程式設計邏輯\n\n"
            "每日重估在線性模型上是便宜的，因為每次只是解一次正規方程式。"
            "注意 purge 必須**跟著移動**：訓練資料只能到 $i-5$，不能到 $i-1$。"
            "Feng and Zhang (2025) 發現損失對視窗長度呈 U 形、1000 至 2000 個觀測較佳，"
            "所以 630 天刻意落在他們偏好的區間之下，是對線性方的**壓力測試**而非最佳化。"
        ),
        en=(
            "### Principle\n\n"
            "R1 and R2 varied the asset and the period, but the **estimation scheme** never moved: annual "
            "re-estimation on an expanding window. Chassot and Audrino (2026) show that HAR's performance "
            "depends heavily on the fitting scheme, and that infrequent re-estimation is exactly the setting "
            "in which machine learning tends to look ahead — in other words, this study might be unfair to "
            "its own linear benchmark.\n\n"
            "This unit puts that objection to the reader **before a referee does**: the linear models are "
            "re-estimated daily, and again on a rolling window.\n\n"
            "### Formulas\n\n"
            "No new formula, only a different estimation sample:\n\n"
            "$$\\lbrace t_0, \\ldots, i-5 \\rbrace \\qquad \\text{vs} \\qquad \\lbrace i-5-\\ell, \\ldots, i-5 \\rbrace$$\n\n"
            "with the expanding window on the left, the rolling window on the right, $i$ the day being forecast and $\\ell = 630$.\n\n"
            "### Algorithm\n\n"
            "1. Re-estimate once for every evaluation day (752 regressions).\n"
            "2. Keep the networks on annual re-estimation: retraining is expensive, and holding them fixed "
            "can only tilt the comparison towards the linear side.\n"
            "3. Recompute the decomposition and see whether the conclusion moves.\n\n"
            "### Program logic\n\n"
            "Daily re-estimation is cheap for a linear model because each step solves the normal equations "
            "once. The purge must **move with the window**: training data may run to $i-5$, never to $i-1$. "
            "Feng and Zhang (2025) find the loss to be U-shaped in window length with 1000 to 2000 "
            "observations preferable, so 630 days deliberately sits below their preferred range and is a "
            "**stress test** of the linear side rather than an optimisation of it."
        ),
    ),
    code(
        """
def daily_scheme(cols, roll=None, target="y_hf"):
    \"\"\"Re-estimate for every evaluation day; roll=None means an expanding window.\"\"\"
    te_all = np.where((D.index >= "2023-01-01") & (D.index <= "2025-12-31"))[0]
    X = np.c_[np.ones(len(D)), D[cols].values]
    y_log = np.log(D[target].values)
    out = np.empty(len(te_all))
    for k, i in enumerate(te_all):
        lo = 0 if roll is None else max(0, i - 5 - roll)
        tr_i = np.arange(lo, i - 5)                      # the purge moves with the window
        ok = tr_i[np.isfinite(y_log[tr_i]) & np.isfinite(X[tr_i]).all(1)]
        b = np.linalg.lstsq(X[ok], y_log[ok], rcond=None)[0]
        out[k] = np.exp(X[i] @ b + 0.5 * np.var(y_log[ok] - X[ok] @ b))
    return pd.Series(out, D.index[te_all])


schemes = {}
for name, cols in [("HAR-RV", HAR), ("HAR-RV-X", FEATS)]:
    f_daily = daily_scheme(cols)
    f_roll = daily_scheme(cols, roll=630)
    schemes[name] = dict(annual=qlike(Y, W["L2 HAR-RV" if name == "HAR-RV" else "L3 HAR-RV-X (full)"]).mean(),
                         daily=qlike(Y, f_daily).mean(), rolling630=qlike(Y, f_roll).mean())
    schemes[name + "_f"] = dict(daily=f_daily, rolling=f_roll)
print(pd.DataFrame({k: v for k, v in schemes.items() if not k.endswith("_f")}).T.round(4).to_string())

d_info_daily = schemes["HAR-RV"]["daily"] - schemes["HAR-RV-X"]["daily"]
d_arch_daily = schemes["HAR-RV-X"]["daily"] - qlike(Y, W["L4 Transformer"]).mean()
print(f"\\nwith daily re-estimation: Delta_info {d_info_daily:+.4f}, Delta_arch {d_arch_daily:+.4f}")
print("manuscript Table 8.6: +0.049 and -0.025")

reg.check("T85_har_daily", schemes["HAR-RV"]["daily"])
reg.check("T85_harx_daily", schemes["HAR-RV-X"]["daily"])
reg.check("T85_harx_roll630", schemes["HAR-RV-X"]["rolling630"])
reg.check("T86_dinfo_daily", d_info_daily)
reg.check("T86_darch_daily", d_arch_daily)
"""
    ),
    unit_header("R4", "區塊 Granger 檢定與歸因對照", "Block Granger tests and the attribution cross-check",
                "granger.py, shap_l4.py", "Granger (1969); Toda and Yamamoto (1995); Kumar et al. (2020)",
                "K1"),
    bi(
        zh=(
            "### 原理\n\n"
            "K2 告訴我們外生資訊整體有用，但沒說**是哪一塊**。"
            "神經網路的歸因（Shapley 值）可以給一個排序，問題是當特徵彼此相關時，"
            "Shapley 值的解讀並不可靠（Kumar et al., 2020；Aas et al., 2021）。\n\n"
            "本研究的做法是**不要單獨相信歸因**：另外做一個完全不同性質的檢定——"
            "區塊 Granger 預測先後檢定——再看兩個排序是否一致。"
            "一致不代表因果，但不一致就是警訊：網路可能依賴了沒有預測先後關係的區塊。\n\n"
            "### 公式\n\n"
            "對每個區塊 $g$，在條件於 HAR 項的迴歸中檢定其所有落後項係數同時為零：\n\n"
            "$$H_0: \\beta_{g,1} = \\cdots = \\beta_{g,p} = 0$$\n\n"
            "Wald 統計量為 $(R\\hat{\\beta})'[R \\hat{V} R']^{-1}(R\\hat{\\beta})$，$\\hat{V}$ 用 HAC 估計。\n\n"
            "### 演算法\n\n"
            "1. **只用估計樣本**（2011–2020），這樣評估期完全沒有被看過。\n"
            "2. 落後期數以 BIC 選取。\n"
            "3. 多重檢定用 Benjamini-Hochberg 控制偽發現率。\n"
            "4. 與歸因排序做 Spearman 相關與置換檢定。\n\n"
            "### 程式設計邏輯\n\n"
            "Wald 檢定用 statsmodels 的 `wald_test`，但限制矩陣 $R$ 是自己建的："
            "教學上要看見「對哪些係數做檢定」是一個明確的矩陣，而不是一個字串參數。"
            "歸因需要訓練好的網路，筆記本無法重算，因此標為無法驗證，但仍讀出儲存的結果做比較。"
        ),
        en=(
            "### Principle\n\n"
            "K2 says the exogenous information helps as a whole, but not **which part of it**. Attributions "
            "from the network (Shapley values) give an ordering, but when features are dependent those values "
            "are unreliable as importance measures (Kumar et al., 2020; Aas et al., 2021).\n\n"
            "The study's answer is **not to trust the attribution alone**: run a test of an entirely "
            "different character — block Granger predictive precedence — and see whether the two orderings "
            "agree. Agreement is not causality, but disagreement is a warning that the network may be "
            "relying on blocks with no predictive precedence at all.\n\n"
            "### Formulas\n\n"
            "For each block $g$, test that all its lag coefficients are jointly zero in a regression that "
            "conditions on the HAR terms:\n\n"
            "$$H_0: \\beta_{g,1} = \\cdots = \\beta_{g,p} = 0$$\n\n"
            "The Wald statistic is $(R\\hat{\\beta})'[R \\hat{V} R']^{-1}(R\\hat{\\beta})$ with $\\hat{V}$ "
            "estimated by HAC.\n\n"
            "### Algorithm\n\n"
            "1. Use the **estimation sample only** (2011-2020), so the evaluation period is never seen.\n"
            "2. Choose the lag length by BIC.\n"
            "3. Control the false discovery rate across blocks with Benjamini-Hochberg.\n"
            "4. Compare with the attribution ordering by Spearman correlation and a permutation test.\n\n"
            "### Program logic\n\n"
            "The Wald test uses statsmodels' `wald_test`, but the restriction matrix $R$ is built by hand: a "
            "reader should see that the choice of which coefficients are tested is an explicit matrix rather "
            "than a string argument. The attributions need a trained network, which the notebook cannot "
            "recompute, so they are marked not verifiable while the stored values are still read and "
            "compared."
        ),
    ),
    code(
        """
import statsmodels.api as sm

TR_mask = (D.index >= "2011-01-04") & (D.index <= "2020-12-31")


def block_wald(dep, xcols, lags, hac=10):
    \"\"\"Joint test that every lag of xcols is zero, conditional on the HAR terms.\"\"\"
    Z = pd.DataFrame({c: D[c] for c in HAR})
    names = []
    for c in xcols:
        for l in range(lags):
            Z[f"{c}_l{l}"] = D[c].shift(l)
            names.append(f"{c}_l{l}")
    Z["dep"] = dep
    Z = Z[TR_mask].dropna()
    X = sm.add_constant(Z.drop(columns="dep"))
    m = sm.OLS(Z["dep"], X).fit(cov_type="HAC", cov_kwds={"maxlags": hac})
    R = np.zeros((len(names), X.shape[1]))
    for i, nm in enumerate(names):
        R[i, list(X.columns).index(nm)] = 1
    t = m.wald_test(R, use_f=False, scalar=True)
    return float(t.statistic), float(t.pvalue), Z.shape[0]


LAGS = {"G3 選擇權前瞻": 3, "G2 下跌與跳躍": 2, "G6 美元與跨資產": 2,
        "G4 報酬": 2, "G7 交易量": 2, "G5 利率": 1}
dep5 = np.log(D["y_hf"])
gr = {}
for blk, lg in LAGS.items():
    stat, p, n = block_wald(dep5, GROUPS[blk], lg)
    gr[blk] = dict(lags=lg, wald_h5=stat, p=p, n=n)
G_tab = pd.DataFrame(gr).T.sort_values("wald_h5", ascending=False)
print(G_tab.round(4).to_string())

reg.check("T91_wald_g3_h5", G_tab.loc["G3 選擇權前瞻", "wald_h5"])
reg.check("T91_wald_g5_h5", G_tab.loc["G5 利率", "wald_h5"])
reg.check_text("T91_g3_largest", G_tab.index[0] == "G3 選擇權前瞻",
               f"largest Wald is {G_tab.index[0]}")
"""
    ),
    code(
        """
# The attribution side cannot be recomputed without the trained network; read what was stored.
shap_file = RES / "res_shap_groups.csv"
if shap_file.exists():
    SH = pd.read_csv(shap_file)
    print(SH.round(4).to_string(index=False))
else:
    print("stored attribution file not found:", shap_file)

reg.not_verifiable("T92_share_g3",
                   "attribution shares need the trained Transformer and a gradient explainer; the notebook "
                   "has neither the weights nor GPU training")
reg.not_verifiable("T92_rank_attr", "same reason as T92_share_g3")
"""
    ),
]
