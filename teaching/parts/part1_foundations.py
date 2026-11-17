# -*- coding: utf-8 -*-
"""Units F1-F3: the data, the predictors, and the out-of-sample protocol."""
from parts._helpers import bi, code, md, mono, unit_header

CELLS = [
    unit_header("F1", "已實現變異數與預測目標", "Realized variance and the forecast target",
                "features.py, build_dataset.py", "Andersen et al. (2003); Corsi (2009)", "—"),
    bi(
        zh=(
            "### 原理\n\n"
            "波動率不是觀察得到的量。要預測它，必須先用觀察得到的東西把它**代理**出來，而這個代理方式會決定"
            "後面所有比較的意義。日報酬平方是最便宜的代理，但雜訊極大；用日內報酬加總出來的已實現變異數"
            "(realized variance) 則準確得多。\n\n"
            "抽樣頻率是個取捨：抽得越密，微觀結構雜訊（買賣價差跳動、報價停滯）帶來的偏誤越大；"
            "抽得越疏，抽樣誤差越大。五分鐘是文獻的慣例，對流動性極高的標的大致落在平衡點上。\n\n"
            "第二個決定是**隔夜**。盤中已實現變異數不含收盤到開盤的那一段，但 GARCH 類模型配適的是"
            "收盤對收盤報酬。兩者若不統一，比較的就是兩個不同的量，QLIKE 會因為定義差異懲罰 GARCH，"
            "而不是因為它預測得比較差。本研究把隔夜項併入目標。\n\n"
            "### 公式\n\n"
            "設 $r_{t,j}$ 為第 $t$ 天第 $j$ 個五分鐘對數報酬、$r^{on}_t$ 為隔夜報酬、$M$ 為當天的日內筆數，"
            "則當日已實現變異數為\n\n"
            "$$RV_t = \\sum_{j=1}^{M} r_{t,j}^2 + (r^{on}_t)^2$$\n\n"
            "預測目標是在第 $t$ 天收盤形成的未來五日年化已實現波動率\n\n"
            "$$\\sigma_{t,t+5} = \\sqrt{\\frac{252}{5} \\sum_{i=1}^{5} RV_{t+i}}$$\n\n"
            "### 演算法\n\n"
            "1. 以當天實際交易時段計算日內報酬（提早收盤日自然較少筆，不補也不刪）。\n"
            "2. 平方加總，加上隔夜報酬平方。\n"
            "3. 向前取五日平均、乘 252、開根號，得到年化波動率。\n"
            "4. 建模時對變異數取對數：波動率右偏且為正，對數讓殘差接近常態、也保證預測為正。\n\n"
            "### 程式設計邏輯\n\n"
            "資料檔裡 `lrv_d` 是**對數年化已實現變異數**、`y_hf` 是上式的目標。"
            "兩者之間存在一個恆等式，下面的程式用它當作第一個資料完整性檢查："
            "如果 `y_hf` 真的是未來五日平均 $RV$ 的平方根，那麼兩者的差應該是浮點誤差等級。"
            "這種**不需要知道正確答案就能執行的檢查**，是本教材反覆強調的工具。"
        ),
        en=(
            "### Principle\n\n"
            "Volatility is not observed. To forecast it we must first **proxy** it with something that is, "
            "and the choice of proxy determines what every later comparison means. The squared daily return "
            "is the cheapest proxy and the noisiest; realized variance, summed from intraday returns, is far "
            "more accurate.\n\n"
            "Sampling frequency is a trade-off: finer sampling raises microstructure bias (bid-ask bounce, "
            "stale quotes), coarser sampling raises sampling error. Five minutes is the convention and sits "
            "near the balance for a highly liquid asset.\n\n"
            "The second decision is the **overnight** period. Intraday realized variance excludes the close-"
            "to-open move, but GARCH-type models are fitted to close-to-close returns. Leaving the two "
            "definitions unaligned compares different quantities, and QLIKE then penalises GARCH for a "
            "definitional difference rather than for forecasting worse. This study adds the overnight term "
            "to the target.\n\n"
            "### Formulas\n\n"
            "With $r_{t,j}$ the $j$-th five-minute log return on day $t$, $r^{on}_t$ the overnight return and "
            "$M$ the number of intraday observations that day, daily realized variance is\n\n"
            "$$RV_t = \\sum_{j=1}^{M} r_{t,j}^2 + (r^{on}_t)^2$$\n\n"
            "and the target, formed at the close of day $t$, is the annualized realized volatility of the "
            "following week\n\n"
            "$$\\sigma_{t,t+5} = \\sqrt{\\frac{252}{5} \\sum_{i=1}^{5} RV_{t+i}}$$\n\n"
            "### Algorithm\n\n"
            "1. Compute intraday returns over the session actually traded (a half day simply has fewer "
            "observations; it is neither padded nor dropped).\n"
            "2. Square and sum, then add the squared overnight return.\n"
            "3. Average the next five days, multiply by 252 and take the square root.\n"
            "4. Model the variance in logs: volatility is positive and right-skewed, so logs make the "
            "residuals closer to normal and keep the forecast positive.\n\n"
            "### Program logic\n\n"
            "In the data file `lrv_d` is the **log annualized realized variance** and `y_hf` is the target "
            "above. An identity connects them, and the cell below uses it as the first data-integrity check: "
            "if `y_hf` really is the square root of the forward five-day mean of $RV$, the difference should "
            "be at floating-point level. A check that **runs without knowing the right answer in advance** is "
            "a tool this notebook returns to repeatedly."
        ),
    ),
    code(
        """
# Identity check: y_hf must equal sqrt(mean of the next five days of annualized RV).
rv_ann = np.exp(D["lrv_d"])                      # lrv_d is log annualized realized variance
fwd5 = rv_ann.rolling(5).mean().shift(-5)        # mean of days t+1 .. t+5
gap = (np.sqrt(fwd5) - D["y_hf"]).abs()

print(f"max |sqrt(forward 5-day mean RV) - y_hf| = {gap.max():.2e}  over {gap.notna().sum()} days")
print(f"mean annualized volatility (y_hf)        = {D['y_hf'].mean():.3f}")
print(f"overnight share of total variance        = "
      f"{((D['r_on'] / 100) ** 2 * 252).sum() / rv_ann.sum():.1%} (sum basis), "
      f"{(((D['r_on'] / 100) ** 2 * 252) / rv_ann).median():.1%} (daily median)")

reg.check_count("N_total", int(((D.index >= '2011-01-04') & (D.index <= '2025-12-31')).sum()))
"""
    ),
    code(
        """
fig, ax = plt.subplots(figsize=(9, 2.8))
ax.plot(D.index, D["y_hf"] * 100, lw=0.7, color="#3a6ea5")
for a, b, c in [("2011-01-04", "2020-12-31", "#eef3f8"), ("2021-01-01", "2022-12-31", "#fdf3e3"),
                ("2023-01-01", "2025-12-31", "#eaf5ec"), ("2026-01-01", "2026-09-14", "#f7eaea")]:
    ax.axvspan(pd.Timestamp(a), pd.Timestamp(b), color=c, zorder=0)
ax.set_ylabel("annualized volatility (%)")
ax.set_title("Target y_hf, with estimation / validation / evaluation / hold-out shaded")
ax.set_xlim(D.index.min(), D.index.max())
plt.show()
"""
    ),
    unit_header("F2", "預測變數區塊與共線性", "Predictor blocks and collinearity",
                "build_dataset.py, groups.json", "Patton and Sheppard (2015); Corsi (2009)", "F1"),
    bi(
        zh=(
            "### 原理\n\n"
            "F1 只給了波動率自己的歷史。但波動率的可預測資訊不只來自它自己：下跌與跳躍、選擇權市場的前瞻定價、"
            "利率與跨資產報酬，都可能有增額內容。問題是這些變數彼此高度相關，直接全部丟進迴歸會讓係數不穩、"
            "符號亂跳——**這不是預測問題，是解釋問題**，但它會讓「哪個變數有用」的討論失去意義。\n\n"
            "本研究把 18 個變數編成 7 個區塊，之後的分解與 Granger 檢定都以**區塊**為單位，而不是單一變數。\n\n"
            "### 公式\n\n"
            "共線性用變異數膨脹因子 (variance inflation factor) 衡量。把第 $j$ 個變數對其餘所有變數迴歸，"
            "得到判定係數 $R_j^2$，則\n\n"
            "$$VIF_j = \\frac{1}{1 - R_j^2}$$\n\n"
            "VIF 為 10 大致對應 $R_j^2 = 0.9$。\n\n"
            "### 演算法\n\n"
            "兩個隱含波動率指數 VIX 與 VIX9D 在對數變異數形式下幾乎共線。本研究不是刪掉其中一個，"
            "而是做**線性重新參數化**：以水準 $\\log VIX^2$ 與斜率 $\\log(VIX9D / VIX)$ 取代兩個變異數。"
            "因為是線性變換，迴歸的配適值完全不變，但個別係數變得可解釋、VIF 大幅下降。\n\n"
            "### 程式設計邏輯\n\n"
            "下面同時做三件事：算兩種參數化的 VIF、驗證「配適值完全相同」這個主張、"
            "並用同一個指標檢查第二標的所用的相對報酬：換成原始報酬時，共線性會推高到什麼程度。"
            "注意 VIF 要在**哪一個設計矩陣**下計算會影響數值——這一點稿件沒有寫明，"
            "重現時必須自己找出來，下一格會示範這個過程。"
        ),
        en=(
            "### Principle\n\n"
            "F1 supplies only volatility's own history. Predictable information comes from elsewhere too: "
            "downside moves and jumps, the forward-looking prices in the option market, interest rates and "
            "cross-asset returns. The difficulty is that these variables are correlated with one another, so "
            "entering them all makes coefficients unstable and signs flip. **That is an interpretation "
            "problem rather than a forecasting one**, but it makes any discussion of which variable matters "
            "meaningless.\n\n"
            "This study groups 18 variables into 7 blocks, and both the decomposition and the Granger tests "
            "later work at **block** level rather than variable level.\n\n"
            "### Formulas\n\n"
            "Collinearity is measured by the variance inflation factor. Regress variable $j$ on all the "
            "others, obtain $R_j^2$, then\n\n"
            "$$VIF_j = \\frac{1}{1 - R_j^2}$$\n\n"
            "A VIF of 10 corresponds roughly to $R_j^2 = 0.9$.\n\n"
            "### Algorithm\n\n"
            "The two implied volatility indices, VIX and VIX9D, are nearly collinear in log variance form. "
            "Rather than dropping one, the study applies a **linear reparameterization**: the level "
            "$\\log VIX^2$ and the slope $\\log(VIX9D / VIX)$ replace the two variances. Because the "
            "transformation is linear the fitted values are unchanged, but the individual coefficients become "
            "interpretable and the inflation factors fall sharply.\n\n"
            "### Program logic\n\n"
            "The cell below does three things at once: computes the inflation factors under both "
            "parameterizations, verifies the claim that fitted values are identical, and checks whether the "
            "relative return used for the second asset really is less correlated than the raw return. Note "
            "that **which design matrix** the factors are computed in changes the numbers; the manuscript "
            "does not say which, so the reproduction has to find out, as the next cell shows."
        ),
    ),
    code(
        """
HAR = GROUPS["G1 歷史已實現變異"]
OPT = GROUPS["G3 選擇權前瞻"]
FEATS = [c for g in GROUPS.values() for c in g]
EST = (D.index >= "2011-01-04") & (D.index <= "2020-12-31")

print("blocks and variables")
for name, cols in GROUPS.items():
    print(f"  {name:22s} {cols}")
print(f"\\ntotal predictors: {len(FEATS)}")


def vif(X, j):
    \"\"\"VIF from the auxiliary regression of column j on the rest; written out rather than
    imported so the formula and the code sit next to each other.\"\"\"
    y_j = X[:, j]
    Z = np.c_[np.ones(len(X)), np.delete(X, j, axis=1)]
    b = np.linalg.lstsq(Z, y_j, rcond=None)[0]
    resid = y_j - Z @ b
    r2 = 1 - (resid @ resid) / (((y_j - y_j.mean()) ** 2).sum())
    return 1 / (1 - r2)


def both_parameterizations(cols, mask):
    sub = D[mask][cols].dropna()
    X_ls = sub.values                                   # level and slope (the paper's choice)
    i_lv, i_sl = cols.index("lvix"), cols.index("vix_slope")
    X_vv = X_ls.copy()
    X_vv[:, i_sl] = X_ls[:, i_lv] + 2 * X_ls[:, i_sl]   # log VIX9D^2 = log VIX^2 + 2 log(VIX9D/VIX)
    return (vif(X_ls, i_lv), vif(X_ls, i_sl), vif(X_vv, i_lv), vif(X_vv, i_sl), len(sub))
"""
    ),
    bi(
        zh=(
            "### 找出稿件數字是在哪個設計下算的\n\n"
            "稿件報告的 VIF 是 6.3 與 1.6（水準＋斜率）、26.9 與 24.6（兩個變異數），"
            "但沒有說是在哪一個迴歸設計、哪一段樣本上算的。重現時不可以調參數去湊，"
            "正確做法是把合理的候選設定全部列出來，看哪一個完全吻合。"
        ),
        en=(
            "### Finding out which design the manuscript's numbers come from\n\n"
            "The manuscript reports inflation factors of 6.3 and 1.6 (level and slope) and 26.9 and 24.6 "
            "(two variances), without saying in which regression design or over which sample. The "
            "reproduction must not tune until it matches; the right move is to enumerate the defensible "
            "candidates and see which one agrees exactly."
        ),
    ),
    code(
        """
ALL = (D.index >= "2011-01-04") & (D.index <= "2025-12-31")
cands = {
    "all 18 predictors, estimation sample": (FEATS, EST),
    "all 18 predictors, 2011-2025": (FEATS, ALL),
    "HAR + option block, estimation sample": (HAR + OPT, EST),
    "HAR + option block, 2011-2025": (HAR + OPT, ALL),
}
rows = []
for lab, (cols, mask) in cands.items():
    lv, sl, vv1, vv2, n = both_parameterizations(cols, mask)
    rows.append(dict(design=lab, n=n, VIF_level=lv, VIF_slope=sl, VIF_logVIX2=vv1, VIF_logVIX9D2=vv2))
tab = pd.DataFrame(rows).set_index("design").round(1)
print(tab.to_string())
print("\\nmanuscript: level 6.3, slope 1.6, logVIX2 26.9, logVIX9D2 24.6")

match = tab.loc["HAR + option block, estimation sample"]
reg.check("VIF_level", match.VIF_level, note="design inferred: HAR plus option block, estimation sample")
reg.check("VIF_slope", match.VIF_slope, note="design inferred: same specification as VIF_level")
reg.check("VIF_vix_raw", match.VIF_logVIX2, note="design inferred: same specification as VIF_level")
reg.check("VIF_vix9d_raw", match.VIF_logVIX9D2, note="design inferred: same specification as VIF_level")
"""
    ),
    code(
        """
# The reparameterization is linear, so the fitted values must be identical to machine precision.
sub = D[EST][HAR + OPT + ["y_hf"]].dropna()
X_ls = sub[HAR + OPT].values
i_lv, i_sl = (HAR + OPT).index("lvix"), (HAR + OPT).index("vix_slope")
X_vv = X_ls.copy()
X_vv[:, i_sl] = X_ls[:, i_lv] + 2 * X_ls[:, i_sl]
y_log = np.log(sub["y_hf"].values)


def fitted(X):
    Z = np.c_[np.ones(len(X)), X]
    return Z @ np.linalg.lstsq(Z, y_log, rcond=None)[0]


diff = np.abs(fitted(X_ls) - fitted(X_vv)).max()
print(f"max |fitted difference| between the two parameterizations = {diff:.2e}")
reg.check_text("reparam_identical", diff < 1e-10, f"max gap {diff:.1e}")

corr_iv = np.corrcoef(X_vv[:, i_lv], X_vv[:, i_sl])[0, 1]
print(f"corr(log VIX^2, log VIX9D^2) on the estimation sample = {corr_iv:.3f}")
reg.check("corr_vix_vix9d", corr_iv)

# The same argument for the second application, again in inflation factors rather than
# correlations: the design is the daily-only predictor set of Section 8.
dS = pd.read_csv(DATA / "daily_SPY.csv", parse_dates=["Date"]).set_index("Date")
m = (dS.index >= "2011-01-04") & (dS.index <= "2020-12-31")
daily_cols = [c for c in dS.columns if c not in ("y", "ret_pct")]
sub2 = dS[m][daily_cols].dropna()
j_cross, j_own = daily_cols.index("r_rel"), daily_cols.index("r_cc")
X_rel = sub2.values
qqq = D["r_qqq"].reindex(sub2.index).values
fin = np.isfinite(qqq)
X_raw = X_rel[fin].copy()
X_raw[:, j_cross] = qqq[fin]                      # swap the relative return for the raw one
print(f"cross-asset variable as the relative return: VIF {vif(X_rel, j_cross):.2f}, "
      f"own return {vif(X_rel, j_own):.2f}")
print(f"cross-asset variable as the raw return     : VIF {vif(X_raw, j_cross):.2f}, "
      f"own return {vif(X_raw, j_own):.2f}")
print("manuscript: 1.1 and 2.8 against 7.5 and 10.1")
reg.check("VIF_rel", vif(X_rel, j_cross))
reg.check("VIF_own_rel", vif(X_rel, j_own))
reg.check("VIF_raw_qqq", vif(X_raw, j_cross))
reg.check("VIF_own_raw", vif(X_raw, j_own))
"""
    ),
    unit_header("F3", "樣本外評估協定", "Out-of-sample protocol",
                "ladder.py (windows), Section 3.6", "Chassot and Audrino (2026); Feng and Zhang (2025)", "F1"),
    bi(
        zh=(
            "### 原理\n\n"
            "F1 與 F2 給了資料，但「模型有多好」這個問題在樣本內沒有意義：參數越多、樣本內越好看。"
            "必須有一個**在估計時看不到評估期**的協定。\n\n"
            "多日目標帶來一個容易漏掉的陷阱：第 $t$ 天的目標用到第 $t+1$ 到 $t+5$ 天的資料。"
            "如果估計樣本一路延伸到評估期前一天，最後五個訓練目標就已經含有評估期的資訊——"
            "**訓練集偷看了測試集**。本研究的做法是把估計樣本的最後五個觀測整段丟掉（purging）。\n\n"
            "### 公式\n\n"
            "設評估年為 $Y$，估計樣本為 $\\lbrace t: t_0 \\le t \\le T_{Y-1} - 5 \\rbrace$，"
            "其中 $T_{Y-1}$ 是 $Y-1$ 年的最後一個交易日。每年重估一次，視窗向前展開 (expanding)。\n\n"
            "### 演算法\n\n"
            "1. 對每個評估年 $Y \\in \\lbrace 2023, 2024, 2025 \\rbrace$：估計樣本為 2011-01-04 至 $Y-1$ 年底，去尾五日。\n"
            "2. 在估計樣本上估計所有參數，包含標準化常數。\n"
            "3. 對 $Y$ 年逐日產生預測，不再更新參數。\n"
            "4. 把三年的預測接起來，得到 752 天的評估序列。\n\n"
            "**超參數**只在第一個視窗的驗證區間（2021–2022）選一次，之後固定；"
            "保留樣本（2026）在設計定案前就先封存，整篇論文只用一次。\n\n"
            "### 程式設計邏輯\n\n"
            "`windows()` 把這個協定寫成一個產生器，所有模型共用它——"
            "這是讓「資訊集合對等」成立的前提：**同樣的視窗、同樣的樣本、同樣的重估頻率**，"
            "差別只在看得到哪些變數。"
        ),
        en=(
            "### Principle\n\n"
            "F1 and F2 supply the data, but asking how good a model is has no meaning in sample: more "
            "parameters always look better there. A protocol is needed in which **estimation cannot see the "
            "evaluation period**.\n\n"
            "A multi-day target brings a trap that is easy to miss. The target at day $t$ uses days $t+1$ to "
            "$t+5$. If the estimation sample runs to the day before the evaluation period, its last five "
            "targets already contain evaluation-period information — **the training set has seen the test "
            "set**. The study drops the last five observations of each estimation sample (purging).\n\n"
            "### Formulas\n\n"
            "For evaluation year $Y$ the estimation sample is $\\lbrace t: t_0 \\le t \\le T_{Y-1} - 5 \\rbrace$, where "
            "$T_{Y-1}$ is the last trading day of year $Y-1$. The model is re-estimated once a year on an "
            "expanding window.\n\n"
            "### Algorithm\n\n"
            "1. For each evaluation year $Y \\in \\lbrace 2023, 2024, 2025 \\rbrace$: estimate on 2011-01-04 to the end "
            "of $Y-1$, less the final five days.\n"
            "2. Estimate every parameter, including standardization constants, on that sample only.\n"
            "3. Forecast each day of $Y$ without updating parameters.\n"
            "4. Concatenate the three years into the 752-day evaluation series.\n\n"
            "**Hyperparameters** are chosen once, on the validation block of the first window (2021-2022), "
            "then held fixed; the hold-out year (2026) is sealed before the design is frozen and used once.\n\n"
            "### Program logic\n\n"
            "`windows()` encodes the protocol as a generator shared by every model. That sharing is what "
            "makes information-set parity possible: **the same windows, the same samples, the same "
            "re-estimation frequency**, differing only in which variables each model may see."
        ),
    ),
    code(
        """
TEST_YEARS = (2023, 2024, 2025)
START = "2011-01-04"


def windows(years=TEST_YEARS, start=START):
    \"\"\"Yield (year, train_idx, test_idx). The [:-5] slice is the purge: the last five
    estimation targets would otherwise overlap the evaluation period.\"\"\"
    for Y in years:
        te = np.where((D.index >= f"{Y}-01-01") & (D.index <= f"{Y}-12-31"))[0]
        tr = np.where((D.index >= start) & (D.index <= f"{Y - 1}-12-31"))[0][:-5]
        yield Y, tr, te


split = {
    "Estimation 2011-2020": int(((D.index >= "2011-01-04") & (D.index <= "2020-12-31")).sum()),
    "Validation 2021-2022": int(((D.index >= "2021-01-01") & (D.index <= "2022-12-31")).sum()),
    "Evaluation 2023-2025": int(((D.index >= "2023-01-01") & (D.index <= "2025-12-31")).sum()),
    "Hold-out 2026": int((D.index >= "2026-01-01").sum()),
}
for k, v in split.items():
    print(f"  {k:24s} {v:5d}")

reg.check_count("N_est", split["Estimation 2011-2020"])
reg.check_count("N_val", split["Validation 2021-2022"])
reg.check_count("N_eval", split["Evaluation 2023-2025"])
reg.check_count("N_holdout", split["Hold-out 2026"])

for Y, tr, te in windows():
    print(f"  {Y}: train {len(tr):5d} days ending {D.index[tr[-1]].date()}  |  test {len(te)} days")
print("\\npurge check: the last training target must not overlap the first test day")
for Y, tr, te in windows():
    overlap = D.index[tr[-1]] + pd.Timedelta(days=0)
    print(f"  {Y}: last train index {D.index[tr[-1]].date()}, first test {D.index[te[0]].date()}, "
          f"gap {(D.index[te[0]] - D.index[tr[-1]]).days} calendar days")
"""
    ),
]
