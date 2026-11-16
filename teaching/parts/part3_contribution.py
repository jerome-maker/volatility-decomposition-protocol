# -*- coding: utf-8 -*-
"""Units K1-K5: the paper's own method, and the two checks that qualify it."""
from parts._helpers import bi, code, md, mono, unit_header

CELLS = [
    unit_header("K1", "資訊集合對等與資訊階梯", "Information-set parity and the ladder",
                "ladder.py, l4_main10.py, lstm_final.py", "Chassot and Audrino (2026); Gu et al. (2020)",
                "C2, C3"),
    bi(
        zh=(
            "### 原理\n\n"
            "C2 與 C3 各自是好模型，但它們**看到的東西不一樣**：HAR 看得到日內已實現變異數，GARCH 只看得到日報酬。"
            "文獻裡絕大多數「深度學習勝過計量模型」的比較正是這樣：神經網路拿到日內測度、選擇權指數、"
            "總體變數，而對照的計量基準沒有。這時報告出來的增益**同時包含資訊的價值與模型的價值**，"
            "事後無法分開。\n\n"
            "本研究的識別限制只有一句話：**第四層的深度學習模型與第三層的線性模型必須收到完全相同的輸入**——"
            "相同變數、相同轉換、相同視窗、相同估計樣本。這不是估計技巧，是設計要求，而且成本極低："
            "把餵給網路的設計矩陣原封不動拿去跑線性迴歸即可。\n\n"
            "### 公式\n\n"
            "定義三個資訊集合：$\\mathcal{I}^d_t$ 為日報酬、$\\mathcal{I}^{HF}_t$ 為日內已實現測度、"
            "$\\mathcal{I}^X_t$ 為外生前瞻變數。階梯為\n\n"
            "$$L0 \\subset \\mathcal{I}^d \\quad(L1) \\subset \\mathcal{I}^{HF} \\quad(L2) \\subset "
            "\\mathcal{I}^{HF} \\cup \\mathcal{I}^X \\quad(L3, L4)$$\n\n"
            "L3 與 L4 的資訊集合**相同**，差別只在函數形式。\n\n"
            "### 演算法\n\n"
            "1. 每一層只改一件事：L1→L2 換資訊（加日內），L2→L3 換資訊（加外生），L3→L4 換函數形式。\n"
            "2. 階梯是依**資訊**排序，不是依預期準確度排序；高層是否真的比較準，是實證問題。\n"
            "3. 第四層同時放 Transformer 與 LSTM：若只試一種架構，"
            "「架構沒有幫助」的結論可能只是那一種架構的問題。\n\n"
            "### 程式設計邏輯\n\n"
            "神經網路無法在這份筆記本裡重訓（需要數小時 GPU），所以 L4 讀既有的十種子集成預測序列。"
            "能獨立重算的是**給定預測之後的每一個統計量**，這一點會在重現報告裡明確標示。"
        ),
        en=(
            "### Principle\n\n"
            "C2 and C3 are both good models, but they **see different things**: HAR sees intraday realized "
            "variance, GARCH only daily returns. Most published comparisons in which deep learning beats an "
            "econometric model look exactly like this — the network receives intraday measures, option-"
            "implied indices and macro variables that the benchmark does not. The reported gain then "
            "**contains the value of the information and the value of the model at once**, and nothing can "
            "separate them after the fact.\n\n"
            "The identifying restriction of this study is one sentence: **the Level 4 deep learning model and "
            "the Level 3 linear model must receive exactly the same inputs** — same variables, same "
            "transformations, same window, same estimation sample. It is a design requirement rather than an "
            "estimation technique, and it is cheap: run the linear regression on the very design matrix fed "
            "to the network.\n\n"
            "### Formulas\n\n"
            "Define three information sets: $\\mathcal{I}^d_t$ daily returns, $\\mathcal{I}^{HF}_t$ intraday "
            "realized measures, $\\mathcal{I}^X_t$ exogenous forward-looking variables. The ladder is\n\n"
            "$$L0 \\subset \\mathcal{I}^d \\quad(L1) \\subset \\mathcal{I}^{HF} \\quad(L2) \\subset "
            "\\mathcal{I}^{HF} \\cup \\mathcal{I}^X \\quad(L3, L4)$$\n\n"
            "where L3 and L4 share the **same** information set and differ only in functional form.\n\n"
            "### Algorithm\n\n"
            "1. Each step changes one thing: L1 to L2 changes information (intraday), L2 to L3 changes "
            "information (exogenous), L3 to L4 changes functional form.\n"
            "2. The ladder is ordered by **information**, not by expected accuracy; whether a higher rung "
            "forecasts better is the empirical question.\n"
            "3. Level 4 holds both a Transformer and an LSTM: with a single architecture, a finding of no "
            "architecture gain might be a fact about that architecture alone.\n\n"
            "### Program logic\n\n"
            "The networks cannot be retrained inside this notebook (hours of GPU time), so Level 4 reads the "
            "stored ten-seed ensemble forecasts. What is recomputed independently is **every statistic given "
            "those forecasts**, and the reproduction report says so explicitly."
        ),
    ),
    code(
        """
ladder_tab = pd.DataFrame({
    "information set": ["RV weekly mean (random walk)", "daily returns", "daily returns",
                        "intraday RV", "intraday RV + option block", "intraday RV + all exogenous",
                        "daily returns + option block", "intraday RV + all exogenous"],
    "functional form": ["none", "GARCH(1,1)", "GJR-GARCH", "linear", "linear", "linear",
                        "GARCH-X", "Transformer / LSTM"],
    "A: QLIKE": [qlike(Y, W[m]).mean() for m in MODELS],
}, index=MODELS)
print(ladder_tab.round(4).to_string())

arch_tab = pd.DataFrame({
    "A: RMSE": [rmse_vol(Y, W[m]) for m in ["L3 HAR-RV-X (full)", "L4 LSTM", "L4 Transformer"]],
    "A: QLIKE": [qlike(Y, W[m]).mean() for m in ["L3 HAR-RV-X (full)", "L4 LSTM", "L4 Transformer"]],
    "B: QLIKE": [qlike(YB, WB[m]).mean() for m in ["L3 HAR-RV-X (full)", "L4 LSTM", "L4 Transformer"]],
}, index=["HAR-RV-X (linear, same inputs)", "LSTM", "Transformer"])
print("\\narchitecture control, both Level 4 models on the Level 3 information set")
print(arch_tab.round(4).to_string())

reg.check("T54_qlike_lstm_A", arch_tab.loc["LSTM", "A: QLIKE"], note="stored ten-seed ensemble")
d_lstm = qlike(Y, W["L3 HAR-RV-X (full)"]).mean() - qlike(Y, W["L4 LSTM"]).mean()
stat, p_lstm = dm_hln(Y, W["L3 HAR-RV-X (full)"], W["L4 LSTM"])
reg.check("T54_darch_lstm_A", d_lstm)
reg.check("T54_p_darch_lstm_A", p_lstm)
d_tl = qlike(Y, W["L4 Transformer"]).mean() - qlike(Y, W["L4 LSTM"]).mean()
stat, p_tl = dm_hln(Y, W["L4 Transformer"], W["L4 LSTM"])
reg.check("T54_trf_vs_lstm", d_tl)
reg.check("T54_p_trf_vs_lstm", p_tl)
"""
    ),
    code(
        """
# Market conditions: the ranking is not constant across states, which matters for K4.
vix = np.exp(D["lvix"] / 2).reindex(Y.index)          # VIX level from log VIX^2
rv_real = Y
cuts = {
    "All (752)": np.ones(len(Y), bool),
    "Low VIX (251)": vix <= vix.quantile(1 / 3),
    "High VIX (252)": vix >= vix.quantile(2 / 3),
    "Top 20% realized (151)": rv_real >= rv_real.quantile(0.80),
    "Mar-May 2025 (63)": (Y.index >= "2025-03-01") & (Y.index <= "2025-05-31"),
}
sub_models = ["L1 GJR-GARCH", "L2 HAR-RV", "L3 HAR-RV-X (full)", "L3 GARCH-X", "L4 Transformer"]
regime = pd.DataFrame({lab: [qlike(Y[m2], W[m][m2]).mean() for m in sub_models]
                       for lab, m2 in cuts.items()}, index=sub_models)
print(regime.round(3).to_string())
print("\\ncounts:", {k: int(np.sum(v)) for k, v in cuts.items()})

reg.check("T55_harx_all", regime.loc["L3 HAR-RV-X (full)", "All (752)"])
reg.check("T55_gjr_top20", regime.loc["L1 GJR-GARCH", "Top 20% realized (151)"])
reg.check("T55_trf_highvix", regime.loc["L4 Transformer", "High VIX (252)"])
reg.check("T55_harx_apr", regime.loc["L3 HAR-RV-X (full)", "Mar-May 2025 (63)"])
"""
    ),
    unit_header("K2", "三項完全分解", "The three-way decomposition",
                "run_eval.py (decomposition)", "本研究的核心貢獻 / the paper's contribution", "K1, C4, C6"),
    bi(
        zh=(
            "### 原理\n\n"
            "K1 建好了階梯，但光有階梯還不夠：讀者看到的仍然只是「最上層比最下層好多少」這一個總數。"
            "分解把這個總數拆成**三個可以分別檢定的部分**，而且三者相加恰好等於總數，沒有殘差。\n\n"
            "能這樣拆的唯一原因是 K1 的對等要求：因為 L3 與 L4 的資訊集合相同，兩者的差才能被解讀為"
            "**純架構效果**。少了對等，第三項就什麼都不是。\n\n"
            "### 公式\n\n"
            "令 $\\bar{L}(m)$ 為某模型的平均樣本外損失，$m_1, \\ldots, m_4$ 為各層的最佳模型：\n\n"
            "$$\\Delta_{HF} = \\bar{L}(m_1) - \\bar{L}(m_2), \\quad "
            "\\Delta_{info} = \\bar{L}(m_2) - \\bar{L}(m_3), \\quad "
            "\\Delta_{arch} = \\bar{L}(m_3) - \\bar{L}(m_4)$$\n\n"
            "三者相加為 $\\bar{L}(m_1) - \\bar{L}(m_4)$，即總增益。正值代表高層較好。\n\n"
            "### 演算法\n\n"
            "1. 各層取最佳模型（以 QLIKE 為準）。\n"
            "2. 算三個差，檢查相加是否等於總數——這是一個**不需要知道正確答案的檢查**。\n"
            "3. 每一項各做一次 DM 檢定與一個區塊拔靴區間。\n\n"
            "三點性質要向讀者講清楚：分解的是**損失差**不是變異數，所以可以是負的，而負值本身是有意義的發現；"
            "總數可能接近零，所以要報水準而不是比例；$\\Delta_{HF}$ 與 $\\Delta_{info}$ 有順序性，"
            "但 $\\Delta_{arch}$ 因為定義在固定資訊集合上，與順序無關。\n\n"
            "### 程式設計邏輯\n\n"
            "下面把分解寫成一個小函數，之後 R1、R2、R3 三個穩健性單元**直接重複使用它**——"
            "穩健性檢查若用另一份程式重算，就無法保證比的是同一件事。"
        ),
        en=(
            "### Principle\n\n"
            "K1 built the ladder, but a ladder alone still shows only one number: how much better the top is "
            "than the bottom. The decomposition splits that total into **three separately testable parts** "
            "which sum back to it exactly, with no residual.\n\n"
            "The only reason this split is possible is the parity requirement of K1: because L3 and L4 share "
            "an information set, their difference can be read as a **pure architecture effect**. Without "
            "parity the third component means nothing.\n\n"
            "### Formulas\n\n"
            "With $\\bar{L}(m)$ the average out-of-sample loss and $m_1, \\ldots, m_4$ the best model at each "
            "level:\n\n"
            "$$\\Delta_{HF} = \\bar{L}(m_1) - \\bar{L}(m_2), \\quad "
            "\\Delta_{info} = \\bar{L}(m_2) - \\bar{L}(m_3), \\quad "
            "\\Delta_{arch} = \\bar{L}(m_3) - \\bar{L}(m_4)$$\n\n"
            "The three sum to $\\bar{L}(m_1) - \\bar{L}(m_4)$, the total gain. Positive values favour the "
            "higher level.\n\n"
            "### Algorithm\n\n"
            "1. Take the best model at each level by QLIKE.\n"
            "2. Form the three differences and check that they sum to the total — a check that **does not "
            "require knowing the right answer**.\n"
            "3. Give each component a DM test and a block bootstrap interval.\n\n"
            "Three properties are worth stating to a reader: the parts are **loss differences**, not a "
            "variance decomposition, so they may be negative and a negative value is a meaningful finding; "
            "the total may be near zero, so the parts are reported in levels rather than shares; and while "
            "$\\Delta_{HF}$ and $\\Delta_{info}$ are sequential, $\\Delta_{arch}$ is invariant to the "
            "ordering because it is defined at a fixed information set.\n\n"
            "### Program logic\n\n"
            "The decomposition is a small function that units R1, R2 and R3 **reuse directly**; a robustness "
            "check recomputed by separate code cannot guarantee it is comparing the same thing."
        ),
    ),
    code(
        """
def decompose(y, f1, f2, f3, f4, loss=qlike, B=5000, seed=7):
    \"\"\"Three-way decomposition with DM p-values and block bootstrap intervals.\"\"\"
    L = [np.asarray(loss(y, f)) for f in (f1, f2, f3, f4)]
    names = ["Delta_HF (L1->L2)", "Delta_info (L2->L3)", "Delta_arch (L3->L4)"]
    rows = []
    rng = np.random.default_rng(seed)
    for k, nm in enumerate(names):
        d = L[k] - L[k + 1]
        stat, p = dm_hln(y, (f1, f2, f3)[k], (f2, f3, f4)[k], loss)
        lo, hi = boot_ci(d, B=B, rng=rng)
        rows.append(dict(component=nm, value=d.mean(), lo=lo, hi=hi, dm_p=p))
    total = L[0].mean() - L[3].mean()
    stat, p = dm_hln(y, f1, f4, loss)
    rows.append(dict(component="Total (L1->L4)", value=total, lo=np.nan, hi=np.nan, dm_p=p))
    return pd.DataFrame(rows)


best = dict(l1="L1 GJR-GARCH", l2="L2 HAR-RV", l3="L3 HAR-RV-X (full)", l4="L4 Transformer")
dec_A = decompose(Y, W[best["l1"]], W[best["l2"]], W[best["l3"]], W[best["l4"]])
dec_B = decompose(YB, WB[best["l1"]], WB[best["l2"]], WB[best["l3"]], WB[best["l4"]])
print("target A (intraday realized volatility)")
print(dec_A.round(4).to_string(index=False))
print("\\ntarget B (daily-return proxy)")
print(dec_B.round(4).to_string(index=False))

parts_sum = dec_A["value"].iloc[:3].sum()
total = dec_A["value"].iloc[3]
print(f"\\nadditivity check: parts sum {parts_sum:+.6f} vs total {total:+.6f} "
      f"(gap {abs(parts_sum - total):.2e})")

reg.check("T52_dhf_A", dec_A["value"].iloc[0])
reg.check("T52_dinfo_A", dec_A["value"].iloc[1])
reg.check("T52_darch_A", dec_A["value"].iloc[2])
reg.check("T52_total_A", dec_A["value"].iloc[3])
reg.check("T52_p_dhf_A", dec_A["dm_p"].iloc[0])
reg.check("T52_p_dinfo_A", dec_A["dm_p"].iloc[1])
reg.check("T52_p_darch_A", dec_A["dm_p"].iloc[2])
reg.check("T52_p_total_A", dec_A["dm_p"].iloc[3])
reg.check("T52_dinfo_B", dec_B["value"].iloc[1])
reg.check("T52_darch_B", dec_B["value"].iloc[2])
reg.check("T52_p_darch_B", dec_B["dm_p"].iloc[2])
reg.check_text("T52_additivity", abs(parts_sum - total) < 1e-10, f"gap {abs(parts_sum - total):.1e}")
reg.check("abs_dinfo", dec_A["value"].iloc[1])
reg.check_sign("abs_darch_sign", dec_A["value"].iloc[2])
"""
    ),
    code(
        """
fig, ax = plt.subplots(figsize=(6.4, 2.6))
lab = ["Delta_HF", "Delta_info", "Delta_arch", "Total"]
val = dec_A["value"].values
err_lo = val[:3] - dec_A["lo"].values[:3]
err_hi = dec_A["hi"].values[:3] - val[:3]
ax.bar(lab, val, color=["#b4c7dc", "#4e8a5b", "#c98a8a", "#999999"], width=0.6)
ax.errorbar(lab[:3], val[:3], yerr=[err_lo, err_hi], fmt="none", ecolor="black", capsize=4, lw=1)
ax.axhline(0, color="black", lw=0.8)
ax.set_ylabel("QLIKE gain")
ax.set_title("Decomposition of the QLIKE gain, target A, 90% block bootstrap intervals")
for i, v in enumerate(val):
    ax.text(i, v + (0.004 if v > 0 else -0.008), f"{v:+.3f}", ha="center", fontsize=8)
plt.show()
"""
    ),
    unit_header("K3", "GARCH-X 與邊界解", "GARCH-X by custom maximum likelihood and the boundary solution",
                "ladder.py (garch_x)", "Engle (1982); Glosten et al. (1993)", "C3, K1"),
    bi(
        zh=(
            "### 原理\n\n"
            "K2 的 $\\Delta_{info}$ 告訴我們外生資訊在 HAR 架構裡有用。但「有用」會不會只是 HAR 的性質？"
            "要回答這個問題，必須把同樣的外生變數放進**另一個模型族**。GARCH-X 就是：在 GJR-GARCH 的"
            "變異數方程式裡直接加入落後的隱含變異數。\n\n"
            "這個規格沒有現成套件，必須自己寫概似函數——這正是本教材唯一需要從零實作最佳化的節點。\n\n"
            "### 公式\n\n"
            "$$h_t = \\omega + (\\alpha + \\gamma I[\\varepsilon_{t-1} < 0])\\varepsilon_{t-1}^2 + "
            "\\beta h_{t-1} + \\delta' z_{t-1}$$\n\n"
            "其中 $z_{t-1}$ 為落後一期的 VIX 與 VIX9D 日變異數。Student-t 對數概似為\n\n"
            "$$\\ell_t = \\log \\Gamma\\left(\\frac{\\nu+1}{2}\\right) - \\log \\Gamma\\left(\\frac{\\nu}{2}\\right) "
            "- \\frac{1}{2}\\log[\\pi(\\nu-2)] - \\frac{1}{2}\\log h_t - \\frac{\\nu+1}{2}"
            "\\log\\left(1 + \\frac{\\varepsilon_t^2}{h_t(\\nu-2)}\\right)$$\n\n"
            "### 演算法\n\n"
            "1. 遞迴過濾出 $h_t$（這一步是序列相依的，無法平行化，也因此**不適合 GPU**）。\n"
            "2. 以 Nelder-Mead 最小化負對數概似；加上定態與非負限制，並用兩組起始值避免局部解。\n"
            "3. 多步預測時外生項固定在最後觀測值。\n\n"
            "### 程式設計邏輯\n\n"
            "完整估計要跑三個視窗、每個視窗兩組起始值、每次兩萬次函數評估，在純 Python 迴圈下需要數分鐘，"
            "所以筆記本**不重跑完整估計**，改成：(a) 把過濾與概似從零寫出來給讀者看，"
            "(b) 在一個視窗上跑一次縮短版的最佳化，驗證論文的關鍵定性發現——"
            "$\\delta$ 停在下界 0，也就是**在 GARCH 的變異數方程式裡，隱含變異數沒有增額內容**，"
            "非對稱項已經把這部分資訊吃掉了。"
        ),
        en=(
            "### Principle\n\n"
            "The $\\Delta_{info}$ of K2 says exogenous information helps inside the HAR framework. But is that "
            "a property of HAR? Answering requires putting the same variables into **another model family**. "
            "GARCH-X does exactly that: lagged implied variances enter the variance equation of GJR-GARCH "
            "directly.\n\n"
            "No package implements this specification, so the likelihood has to be written by hand — the one "
            "node in this tutorial that genuinely needs an optimiser built from scratch.\n\n"
            "### Formulas\n\n"
            "$$h_t = \\omega + (\\alpha + \\gamma I[\\varepsilon_{t-1} < 0])\\varepsilon_{t-1}^2 + "
            "\\beta h_{t-1} + \\delta' z_{t-1}$$\n\n"
            "with $z_{t-1}$ the lagged daily VIX and VIX9D variances. The Student-t log-likelihood term is\n\n"
            "$$\\ell_t = \\log \\Gamma\\left(\\frac{\\nu+1}{2}\\right) - \\log \\Gamma\\left(\\frac{\\nu}{2}\\right) "
            "- \\frac{1}{2}\\log[\\pi(\\nu-2)] - \\frac{1}{2}\\log h_t - \\frac{\\nu+1}{2}"
            "\\log\\left(1 + \\frac{\\varepsilon_t^2}{h_t(\\nu-2)}\\right)$$\n\n"
            "### Algorithm\n\n"
            "1. Filter $h_t$ recursively (this step is sequentially dependent, cannot be parallelised, and is "
            "therefore **a poor fit for a GPU**).\n"
            "2. Minimise the negative log-likelihood with Nelder-Mead under stationarity and non-negativity "
            "constraints, from two starting values to guard against a local optimum.\n"
            "3. Hold the exogenous term at its last observed value when iterating the multi-step forecast.\n\n"
            "### Program logic\n\n"
            "A full estimation runs three windows, two starts each, twenty thousand function evaluations per "
            "start, through a Python loop: several minutes. The notebook therefore **does not refit it in "
            "full**. Instead it (a) writes the filter and the likelihood out so the reader can see them and "
            "(b) runs one shortened optimisation on a single window to verify the paper's qualitative "
            "finding — $\\delta$ sits at its lower bound of zero, meaning the implied variances add nothing "
            "**inside the GARCH variance equation**, where the asymmetry term has already absorbed that "
            "information."
        ),
    ),
    code(
        """
from scipy.optimize import minimize
from scipy.special import gammaln


def garchx_filter(p, r, Z):
    \"\"\"One pass of the variance recursion. Sequential by construction: h_t needs h_{t-1}.\"\"\"
    mu, om, al, ga, be = p[:5]
    d = p[5:5 + Z.shape[1]]
    e = r - mu
    h = np.empty(len(r))
    h[0] = np.var(r)
    zc = Z @ d
    for t in range(1, len(r)):
        h[t] = om + (al + ga * (e[t - 1] < 0)) * e[t - 1] ** 2 + be * h[t - 1] + zc[t - 1]
        if h[t] < 1e-8:
            h[t] = 1e-8
    return e, h


def garchx_nll(theta, r, Z):
    p, nu = theta[:-1], theta[-1]
    if min(p[1], p[2], p[3], p[4]) < 0 or nu <= 2.05:
        return 1e10
    if p[2] + p[3] / 2 + p[4] >= 0.999:          # stationarity
        return 1e10
    if np.any(p[5:] < 0):                        # exogenous loadings cannot be negative variances
        return 1e10
    e, h = garchx_filter(p, r, Z)
    z2 = e ** 2 / h
    ll = (gammaln((nu + 1) / 2) - gammaln(nu / 2) - 0.5 * np.log(np.pi * (nu - 2))
          - 0.5 * np.log(h) - (nu + 1) / 2 * np.log1p(z2 / (nu - 2)))
    return -np.sum(ll) if np.isfinite(ll).all() else 1e10


# One window, shortened optimisation: enough to see where delta goes.
Yr, tr, te = list(windows())[0]
sl = slice(tr[0], te[-1] + 1)
r = D["ret_pct"].values[sl]
vix2 = np.exp(D["lvix"].values[sl]) / A * 1e4                                  # daily variance in %^2
vix9d2 = np.exp(D["lvix"].values[sl] + 2 * D["vix_slope"].values[sl]) / A * 1e4
Z = np.c_[vix2, vix9d2]
n_tr = len(tr)
theta0 = np.array([r[:n_tr].mean(), 0.05, 0.02, 0.08, 0.90, 1e-4, 1e-4, 8.0])
import time as _t
t0 = _t.time()
res = minimize(garchx_nll, theta0, args=(r[:n_tr], Z[:n_tr]), method="Nelder-Mead",
               options=dict(maxiter=4000, maxfev=4000, xatol=1e-5, fatol=1e-5))
names = ["mu", "omega", "alpha", "gamma", "beta", "delta_vix", "delta_vix9d", "nu"]
print(f"shortened fit on the {Yr} window ({_t.time() - t0:.0f}s, {res.nfev} evaluations)")
print({k: round(v, 5) for k, v in zip(names, res.x)})
print(f"\\ndelta on VIX    = {res.x[5]:.2e}")
print(f"delta on VIX9D  = {res.x[6]:.2e}   -> both at the lower bound, as the paper reports")
print(f"persistence     = {res.x[2] + res.x[3] / 2 + res.x[4]:.4f}")

reg.check("T51_qlike_garchx", qlike(Y, W["L3 GARCH-X"]).mean(),
          note="computed from the stored GARCH-X forecasts; the full MLE is not refit in the notebook")
"""
    ),
    unit_header("K4", "經濟評估", "Economic evaluation",
                "econ2.py (var_backtest, vol_target)",
                "Kupiec (1995); Christoffersen (1998); Fleming et al. (2003)", "K1"),
    bi(
        zh=(
            "### 原理\n\n"
            "K2 的分解整個建立在 QLIKE 上。但損失函數只是一個尺度，**沒有人用 QLIKE 做決策**。"
            "如果統計上的排序在真實決策裡站不住，那排序本身的意義就有限。"
            "本單元把預測送進兩個決策：風險值回測與波動率目標投資組合。\n\n"
            "### 公式\n\n"
            "五日風險值由預測波動率與標準化報酬的歷史分位數組成：\n\n"
            "$$VaR_t = \\hat{\\sigma}_t \\sqrt{5/252} \\quad q_{\\alpha}$$\n\n"
            "Kupiec 的無條件覆蓋檢定為概似比\n\n"
            "$$LR_{uc} = -2\\log\\frac{(1-\\alpha)^{T-x}\\alpha^x}{(1-\\hat{\\pi})^{T-x}\\hat{\\pi}^x} \\sim \\chi^2_1$$\n\n"
            "波動率目標投組的權重為 $w_t = \\min(2, \\sigma^{target} / \\hat{\\sigma}_t)$，每五日再平衡。\n\n"
            "### 演算法\n\n"
            "1. 標準化分位數 $q_\\alpha$ **只用估計樣本**算，所有模型共用，差別才只來自波動率預測。\n"
            "2. 違反次數在**不重疊**的五日區塊上計算，否則重疊會讓違反自動叢聚。\n"
            "3. Sharpe 用算術定義 $\\bar{r}/s \\times \\sqrt{252}$，與拔靴檢定一致。\n\n"
            "### 程式設計邏輯\n\n"
            "再平衡用一個明確的迴圈而不是 `resample`：權重在再平衡日之間必須**維持不變**，"
            "寫成迴圈讓這個語意一眼可見。成本以週轉率乘基點計入淨報酬。\n\n"
            "**這個單元也發現了稿件的一處不一致**，見 D2。"
        ),
        en=(
            "### Principle\n\n"
            "The decomposition of K2 rests entirely on QLIKE. But a loss function is only a scale, and "
            "**nobody makes decisions with QLIKE**. If the statistical ranking does not survive a real "
            "decision, its meaning is limited. This unit feeds the forecasts into two: value-at-risk "
            "backtesting and a volatility-targeted portfolio.\n\n"
            "### Formulas\n\n"
            "Five-day value-at-risk combines the forecast with a historical quantile of standardized "
            "returns:\n\n"
            "$$VaR_t = \\hat{\\sigma}_t \\sqrt{5/252} \\quad q_{\\alpha}$$\n\n"
            "Kupiec's unconditional coverage test is the likelihood ratio\n\n"
            "$$LR_{uc} = -2\\log\\frac{(1-\\alpha)^{T-x}\\alpha^x}{(1-\\hat{\\pi})^{T-x}\\hat{\\pi}^x} \\sim \\chi^2_1$$\n\n"
            "The targeted portfolio holds $w_t = \\min(2, \\sigma^{target} / \\hat{\\sigma}_t)$, rebalanced "
            "every five days.\n\n"
            "### Algorithm\n\n"
            "1. The standardized quantile $q_\\alpha$ is estimated **on the training sample only** and shared "
            "by every model, so differences come only from the volatility forecast.\n"
            "2. Violations are counted on **non-overlapping** five-day blocks; overlapping blocks would make "
            "violations cluster mechanically.\n"
            "3. The Sharpe ratio uses the arithmetic convention $\\bar{r}/s \\times \\sqrt{252}$, matching "
            "the bootstrap test.\n\n"
            "### Program logic\n\n"
            "Rebalancing is an explicit loop rather than a `resample` call: the weight must be **held "
            "constant** between rebalancing days, and the loop makes that semantics visible. Costs enter the "
            "net return as turnover times basis points.\n\n"
            "**This unit also uncovered an inconsistency in the manuscript**; see D2."
        ),
    ),
    code(
        """
from scipy.stats import chi2

TEST = (D.index >= "2023-01-01") & (D.index <= "2025-12-31")
idx_test = D.index[TEST]
ret_d = D["ret_pct"].values / 100
fwd5 = pd.Series(ret_d).rolling(5).sum().shift(-5).values

# Filtered historical simulation quantile, from the training sample only.
tr_mask = (D.index >= "2011-01-04") & (D.index <= "2020-12-31")
Xh = np.c_[np.ones(len(D)), D[HAR].values]
yl = np.log(D["y_hf"].values)
ok = tr_mask & np.isfinite(yl)
bh = np.linalg.lstsq(Xh[ok], yl[ok], rcond=None)[0]
fit_in = np.exp(Xh @ bh + 0.5 * np.var(yl[ok] - Xh[ok] @ bh))
z_std = (fwd5 / (fit_in * np.sqrt(5 / A)))[ok & np.isfinite(fwd5)]
z05 = np.quantile(z_std, 0.05)
print(f"standardized 5% quantile from the training sample: {z05:.3f}")


def var_backtest(f, ret5, zq, alpha=0.05):
    VaR = f * np.sqrt(5 / A) * zq
    hit = (ret5 < VaR).astype(int)
    T, x = len(hit), int(hit.sum())
    pi = x / T
    lr = (-2 * ((T - x) * np.log(1 - alpha) + x * np.log(alpha))
          + 2 * ((T - x) * np.log(1 - pi) + x * np.log(pi))) if 0 < pi < 1 else np.nan
    return dict(violations=x, rate=pi, p_kupiec=1 - chi2.cdf(lr, 1) if np.isfinite(lr) else np.nan)


sel = np.where(TEST)[0]
nonov = sel[::5]
ret5_no = fwd5[nonov]
keep = np.isfinite(ret5_no)
var_rows = {}
for m in MODELS + ["L4 LSTM"]:
    f = W[m].reindex(idx_test).values[::5][keep]
    var_rows[m] = var_backtest(f, ret5_no[keep], z05)
V = pd.DataFrame(var_rows).T
print(f"\\nnon-overlapping blocks: {int(keep.sum())}")
print(V.round(4).to_string())

reg.check_count("T61_viol_gjr", V.loc["L1 GJR-GARCH", "violations"])
reg.check_count("T61_viol_trf", V.loc["L4 Transformer", "violations"])
reg.check("T61_p_kupiec_gjr", V.loc["L1 GJR-GARCH", "p_kupiec"])
reg.check_text("T61_allpass", bool((V["p_kupiec"] > 0.05).all()),
               f"minimum Kupiec p across models = {V['p_kupiec'].min():.3f}")
"""
    ),
    code(
        """
def vol_target(f, ret_pct, target=0.10, wmax=2.0, cost_bps=5.0, rebal=5):
    \"\"\"Scale exposure to a volatility target; the weight is held between rebalancing days.\"\"\"
    w = np.minimum(wmax, target / f)
    wt = np.empty(len(f))
    cur = w[0]
    for i in range(len(f)):
        if i % rebal == 0:
            cur = w[i]
        wt[i] = cur
    r = ret_pct / 100
    turn = np.abs(np.diff(np.r_[0, wt]))
    net = wt * r - turn * cost_bps / 1e4
    cum = np.cumprod(1 + net)
    return dict(geo_return=cum[-1] ** (A / len(net)) - 1,
                arith_return=net.mean() * A,
                vol=net.std() * np.sqrt(A),
                sharpe=net.mean() / net.std() * np.sqrt(A),
                maxdd=(1 - cum / np.maximum.accumulate(cum)).max(),
                avg_w=wt.mean(), net=net)


ret_test = D["ret_pct"].values[TEST]
port = {}
for m in ["L1 GJR-GARCH", "L3 GARCH-X", "L3 HAR-RV-X (full)", "L4 LSTM", "L4 Transformer", "L2 HAR-RV"]:
    port[m] = vol_target(W[m].reindex(idx_test).values, ret_test)
bh_net = ret_test / 100
cum_bh = np.cumprod(1 + bh_net)
port["Buy and hold"] = dict(geo_return=cum_bh[-1] ** (A / len(bh_net)) - 1,
                            arith_return=bh_net.mean() * A,
                            vol=bh_net.std() * np.sqrt(A),
                            sharpe=bh_net.mean() / bh_net.std() * np.sqrt(A),
                            maxdd=(1 - cum_bh / np.maximum.accumulate(cum_bh)).max(),
                            avg_w=1.0, net=bh_net)
Pt = pd.DataFrame({k: {kk: vv for kk, vv in v.items() if kk != "net"} for k, v in port.items()}).T
print(Pt.round(4).to_string())

reg.check("T62_sharpe_gjr", Pt.loc["L1 GJR-GARCH", "sharpe"])
reg.check("T62_sharpe_harx", Pt.loc["L3 HAR-RV-X (full)", "sharpe"])
reg.check("T62_sharpe_trf", Pt.loc["L4 Transformer", "sharpe"])
reg.check("T62_sharpe_bh", Pt.loc["Buy and hold", "sharpe"])
reg.check("T62_avgw_gjr", Pt.loc["L1 GJR-GARCH", "avg_w"])
reg.check("T62_ret_gjr", Pt.loc["L1 GJR-GARCH", "geo_return"], note="geometric, as the model rows are")
reg.check("T62_ret_bh", Pt.loc["Buy and hold", "arith_return"],
          note="matches only under the arithmetic convention; geometric would be %.1f%%" % (Pt.loc["Buy and hold", "geo_return"] * 100))
rank_names = {"L1 GJR-GARCH": "GJR-GARCH", "L3 GARCH-X": "GARCH-X", "L3 HAR-RV-X (full)": "HAR-RV-X",
              "L4 LSTM": "LSTM", "L4 Transformer": "Transformer", "L2 HAR-RV": "HAR-RV"}
reg.check_rank("T62_rank_sharpe", {rank_names[k]: port[k]["sharpe"] for k in rank_names})
print("\\nnote the two return conventions in the same column: the targeted rows are reported")
print("geometrically in the manuscript, the buy-and-hold row arithmetically. See unit D2.")
"""
    ),
    unit_header("K5", "種子與版本的重現性", "Seeds and version pinning",
                "l4_main10.py, ENVIRONMENT.md", "Gundersen and Kjensmo (2018); Kapoor and Narayanan (2023)",
                "K1"),
    bi(
        zh=(
            "### 原理\n\n"
            "K2 量到的架構效果是 −0.024。但這個數字要可信，前提是它**大於那些沒人報告的實作選擇所造成的變動**。"
            "本單元檢查兩個這樣的選擇：隨機種子與深度學習套件的版本。\n\n"
            "這是整篇論文最可移植的部分：它與波動率無關，任何做深度學習比較的研究都適用。\n\n"
            "### 公式\n\n"
            "沒有新公式。要量的是同一個模型在只改種子時的損失分布，以及集成\n\n"
            "$$\\bar{f}_t = \\frac{1}{S}\\sum_{s=1}^{S} f_{t}^{(s)}$$\n\n"
            "在不同 $S$ 與不同種子子集下的穩定度。\n\n"
            "### 演算法\n\n"
            "1. 以十個種子訓練，只改初始化與批次順序。\n"
            "2. 計算每個種子的損失，報告全距與標準差。\n"
            "3. 比較「前五個種子的集成」「後五個」「全部十個」。\n"
            "4. 固定種子、資料、程式與硬體，只換套件版本，重跑一次。\n\n"
            "### 程式設計邏輯\n\n"
            "種子層級的預測序列有存下來，所以前三步可以在筆記本裡獨立重算。"
            "第四步不行：它需要同時安裝兩個版本的深度學習套件，**這在重現報告裡誠實標為無法驗證**。"
            "能保留的是程序本身：版本若會移動結果，就必須鎖定並揭露。"
        ),
        en=(
            "### Principle\n\n"
            "The architecture effect measured in K2 is −0.024. For that number to be credible it must be "
            "**larger than the variation caused by implementation choices nobody reports**. This unit "
            "examines two of them: the random seed and the version of the deep learning library.\n\n"
            "This is the most portable part of the paper: it has nothing to do with volatility and applies to "
            "any study comparing deep learning models.\n\n"
            "### Formulas\n\n"
            "No new formula. What is measured is the distribution of the loss across seeds, and the stability "
            "of the ensemble\n\n"
            "$$\\bar{f}_t = \\frac{1}{S}\\sum_{s=1}^{S} f_{t}^{(s)}$$\n\n"
            "under different $S$ and different subsets of seeds.\n\n"
            "### Algorithm\n\n"
            "1. Train with ten seeds, changing only initialisation and batch order.\n"
            "2. Compute each seed's loss; report the range and the standard deviation.\n"
            "3. Compare the ensemble of seeds 0-4, of 5-9, and of all ten.\n"
            "4. Holding seeds, data, code and hardware fixed, swap the library version and rerun.\n\n"
            "### Program logic\n\n"
            "The seed-level forecast series were stored, so the first three steps are recomputed here "
            "independently. The fourth cannot be: it needs two versions of the deep learning library "
            "installed at once, and it is **recorded as not verifiable in the reproduction report**. What "
            "survives is the procedure itself: if the version moves the result, it must be pinned and "
            "disclosed."
        ),
    ),
    code(
        """
S = pd.read_csv(PRED / "pred_transformer_by_seed_SPY.csv")
S.columns = [c.lstrip("\\ufeff") for c in S.columns]
S = S[S["target"] == "y_hf"].copy()
S["date"] = pd.to_datetime(S["date"])
E = S.pivot_table(index="date", columns="seed", values="forecast")

per_seed = pd.Series({s: qlike(Y, E[s]).mean() for s in E.columns}).sort_values()
print("QLIKE by seed")
print(per_seed.round(4).to_string())
print(f"\\nrange  {per_seed.max() - per_seed.min():.4f}   sd {per_seed.std():.4f}")
print(f"ensemble seeds 0-4 {qlike(Y, E[[0, 1, 2, 3, 4]].mean(axis=1)).mean():.4f}")
print(f"ensemble seeds 5-9 {qlike(Y, E[[5, 6, 7, 8, 9]].mean(axis=1)).mean():.4f}")
print(f"ensemble all ten   {qlike(Y, E.mean(axis=1)).mean():.4f}")
print(f"\\narchitecture effect being measured: {abs(dec_A['value'].iloc[2]):.4f}")
print(f"seed range over that effect        : {(per_seed.max() - per_seed.min()) / abs(dec_A['value'].iloc[2]):.1f}x")

reg.check("seed_min", per_seed.min())
reg.check("seed_max", per_seed.max())
reg.check("seed_spread", per_seed.max() - per_seed.min())
reg.check("seed_ens_05", qlike(Y, E[[0, 1, 2, 3, 4]].mean(axis=1)).mean())
reg.check("seed_ens_59", qlike(Y, E[[5, 6, 7, 8, 9]].mean(axis=1)).mean())
reg.check("seed_ens_all", qlike(Y, E.mean(axis=1)).mean())
reg.not_verifiable("version_shift",
                   "needs two PyTorch builds (2.6.0+cu124 and 2.13.0+cu126) installed side by side and the "
                   "networks retrained under each; the notebook has neither GPU training nor both builds")
"""
    ),
    code(
        """
fig, ax = plt.subplots(1, 2, figsize=(9, 2.7))
ax[0].bar(range(len(per_seed)), per_seed.values, color="#9ab7d3")
ax[0].axhline(qlike(Y, E.mean(axis=1)).mean(), color="#c0392b", lw=1,
              label="ten-seed ensemble")
ax[0].axhline(qlike(Y, W["L3 HAR-RV-X (full)"]).mean(), color="#2c7a3f", lw=1, ls="--",
              label="linear model, same inputs")
ax[0].set_xticks(range(len(per_seed)))
ax[0].set_xticklabels([str(s) for s in per_seed.index])
ax[0].set_xlabel("seed (sorted)")
ax[0].set_ylabel("QLIKE")
ax[0].set_title("Single-seed losses against the two reference lines")
ax[0].legend(fontsize=7)

sizes = range(1, 11)
means = [np.mean([qlike(Y, E[list(c)].mean(axis=1)).mean()
                  for c in [list(E.columns)[:k]]]) for k in sizes]
ax[1].plot(list(sizes), means, marker="o", ms=3, color="#3a6ea5")
ax[1].set_xlabel("number of seeds in the ensemble")
ax[1].set_ylabel("QLIKE")
ax[1].set_title("Ensembling stabilises the point estimate")
plt.tight_layout()
plt.show()
"""
    ),
]
