# -*- coding: utf-8 -*-
"""Units C1-C7: losses, the two benchmark estimators, and the inference toolkit."""
from parts._helpers import bi, code, md, mono, unit_header

CELLS = [
    unit_header("C1", "代理變數穩健損失函數", "Proxy-robust loss functions",
                "evaluate.py (mse_var, qlike)", "Patton (2011); Taylor (2026)", "F1"),
    bi(
        zh=(
            "### 原理\n\n"
            "F1 建好了目標，但目標只是**代理變數**：真正的潛在波動率沒人看得到。"
            "這帶來一個不明顯的危險——用錯損失函數時，代理變數的雜訊會讓**排序本身**偏掉，"
            "也就是說，比較的結果可能是雜訊造成的，而不是模型優劣造成的。\n\n"
            "Patton (2011) 刻畫了一族損失函數，在這族之內，即使用有雜訊的代理變數，"
            "期望損失的排序仍與用真實波動率時相同。平方誤差（變異數尺度）與 QLIKE 是其中最常用的兩個。"
            "本研究兩個都報，主要用 QLIKE。\n\n"
            "### 公式\n\n"
            "以 $\\sigma^2$ 表示代理的變異數、$\\hat{\\sigma}^2$ 表示預測，QLIKE 為\n\n"
            "$$L(\\sigma^2, \\hat{\\sigma}^2) = \\frac{\\sigma^2}{\\hat{\\sigma}^2} - "
            "\\log \\frac{\\sigma^2}{\\hat{\\sigma}^2} - 1$$\n\n"
            "它在 $\\hat{\\sigma}^2 = \\sigma^2$ 時為 0，且對**低估**的懲罰重於高估——"
            "這對風險管理是正確的方向。變異數尺度的平方誤差則是 "
            "$(\\sigma^2 - \\hat{\\sigma}^2)^2$，對高波動日的權重大得多。\n\n"
            "### 演算法\n\n"
            "1. 把預測與實現值都換算到**同一個尺度**（這裡是年化波動率，平方後成為變異數）。\n"
            "2. 逐日計算損失，取平均。\n"
            "3. 兩個損失函數都算：若兩者給出的排序不同，那本身就是結果的一部分。\n\n"
            "### 程式設計邏輯\n\n"
            "損失函數寫成純函數、接受向量，後面每一個檢定都重複使用它們。"
            "注意 `mse_var` 乘了 $10^8$ 只是為了讓數字好讀——**縮放不影響任何檢定**，"
            "但會影響表格的可讀性，所以把縮放寫在函數裡、而不是散落在輸出格式中。"
        ),
        en=(
            "### Principle\n\n"
            "F1 built the target, but the target is only a **proxy**: latent volatility is unobserved. That "
            "creates a danger which is not obvious — under the wrong loss function, proxy noise can distort "
            "**the ranking itself**, so that a comparison reflects noise rather than forecast quality.\n\n"
            "Patton (2011) characterised a family of loss functions under which the expected-loss ranking "
            "with a noisy proxy is the same as with true volatility. Squared error in variance units and "
            "QLIKE are its two best-known members. This study reports both and leads with QLIKE.\n\n"
            "### Formulas\n\n"
            "With $\\sigma^2$ the proxy variance and $\\hat{\\sigma}^2$ the forecast, QLIKE is\n\n"
            "$$L(\\sigma^2, \\hat{\\sigma}^2) = \\frac{\\sigma^2}{\\hat{\\sigma}^2} - "
            "\\log \\frac{\\sigma^2}{\\hat{\\sigma}^2} - 1$$\n\n"
            "It is zero when $\\hat{\\sigma}^2 = \\sigma^2$ and penalises **under-prediction** more heavily "
            "than over-prediction, which is the right direction for risk management. Squared error in "
            "variance units, $(\\sigma^2 - \\hat{\\sigma}^2)^2$, puts far more weight on high-volatility "
            "days.\n\n"
            "### Algorithm\n\n"
            "1. Put forecast and realisation on the **same scale** (here annualized volatility, squared into "
            "variance).\n"
            "2. Evaluate the loss day by day and average.\n"
            "3. Compute both losses: if they rank models differently, that disagreement is itself a result.\n\n"
            "### Program logic\n\n"
            "The losses are plain functions over vectors, reused by every test that follows. The factor of "
            "$10^8$ in `mse_var` only makes the numbers readable — **scaling changes no test** — and it "
            "lives inside the function rather than in print formatting so that every caller shares it."
        ),
    ),
    code(
        """
A = 252


def qlike(y, f):
    \"\"\"QLIKE on variances built from volatility inputs y and f.\"\"\"
    ratio = (y ** 2) / (f ** 2)
    return ratio - np.log(ratio) - 1


def mse_var(y, f):
    \"\"\"Squared error in variance units, scaled by 1e8 for readability only.\"\"\"
    return ((y ** 2 - f ** 2) ** 2) * 1e8


def rmse_vol(y, f):
    return np.sqrt(np.mean(((f - y) * 100) ** 2))


def mae_vol(y, f):
    return np.mean(np.abs((f - y) * 100))


# Why QLIKE is asymmetric: hold the realisation fixed and move the forecast.
sigma = 0.20
grid = np.linspace(0.08, 0.45, 200)
fig, ax = plt.subplots(figsize=(5.2, 2.6))
ax.plot(grid, qlike(np.full_like(grid, sigma), grid), label="QLIKE")
ax.plot(grid, mse_var(np.full_like(grid, sigma), grid) / 2e4, label="variance MSE (rescaled)")
ax.axvline(sigma, color="grey", lw=0.8)
ax.set_xlabel("forecast volatility")
ax.set_ylabel("loss")
ax.set_title("Loss against the forecast, realisation fixed at 0.20")
ax.legend()
plt.show()
print("QLIKE at half the truth :", f"{qlike(sigma, sigma / 2):.3f}")
print("QLIKE at twice the truth:", f"{qlike(sigma, sigma * 2):.3f}")
"""
    ),
    code(
        """
# The evaluation sample and the stored forecast series used throughout the notebook.
P = pd.read_csv(PRED / "pred_main_SPY.csv")
P.columns = [c.lstrip("\\ufeff") for c in P.columns]


def forecasts(target):
    \"\"\"Wide matrix of forecasts plus the realised target, for one target definition.

    The explicit filter on `target` matters: the file stacks y_hf and y_cc, and a pivot
    without it silently averages two different targets (see unit D2).\"\"\"
    g = P[P["target"] == target]
    W = g.pivot_table(index="date", columns="model", values="forecast")
    W.index = pd.to_datetime(W.index)
    y = g.groupby("date")["actual"].first()
    y.index = pd.to_datetime(y.index)
    assert len(W) == 752, f"expected 752 evaluation days, got {len(W)}"
    assert g.groupby(["date", "model"]).size().max() == 1, "duplicated (date, model) rows"
    return W, y


W, Y = forecasts("y_hf")
WB, YB = forecasts("y_cc")
MODELS = ["L0 Naive", "L1 GARCH(1,1)", "L1 GJR-GARCH", "L2 HAR-RV",
          "L3 HAR-RV-X (opt only)", "L3 HAR-RV-X (full)", "L3 GARCH-X", "L4 Transformer"]

tab = pd.DataFrame({
    "A: MAE": [mae_vol(Y, W[m]) for m in MODELS],
    "A: RMSE": [rmse_vol(Y, W[m]) for m in MODELS],
    "A: QLIKE": [qlike(Y, W[m]).mean() for m in MODELS],
    "B: QLIKE": [qlike(YB, WB[m]).mean() for m in MODELS],
}, index=MODELS)
print(tab.round(4).to_string())

reg.check("T51_qlike_L0", tab.loc["L0 Naive", "A: QLIKE"])
reg.check("T51_qlike_trf", tab.loc["L4 Transformer", "A: QLIKE"],
          note="computed from the stored ten-seed ensemble forecast; the network is not retrained here")
reg.check("T51_rmse_trf", tab.loc["L4 Transformer", "A: RMSE"], note="same")
reg.check("T51B_qlike_trf", tab.loc["L4 Transformer", "B: QLIKE"], note="same")
reg.check_text("T51_best_model",
               tab["A: QLIKE"].idxmin() == "L3 HAR-RV-X (full)" and tab["B: QLIKE"].idxmin() == "L3 HAR-RV-X (full)",
               "lowest QLIKE at both targets")
reg.check_text("T51_nonmonotone",
               tab.loc["L2 HAR-RV", "A: QLIKE"] > tab.loc["L1 GJR-GARCH", "A: QLIKE"],
               "HAR-RV above GJR-GARCH")
"""
    ),
    unit_header("C2", "HAR-RV 與對數尺度迴歸", "HAR-RV and regression on the log variance",
                "ladder.py (linreg)", "Corsi (2009); Taylor (2026)", "F1, F3"),
    bi(
        zh=(
            "### 原理\n\n"
            "C1 給了評分方式，但還沒有模型。波動率有長記憶：今天的波動與一個月前的波動仍然相關。"
            "完整的長記憶模型估計困難，Corsi (2009) 的異質自迴歸 (heterogeneous autoregressive, HAR) 用"
            "三個變數——昨日、過去五日平均、過去 22 日平均——就重現了長記憶的衰減形狀，而且是線性迴歸，"
            "幾百筆資料就估得動。\n\n"
            "### 公式\n\n"
            "以對數年化變異數為被解釋變數：\n\n"
            "$$\\log RV_{t+1:t+5} = \\beta_0 + \\beta_d \\log RV_t + \\beta_w \\log RV_{t-4:t} + "
            "\\beta_m \\log RV_{t-21:t} + \\varepsilon_{t}$$\n\n"
            "預測變異數時必須轉回原尺度。若 $\\varepsilon$ 近似常態且變異數為 $s^2$，則\n\n"
            "$$\\widehat{RV} = \\exp(\\hat{y} + s^2 / 2)$$\n\n"
            "這個 $s^2/2$ 是 Jensen 修正：少了它，預測會系統性偏低。\n\n"
            "### 演算法\n\n"
            "1. 取對數、用最小平方法估計；殘差變異數 $s^2$ 由估計樣本算出。\n"
            "2. 以 $\\exp(\\hat{y} + s^2/2)$ 轉回變異數，開根號得到波動率。\n"
            "3. 加入外生變數時**只改設計矩陣的欄位**，其餘一字不動——這是 K1 資訊集合對等的實作方式。\n\n"
            "### 程式設計邏輯\n\n"
            "下面刻意用 `np.linalg.lstsq` 而不是套件的迴歸物件：教學上要看見"
            "「係數 = 解正規方程式」這件事，而且它讓同一行程式服務三種資訊集合。\n\n"
            "**一個誠實的限制**：Taylor (2026) 指出，用對數模型建構、卻用相對損失（如 QLIKE）評估時，"
            "正確的轉換修正應同時取決於損失函數與誤差分布。這裡用的 $s^2/2$ 是高斯平方誤差下的修正，"
            "對 QLIKE 並非最適；但它對每一個以對數估計的階梯一視同仁，不偏袒比較的任一方。"
        ),
        en=(
            "### Principle\n\n"
            "C1 supplied the scoring rule but no model. Volatility has long memory: today's level is still "
            "correlated with a month ago. Estimating a full long-memory model is awkward, and the "
            "heterogeneous autoregressive (HAR) model of Corsi (2009) reproduces the decay with three "
            "regressors — yesterday, the past five days, the past 22 days — in a linear regression that a "
            "few hundred observations can estimate.\n\n"
            "### Formulas\n\n"
            "With the log annualized variance as the dependent variable:\n\n"
            "$$\\log RV_{t+1:t+5} = \\beta_0 + \\beta_d \\log RV_t + \\beta_w \\log RV_{t-4:t} + "
            "\\beta_m \\log RV_{t-21:t} + \\varepsilon_{t}$$\n\n"
            "Forecasting a variance requires transforming back. If $\\varepsilon$ is approximately normal "
            "with variance $s^2$, then\n\n"
            "$$\\widehat{RV} = \\exp(\\hat{y} + s^2 / 2)$$\n\n"
            "The $s^2/2$ is the Jensen correction; without it the forecast is systematically too low.\n\n"
            "### Algorithm\n\n"
            "1. Take logs, estimate by least squares, compute the residual variance $s^2$ on the estimation "
            "sample.\n"
            "2. Transform back with $\\exp(\\hat{y} + s^2/2)$ and take the square root for volatility.\n"
            "3. Adding exogenous variables **changes only the columns of the design matrix**, nothing else — "
            "this is how information-set parity (K1) is implemented.\n\n"
            "### Program logic\n\n"
            "`np.linalg.lstsq` is used deliberately rather than a regression object: the reader should see "
            "that the coefficients solve the normal equations, and the same line then serves three different "
            "information sets.\n\n"
            "**An honest limitation.** Taylor (2026) shows that when a forecast is built from a log model and "
            "evaluated with a relative loss such as QLIKE, the back-transformation should carry an adjustment "
            "depending on both the loss and the error distribution. The $s^2/2$ used here is the Gaussian "
            "squared-error correction, which is not loss-optimal for QLIKE; it applies identically to every "
            "rung estimated in logs, so it does not favour either side of the comparison."
        ),
    ),
    code(
        """
def linreg(target, cols, tr, te):
    \"\"\"OLS on the log target, back-transformed with the Jensen correction.

    Written from scratch (normal equations via lstsq) so the formula above and the code
    sit side by side; the estimation sample is passed in, never inferred here.\"\"\"
    X = np.c_[np.ones(len(D)), D[cols].values]
    y_log = np.log(D[target].values)
    ok = tr[np.isfinite(y_log[tr])]
    b = np.linalg.lstsq(X[ok], y_log[ok], rcond=None)[0]
    s2 = np.var(y_log[ok] - X[ok] @ b)
    return np.exp(X[te] @ b + 0.5 * s2)


def ladder_linear(target, cols):
    \"\"\"Run the protocol of F3 for one information set and stitch the years together.\"\"\"
    parts = [pd.Series(linreg(target, cols, tr, te), D.index[te]) for _, tr, te in windows()]
    return pd.concat(parts)


refit = {}
for name, cols in [("HAR-RV", HAR), ("HAR-RV-X (opt only)", HAR + OPT), ("HAR-RV-X (full)", FEATS)]:
    f = ladder_linear("y_hf", cols)
    y = D["y_hf"].reindex(f.index)
    refit[name] = dict(MAE=mae_vol(y, f), RMSE=rmse_vol(y, f), QLIKE=qlike(y, f).mean())
    refit[name + " | B"] = dict(QLIKE=qlike(D["y_cc"].reindex(f.index), ladder_linear("y_cc", cols)).mean())

print(pd.DataFrame(refit).T.round(4).to_string())
print("\\nmanuscript Table 5.1: HAR-RV 0.2318 | option only 0.1928 | full 0.1835")

reg.check("T51_qlike_har", refit["HAR-RV"]["QLIKE"])
reg.check("T51_qlike_harx_opt", refit["HAR-RV-X (opt only)"]["QLIKE"])
reg.check("T51_qlike_harx_full", refit["HAR-RV-X (full)"]["QLIKE"])
reg.check("T51_rmse_harx_full", refit["HAR-RV-X (full)"]["RMSE"])
reg.check("T51_mae_harx_opt", refit["HAR-RV-X (opt only)"]["MAE"])
reg.check("T51B_qlike_harx_full", refit["HAR-RV-X (full) | B"]["QLIKE"])
"""
    ),
    code(
        """
# What the coefficients look like, and why the Jensen correction is not cosmetic.
tr_last = list(windows())[-1][1]
X = np.c_[np.ones(len(D)), D[HAR].values]
y_log = np.log(D["y_hf"].values)
ok = tr_last[np.isfinite(y_log[tr_last])]
b = np.linalg.lstsq(X[ok], y_log[ok], rcond=None)[0]
s2 = np.var(y_log[ok] - X[ok] @ b)
print("HAR coefficients on the 2025 window:",
      dict(zip(["const"] + HAR, np.round(b, 4))), f"| s2 = {s2:.4f}")

te_all = np.where((D.index >= "2023-01-01") & (D.index <= "2025-12-31"))[0]
with_corr = ladder_linear("y_hf", HAR)
without = np.exp(np.c_[np.ones(len(D)), D[HAR].values][te_all] @ b)      # no s2/2, last window's b
print(f"QLIKE with the Jensen correction   : {qlike(D['y_hf'].reindex(with_corr.index), with_corr).mean():.4f}")
print(f"QLIKE without it (same window's b) : "
      f"{qlike(D['y_hf'].values[te_all], without).mean():.4f}   <- biased low, worse loss")
"""
    ),
    unit_header("C3", "GARCH 與 GJR-GARCH", "GARCH and GJR-GARCH with Student-t errors",
                "ladder.py (garch)", "Engle (1982); Glosten et al. (1993); Hansen and Lunde (2005)", "F1, F3"),
    bi(
        zh=(
            "### 原理\n\n"
            "C2 的 HAR 需要日內資料才能建出 $RV$。但有一整類模型**只用日報酬**就能描述波動叢聚，"
            "那就是 GARCH。它在本研究裡是資訊階梯的第一層：代表「只有日報酬」這個資訊集合。\n\n"
            "GARCH(1,1) 對稱地看待正負報酬，但股價下跌後的波動通常高於同幅度上漲之後——槓桿效果。"
            "GJR-GARCH 加一個只在負報酬時啟動的項來捕捉它。Hansen and Lunde (2005) 的大規模比較發現"
            "沒有模型顯著勝過簡單的 GARCH(1,1)；本研究的結果顯示**非對稱版本是很難打敗的基準**。\n\n"
            "### 公式\n\n"
            "$$h_t = \\omega + (\\alpha + \\gamma I[\\varepsilon_{t-1} < 0]) \\varepsilon_{t-1}^2 + \\beta h_{t-1}$$\n\n"
            "$\\gamma = 0$ 時退化為 GARCH(1,1)。持續性為 $\\alpha + \\gamma/2 + \\beta$，"
            "必須小於 1 才定態。誤差用 Student-t 分布以容納厚尾。\n\n"
            "多步預測由遞迴得到，再把五天的條件變異數相加、年化、開根號，換算成與目標同尺度的波動率。\n\n"
            "### 演算法\n\n"
            "1. 以最大概似估計 $(\\omega, \\alpha, \\gamma, \\beta, \\nu)$。\n"
            "2. 用 `last_obs` 告訴套件哪一天之後不得使用——這是把 F3 的協定落實到套件呼叫上。\n"
            "3. 對評估期每一天做 5 步預測，加總五天的變異數。\n\n"
            "### 程式設計邏輯\n\n"
            "這裡用 `arch` 套件而非自己寫 MLE，因為這是標準估計；真正需要從零實作的是 K3 的 GARCH-X"
            "（套件沒有那個規格）。報酬以**百分比**輸入是 `arch` 的慣例，數值條件較好；"
            "輸出要除以 100 才回到小數尺度，這種單位轉換是最常見的錯誤來源之一。"
        ),
        en=(
            "### Principle\n\n"
            "The HAR model of C2 needs intraday data to build $RV$. An entire model class describes "
            "volatility clustering from **daily returns alone**: GARCH. In this study it is the first rung of "
            "the ladder, representing the information set that contains only daily returns.\n\n"
            "GARCH(1,1) treats positive and negative returns symmetrically, yet volatility after a fall is "
            "typically higher than after a rise of the same size — the leverage effect. GJR-GARCH adds a term "
            "that switches on only for negative shocks. Hansen and Lunde (2005) found no specification that "
            "significantly beat a plain GARCH(1,1); in this study the asymmetric version is **a benchmark "
            "that is hard to beat**.\n\n"
            "### Formulas\n\n"
            "$$h_t = \\omega + (\\alpha + \\gamma I[\\varepsilon_{t-1} < 0]) \\varepsilon_{t-1}^2 + \\beta h_{t-1}$$\n\n"
            "Setting $\\gamma = 0$ gives GARCH(1,1). Persistence is $\\alpha + \\gamma/2 + \\beta$ and must be "
            "below one for stationarity. The errors are Student-t to accommodate fat tails.\n\n"
            "Multi-step forecasts follow from the recursion; the five conditional variances are summed, "
            "annualized and square-rooted onto the scale of the target.\n\n"
            "### Algorithm\n\n"
            "1. Estimate $(\\omega, \\alpha, \\gamma, \\beta, \\nu)$ by maximum likelihood.\n"
            "2. Pass `last_obs` so the library knows which day estimation may not see — this is how the F3 "
            "protocol reaches into the library call.\n"
            "3. Produce five-step forecasts for every evaluation day and sum the five variances.\n\n"
            "### Program logic\n\n"
            "The `arch` package is used rather than a hand-written likelihood because this is a standard "
            "estimator; the specification that genuinely needs writing from scratch is the GARCH-X of K3, "
            "which no package provides. Returns enter in **percent**, the package's convention and better "
            "conditioned numerically; the output is divided by 100 to return to decimals. Unit conversions "
            "like this are among the most common sources of silent error."
        ),
    ),
    code(
        """
from arch import arch_model


def garch_ladder(gjr):
    \"\"\"Refit GARCH per evaluation year under exactly the protocol of F3.\"\"\"
    parts, params = [], {}
    for Y, tr, te in windows():
        r = D["ret_pct"].iloc[tr[0]:te[-1] + 1]
        am = arch_model(r, mean="Constant", vol="GARCH", p=1, o=1 if gjr else 0, q=1, dist="t")
        res = am.fit(last_obs=D.index[tr[-1]] + pd.Timedelta(days=1), disp="off")
        fc = res.forecast(horizon=5, start=D.index[te[0]], reindex=False).variance.reindex(D.index[te])
        parts.append(pd.Series(np.sqrt(A / 5 * fc.sum(axis=1).values) / 100, D.index[te]))
        params[Y] = res.params.to_dict()
    return pd.concat(parts), params


f_g11, p_g11 = garch_ladder(False)
f_gjr, p_gjr = garch_ladder(True)
y = D["y_hf"].reindex(f_gjr.index)

print(f"GARCH(1,1) QLIKE {qlike(y, f_g11).mean():.4f}   manuscript 0.2340")
print(f"GJR-GARCH  QLIKE {qlike(y, f_gjr).mean():.4f}   manuscript 0.1998")
print("\\nGJR parameters by window (note gamma > alpha: the asymmetry does the work)")
print(pd.DataFrame(p_gjr).T.round(4).to_string())
persist = {Y: p["alpha[1]"] + p.get("gamma[1]", 0) / 2 + p["beta[1]"] for Y, p in p_gjr.items()}
print("persistence:", {k: round(v, 4) for k, v in persist.items()})

reg.check("T51_qlike_g11", qlike(y, f_g11).mean())
reg.check("T51_qlike_gjr", qlike(y, f_gjr).mean())
"""
    ),
    unit_header("C4", "Diebold-Mariano 檢定與 HLN 校正", "Diebold-Mariano with the HLN correction",
                "evaluate.py (hac_var, dm_hln)", "Diebold and Mariano (1995); Harvey et al. (1997)", "C1"),
    bi(
        zh=(
            "### 原理\n\n"
            "C1 到 C3 讓我們能算出兩個模型的平均損失誰比較小，但**小多少才算真的比較好**？"
            "直接比大小等於假設沒有抽樣誤差。DM 檢定把這個問題變成對損失差序列均值的檢定。\n\n"
            "多日目標讓相鄰的損失差自動相關（第 $t$ 天與第 $t+1$ 天的目標共用四天），"
            "所以標準誤必須用 HAC 估計；小樣本下統計量還會偏大，HLN 校正處理這一點。\n\n"
            "### 公式\n\n"
            "令 $d_t = L(y_t, f_{1t}) - L(y_t, f_{2t})$，則\n\n"
            "$$DM = \\frac{\\bar{d}}{\\sqrt{\\hat{V}(\\bar{d})}}, \\quad "
            "\\hat{V}(\\bar{d}) = \\frac{1}{T}\\left(\\gamma_0 + 2\\sum_{k=1}^{h-1} w_k \\gamma_k\\right)$$\n\n"
            "其中 $w_k = 1 - k/(h+1)$ 為 Bartlett 權重、$\\gamma_k$ 為自我共變異數。HLN 校正因子為\n\n"
            "$$c = \\sqrt{\\frac{T + 1 - 2h + h(h-1)/T}{T}}$$\n\n"
            "校正後的統計量對照自由度 $T-1$ 的 t 分布。\n\n"
            "### 演算法\n\n"
            "1. 計算逐日損失差。\n"
            "2. 以 Bartlett 核估 HAC 變異數，落後期取 $h = 5$（目標的重疊長度）。\n"
            "3. 乘上 HLN 因子，查 t 分布。\n\n"
            "### 程式設計邏輯\n\n"
            "`hac_var` 只有五行，刻意不呼叫 statsmodels：讀者要看到 Bartlett 權重長什麼樣子。"
            "重疊造成的變異數膨脹倍數，相對於獨立情形，之後在 D2 會再用到。"
        ),
        en=(
            "### Principle\n\n"
            "C1 to C3 let us say which model has the lower average loss, but **how much lower counts as "
            "genuinely better**? Comparing the averages alone assumes away sampling error. The DM test turns "
            "the question into a test on the mean of the loss-difference series.\n\n"
            "A multi-day target makes neighbouring loss differences autocorrelated by construction (the "
            "targets at $t$ and $t+1$ share four days), so the standard error must be HAC; in small samples "
            "the statistic is also too large, which the HLN correction addresses.\n\n"
            "### Formulas\n\n"
            "With $d_t = L(y_t, f_{1t}) - L(y_t, f_{2t})$,\n\n"
            "$$DM = \\frac{\\bar{d}}{\\sqrt{\\hat{V}(\\bar{d})}}, \\quad "
            "\\hat{V}(\\bar{d}) = \\frac{1}{T}\\left(\\gamma_0 + 2\\sum_{k=1}^{h-1} w_k \\gamma_k\\right)$$\n\n"
            "where $w_k = 1 - k/(h+1)$ are Bartlett weights and $\\gamma_k$ the autocovariances. The HLN "
            "factor is\n\n"
            "$$c = \\sqrt{\\frac{T + 1 - 2h + h(h-1)/T}{T}}$$\n\n"
            "and the corrected statistic is compared with a t distribution on $T-1$ degrees of freedom.\n\n"
            "### Algorithm\n\n"
            "1. Compute the daily loss differences.\n"
            "2. Estimate the HAC variance with a Bartlett kernel and $h = 5$ lags, the overlap of the "
            "target.\n"
            "3. Multiply by the HLN factor and read off the t distribution.\n\n"
            "### Program logic\n\n"
            "`hac_var` is five lines and deliberately does not call statsmodels: the reader should see what "
            "the Bartlett weights do. The variance inflation it implies, relative to the independent case, "
            "comes back in unit D2."
        ),
    ),
    code(
        """
from scipy.stats import t as tdist, norm


def hac_var(d, lag):
    \"\"\"Newey-West long-run variance with Bartlett weights, written out in full.\"\"\"
    T = len(d)
    dc = d - d.mean()
    v = dc @ dc / T
    for k in range(1, lag + 1):
        v += 2 * (1 - k / (lag + 1)) * (dc[k:] @ dc[:-k]) / T
    return v


def dm_hln(y, f1, f2, loss=qlike, h=5):
    \"\"\"Negative statistic favours f1. Returns (statistic, two-sided p).\"\"\"
    d = np.asarray(loss(y, f1) - loss(y, f2), dtype=float)
    T = len(d)
    stat = d.mean() / np.sqrt(hac_var(d, h) / T)
    stat *= np.sqrt((T + 1 - 2 * h + h * (h - 1) / T) / T)
    return stat, 2 * (1 - tdist.cdf(abs(stat), T - 1))


pairs = [("L4 Transformer", "L1 GARCH(1,1)", "T53_dq_trf_g11", None),
         ("L4 Transformer", "L1 GJR-GARCH", "T53_dq_trf_gjr", "T53_p_trf_gjr"),
         ("L4 Transformer", "L3 HAR-RV-X (full)", "T53_dq_trf_harx", "T53_p_trf_harx"),
         ("L3 HAR-RV-X (full)", "L2 HAR-RV", "T53_dq_harx_har", "T53_p_harx_har")]
rows = []
for a, b, fid_d, fid_p in pairs:
    stat, p = dm_hln(Y, W[a], W[b])
    dq = qlike(Y, W[a]).mean() - qlike(Y, W[b]).mean()
    rows.append(dict(comparison=f"{a} vs {b}", dQLIKE=dq, DM=stat, p=p))
    if fid_d and fid_d in reg.rows:
        reg.check(fid_d, dq)
    if fid_p:
        reg.check(fid_p, p)
print(pd.DataFrame(rows).round(4).to_string(index=False))
"""
    ),
    unit_header("C5", "Clark-West 巢狀檢定", "Clark-West test for nested models",
                "evaluate.py (clark_west)", "Clark and West (2007)", "C4"),
    bi(
        zh=(
            "### 原理\n\n"
            "C4 的 DM 檢定假設兩個模型**非巢狀**。但 HAR-RV 是 HAR-RV-X 的特例（把外生係數設為零），"
            "這時在虛無假設下大模型多估了幾個其實為零的參數，樣本外損失會被這些估計誤差推高，"
            "DM 檢定因此偏向保守——即使大模型真的有用也不容易顯著。\n\n"
            "Clark-West 把這個已知的偏誤加回去。\n\n"
            "### 公式\n\n"
            "$$\\hat{f}_t = (y_t - f_{s,t})^2 - \\left[(y_t - f_{b,t})^2 - (f_{s,t} - f_{b,t})^2\\right]$$\n\n"
            "其中 $f_s$ 為小模型、$f_b$ 為大模型。第三項就是修正：它扣掉因多估參數而產生的額外變異。"
            "統計量為 $\\bar{\\hat{f}}$ 除以其 HAC 標準誤，單尾檢定，正值支持大模型。\n\n"
            "### 演算法\n\n"
            "與 DM 幾乎相同，只是被平均的序列換成 $\\hat{f}_t$，而且是**單尾**。\n\n"
            "### 程式設計邏輯\n\n"
            "本研究在變異數尺度上做這個檢定（$y^2$ 與 $f^2$），與 Clark-West 原始設定的平方誤差一致。"
            "注意它回報的 p 值比 DM 小——這正是預期中的方向。"
        ),
        en=(
            "### Principle\n\n"
            "The DM test of C4 assumes the two models are **non-nested**. HAR-RV is a special case of "
            "HAR-RV-X (exogenous coefficients set to zero), and under the null the larger model estimates "
            "parameters that are truly zero. That estimation noise inflates its out-of-sample loss, so DM is "
            "conservative here: even a genuinely useful larger model struggles to look significant.\n\n"
            "Clark-West adds the known bias back.\n\n"
            "### Formulas\n\n"
            "$$\\hat{f}_t = (y_t - f_{s,t})^2 - \\left[(y_t - f_{b,t})^2 - (f_{s,t} - f_{b,t})^2\\right]$$\n\n"
            "with $f_s$ the small model and $f_b$ the large one. The third term is the correction: it removes "
            "the extra variance caused by estimating the additional parameters. The statistic is "
            "$\\bar{\\hat{f}}$ over its HAC standard error, one-sided, with positive values favouring the "
            "larger model.\n\n"
            "### Algorithm\n\n"
            "Almost identical to DM, except that the averaged series is $\\hat{f}_t$ and the test is "
            "**one-sided**.\n\n"
            "### Program logic\n\n"
            "The study runs this on the variance scale ($y^2$ and $f^2$), matching the squared-error setting "
            "of the original test. The p-values come out below the DM ones, which is the expected direction."
        ),
    ),
    code(
        """
def clark_west(y, f_small, f_big, h=5):
    fhat = ((y ** 2 - f_small ** 2) ** 2
            - ((y ** 2 - f_big ** 2) ** 2 - (f_small ** 2 - f_big ** 2) ** 2))
    fhat = np.asarray(fhat, dtype=float)
    T = len(fhat)
    stat = fhat.mean() / np.sqrt(hac_var(fhat, h) / T)
    return stat, 1 - norm.cdf(stat)


s_full, p_full = clark_west(Y, W["L2 HAR-RV"], W["L3 HAR-RV-X (full)"])
s_opt, p_opt = clark_west(Y, W["L2 HAR-RV"], W["L3 HAR-RV-X (opt only)"])
print(f"HAR-RV vs HAR-RV-X (full)        CW {s_full:.2f}  p {p_full:.3f}   manuscript 1.57 / 0.058")
print(f"HAR-RV vs HAR-RV-X (option only) CW {s_opt:.2f}  p {p_opt:.3f}   manuscript 1.63 / 0.052")
reg.check("CW_stat_full", s_full)
reg.check("CW_p_full", p_full)
reg.check("CW_stat_opt", s_opt)
reg.check("CW_p_opt", p_opt)
"""
    ),
    unit_header("C6", "移動區塊拔靴法", "Moving block bootstrap",
                "evaluate.py (block_boot_idx, boot_ci)", "Künsch (1989)", "C1"),
    bi(
        zh=(
            "### 原理\n\n"
            "C4 給了 p 值，但論文還需要**區間**：分解的三項各自有多大的不確定性。"
            "損失差有自我相關，直接對觀測重抽會破壞這個相關結構，低估變異。"
            "移動區塊拔靴法改成重抽**長度固定的連續區塊**，區塊內的相關結構被保留下來。\n\n"
            "### 公式\n\n"
            "設區塊長度 $\\ell$、樣本長度 $T$，需要 $\\lceil T/\\ell \\rceil$ 個區塊。"
            "每次重抽從 $\\lbrace 0, \\ldots, T-\\ell \\rbrace$ 均勻抽起點，串接後截到長度 $T$，"
            "計算統計量，重複 $B$ 次，取分位數為區間。\n\n"
            "### 演算法\n\n"
            "1. 選區塊長度：要長到涵蓋相關結構（這裡目標重疊五天，取 20 天），又不能長到區塊數太少。\n"
            "2. 產生 $B \\times T$ 的索引矩陣，一次完成所有重抽——向量化比迴圈快兩個數量級。\n"
            "3. 取 5% 與 95% 分位數。\n\n"
            "### 程式設計邏輯\n\n"
            "**一個重現性上的陷阱**：原始程式把亂數產生器放在模組層級，由多個函數共用。"
            "這表示重抽結果取決於**先前呼叫消耗了多少亂數**，光有種子不足以重現。"
            "下面示範這一點，並報告蒙地卡羅波動——這也解釋了為什麼稿件的區間端點在這裡只能近似重現。"
        ),
        en=(
            "### Principle\n\n"
            "C4 produced p-values, but the paper also needs **intervals**: how uncertain each of the three "
            "components is. Loss differences are autocorrelated, and resampling observations independently "
            "would destroy that structure and understate the variance. The moving block bootstrap resamples "
            "**contiguous blocks of fixed length** instead, preserving dependence within a block.\n\n"
            "### Formulas\n\n"
            "With block length $\\ell$ and sample length $T$, a replicate needs "
            "$\\lceil T/\\ell \\rceil$ blocks. Each start is drawn uniformly from $\\lbrace 0, \\ldots, T-\\ell \\rbrace$; "
            "the blocks are concatenated, truncated to $T$, the statistic recomputed, and this repeated $B$ "
            "times, with quantiles taken across replicates.\n\n"
            "### Algorithm\n\n"
            "1. Choose the block length: long enough to span the dependence (the target overlaps five days; "
            "20 is used) but short enough to leave many blocks.\n"
            "2. Build the whole $B \\times T$ index matrix at once — vectorising beats a loop by two orders "
            "of magnitude.\n"
            "3. Take the 5% and 95% quantiles.\n\n"
            "### Program logic\n\n"
            "**A reproducibility trap.** The original script keeps the random generator at module level, "
            "shared by several functions. The draws therefore depend on **how much randomness earlier calls "
            "consumed**, so the seed alone is not enough to reproduce them. The cell below demonstrates this "
            "and reports the Monte Carlo spread, which is why the manuscript's interval endpoints can only "
            "be reproduced approximately here."
        ),
    ),
    code(
        """
def block_boot_idx(T, B, block=20, rng=None):
    rng = rng or np.random.default_rng(7)
    nb = int(np.ceil(T / block))
    starts = rng.integers(0, T - block + 1, size=(B, nb))
    return (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(B, -1)[:, :T]


def boot_ci(x, B=5000, block=20, q=(5, 95), rng=None):
    idx = block_boot_idx(len(x), B, block, rng)
    return np.percentile(np.asarray(x)[idx].mean(1), q)


d_info = np.asarray(qlike(Y, W["L2 HAR-RV"]) - qlike(Y, W["L3 HAR-RV-X (full)"]))
lo, hi = boot_ci(d_info, rng=np.random.default_rng(7))
print(f"Delta_info 90% interval, fresh rng(7): [{lo:+.3f}, {hi:+.3f}]   manuscript [+0.017, +0.083]")

# How much of that gap is Monte Carlo noise? Repeat with twenty different streams.
ends = np.array([boot_ci(d_info, B=5000, rng=np.random.default_rng(s)) for s in range(20)])
print(f"across 20 streams: lower {ends[:, 0].mean():+.4f} +- {ends[:, 0].std():.4f}, "
      f"upper {ends[:, 1].mean():+.4f} +- {ends[:, 1].std():.4f}")
reg.not_verifiable("T52_ci_dinfo_A_lo",
                   "evaluate.py shares one module-level generator across calls, so the stream position when "
                   f"the published interval was drawn is not recoverable; fresh streams give {ends[:, 0].mean():+.3f} "
                   f"+- {ends[:, 0].std():.3f}")
reg.not_verifiable("T52_ci_dinfo_A_hi",
                   f"same reason; fresh streams give {ends[:, 1].mean():+.3f} +- {ends[:, 1].std():.3f}")
"""
    ),
    unit_header("C7", "模型信賴集合", "Model confidence set",
                "evaluate.py (mcs)", "Hansen, Lunde and Nason (2011)", "C4, C6"),
    bi(
        zh=(
            "### 原理\n\n"
            "C4 一次只比兩個模型。但本研究有八個模型，做 28 次成對比較會讓至少一次顯著的機率遠高於名目水準——"
            "多重檢定問題。模型信賴集合 (model confidence set) 直接回答另一個問題："
            "**在給定信心水準下，哪些模型不能被排除為最佳？**\n\n"
            "### 公式\n\n"
            "對現存模型集合 $\\mathcal{M}$，以全距統計量檢定「所有模型等優」：\n\n"
            "$$T_R = \\max_{i,j \\in \\mathcal{M}} \\frac{|\\bar{d}_{ij}|}{\\sqrt{\\widehat{var}(\\bar{d}_{ij})}}$$\n\n"
            "臨界值由 C6 的區塊拔靴法給出。若拒絕，刪掉最差的模型，重複；若不拒絕，剩下的就是信賴集合。\n\n"
            "### 演算法\n\n"
            "1. 計算所有兩兩損失差與其拔靴分布。\n"
            "2. 算 $T_R$ 與拔靴 p 值。\n"
            "3. p < $\\alpha$ 則剔除最差模型後重複，否則停止。\n\n"
            "### 程式設計邏輯\n\n"
            "拔靴索引**只產生一次**並在整個迴圈重複使用：每輪重抽會讓各輪的隨機性不可比，"
            "而且慢得多。這是效率與正確性恰好一致的少數情況。"
        ),
        en=(
            "### Principle\n\n"
            "C4 compares two models at a time. With eight models there are 28 pairs, and the chance that at "
            "least one looks significant far exceeds the nominal level — the multiple-testing problem. The "
            "model confidence set answers a different question directly: **which models cannot be excluded "
            "from being the best, at a given confidence level?**\n\n"
            "### Formulas\n\n"
            "For the surviving set $\\mathcal{M}$, the range statistic tests equal predictive ability:\n\n"
            "$$T_R = \\max_{i,j \\in \\mathcal{M}} \\frac{|\\bar{d}_{ij}|}{\\sqrt{\\widehat{var}(\\bar{d}_{ij})}}$$\n\n"
            "with critical values from the block bootstrap of C6. If the test rejects, the worst model is "
            "removed and the test repeated; when it stops rejecting, the survivors form the confidence set.\n\n"
            "### Algorithm\n\n"
            "1. Compute all pairwise loss differences and their bootstrap distribution.\n"
            "2. Form $T_R$ and the bootstrap p-value.\n"
            "3. If p is below $\\alpha$, eliminate the worst model and repeat; otherwise stop.\n\n"
            "### Program logic\n\n"
            "The bootstrap indices are drawn **once** and reused across the elimination loop: redrawing each "
            "round would make the rounds incomparable and is much slower. This is one of the cases where "
            "efficiency and correctness point the same way."
        ),
    ),
    code(
        """
def mcs(losses, alpha=0.10, B=2000, block=20, seed=7):
    \"\"\"Hansen-Lunde-Nason MCS with the range statistic.\"\"\"
    alive = list(losses.columns)
    idx = block_boot_idx(len(losses), B, block, np.random.default_rng(seed))
    trace = []
    while len(alive) > 1:
        X = losses[alive].values
        dbar = X.mean(0)
        boot = X[idx].mean(1)
        M = len(alive)
        t_stat = np.zeros((M, M))
        t_boot = np.zeros((B, M, M))
        for i in range(M):
            for j in range(M):
                if i == j:
                    continue
                dij = dbar[i] - dbar[j]
                bij = boot[:, i] - boot[:, j]
                v = max(np.var(bij - dij), 1e-18)
                t_stat[i, j] = dij / np.sqrt(v)
                t_boot[:, i, j] = (bij - dij) / np.sqrt(v)
        TR = np.max(np.abs(t_stat))
        p = (np.max(np.abs(t_boot), axis=(1, 2)) > TR).mean()
        trace.append((len(alive), round(float(p), 3)))
        if p >= alpha:
            break
        alive.remove(alive[int(np.argmax([np.max(t_stat[i]) for i in range(M)]))])
    return alive, trace


L_mat = pd.DataFrame({m: qlike(Y, W[m]) for m in MODELS})
alive, trace = mcs(L_mat)
print(f"models retained at the 90% level: {len(alive)} of {len(MODELS)}")
for m in alive:
    print("   ", m)
print("eliminated:", [m for m in MODELS if m not in alive])
print("trace (size, p):", trace)
reg.check_count("MCS_qlike_kept", len(alive))
"""
    ),
]
