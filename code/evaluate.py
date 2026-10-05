"""Forecast evaluation, loss decomposition, and economic value for the information ladder."""
import numpy as np, pandas as pd, pickle, json
from scipy.stats import norm, t as tdist, chi2

A = 252
D = pd.read_parquet('analysis_daily.parquet')
rng = np.random.default_rng(7)

# ---------------- losses
def mse_var(y, f): return ((y ** 2 - f ** 2) ** 2) * 1e8      # variance MSE, scaled for readability
def qlike(y, f): return (y ** 2) / (f ** 2) - np.log((y ** 2) / (f ** 2)) - 1
def rmse_vol(y, f): return np.sqrt(np.mean(((f - y) * 100) ** 2))
def mae_vol(y, f): return np.mean(np.abs((f - y) * 100))

def hac_var(d, lag):
    T = len(d); dc = d - d.mean()
    v = dc @ dc / T
    for k in range(1, lag + 1):
        v += 2 * (1 - k / (lag + 1)) * (dc[k:] @ dc[:-k]) / T
    return v

def dm_hln(y, f1, f2, loss, h=5):
    """Diebold-Mariano with Harvey-Leybourne-Newbold small-sample correction. <0 favours f1."""
    d = loss(y, f1) - loss(y, f2); T = len(d)
    v = hac_var(d, h)
    stat = d.mean() / np.sqrt(v / T)
    corr = np.sqrt((T + 1 - 2 * h + h * (h - 1) / T) / T)
    stat *= corr
    return stat, 2 * (1 - tdist.cdf(abs(stat), T - 1))

def clark_west(y, f_small, f_big, h=5):
    """One-sided CW test for nested models; positive stat favours the larger model."""
    fhat = (y ** 2 - f_small ** 2) ** 2 - ((y ** 2 - f_big ** 2) ** 2 - (f_small ** 2 - f_big ** 2) ** 2)
    T = len(fhat)
    stat = fhat.mean() / np.sqrt(hac_var(fhat, h) / T)
    return stat, 1 - norm.cdf(stat)

def block_boot_idx(T, B, block=20):
    nb = int(np.ceil(T / block))
    starts = rng.integers(0, T - block + 1, size=(B, nb))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(B, -1)[:, :T]
    return idx

def boot_ci(x, B=5000, block=20, q=(5, 95)):
    idx = block_boot_idx(len(x), B, block)
    m = x[idx].mean(1)
    return np.percentile(m, q)

def mcs(losses: pd.DataFrame, alpha=0.10, B=2000, block=20):
    """Hansen-Lunde-Nason MCS, range statistic, block bootstrap."""
    L = losses.copy(); alive = list(L.columns); T = len(L)
    idx = block_boot_idx(T, B, block)
    pvals = {}
    while len(alive) > 1:
        X = L[alive].values
        dbar = X.mean(0)
        boot = X[idx].mean(1)                                    # B x M
        var_d = np.zeros((len(alive), len(alive)))
        t_stat = np.zeros_like(var_d); t_boot = np.zeros((B, len(alive), len(alive)))
        for i in range(len(alive)):
            for j in range(len(alive)):
                if i == j: continue
                dij = dbar[i] - dbar[j]
                bij = boot[:, i] - boot[:, j]
                v = max(np.var(bij - dij), 1e-18)
                var_d[i, j] = v
                t_stat[i, j] = dij / np.sqrt(v)
                t_boot[:, i, j] = (bij - dij) / np.sqrt(v)
        TR = np.max(np.abs(t_stat)); TRb = np.max(np.abs(t_boot), axis=(1, 2))
        p = (TRb > TR).mean()
        pvals[tuple(alive)] = p
        if p >= alpha: break
        # eliminate the worst model
        worst = alive[int(np.argmax([np.max(t_stat[i]) for i in range(len(alive))]))]
        alive.remove(worst)
    return alive, pvals

# ---------------- economic value
def var_backtest(dates, y, f, ret5, z_quant, alpha):
    VaR = f * np.sqrt(5 / A) * z_quant                            # negative number
    hit = (ret5 < VaR).astype(int)
    T = len(hit); x = hit.sum(); pi = x / T
    # Kupiec POF
    if 0 < pi < 1:
        lr_pof = -2 * ((T - x) * np.log(1 - alpha) + x * np.log(alpha)) + 2 * ((T - x) * np.log(1 - pi) + x * np.log(pi))
    else:
        lr_pof = np.nan
    p_pof = 1 - chi2.cdf(lr_pof, 1) if np.isfinite(lr_pof) else np.nan
    # Christoffersen independence
    n00 = n01 = n10 = n11 = 0
    for a, b in zip(hit[:-1], hit[1:]):
        if a == 0 and b == 0: n00 += 1
        elif a == 0 and b == 1: n01 += 1
        elif a == 1 and b == 0: n10 += 1
        else: n11 += 1
    p01 = n01 / max(n00 + n01, 1); p11 = n11 / max(n10 + n11, 1); pu = (n01 + n11) / max(n00 + n01 + n10 + n11, 1)
    def ll(p, a, b): return 0 if p in (0, 1) else a * np.log(1 - p) + b * np.log(p)
    lr_ind = -2 * (ll(pu, n00 + n10, n01 + n11) - (ll(p01, n00, n01) + ll(p11, n10, n11)))
    p_ind = 1 - chi2.cdf(lr_ind, 1) if np.isfinite(lr_ind) else np.nan
    p_cc = 1 - chi2.cdf(lr_pof + lr_ind, 2) if np.isfinite(lr_pof + lr_ind) else np.nan
    tick = np.mean((alpha - (ret5 < VaR)) * (ret5 - VaR))          # quantile (tick) loss
    return dict(viol=int(x), rate=pi, expected=alpha, p_kupiec=p_pof, p_ind=p_ind, p_cc=p_cc, tick=tick)

def vol_target(dates, f, ret_pct, target=0.10, wmax=2.0, cost_bps=5.0, rebal=5):
    w = np.minimum(wmax, target / f)
    wt = np.empty(len(f)); cur = w[0]
    for i in range(len(f)):
        if i % rebal == 0: cur = w[i]
        wt[i] = cur
    r = ret_pct / 100
    turn = np.abs(np.diff(np.r_[0, wt]))
    net = wt * r - turn * cost_bps / 1e4
    cum = np.cumprod(1 + net)
    ann_ret = cum[-1] ** (A / len(net)) - 1
    ann_vol = np.std(net) * np.sqrt(A)
    # Sharpe ratio on the arithmetic convention, so that it matches the bootstrap test
    sharpe = net.mean() / net.std() * np.sqrt(A) if net.std() > 0 else np.nan
    dd = 1 - cum / np.maximum.accumulate(cum)
    return dict(ann_ret=ann_ret, ann_vol=ann_vol, sharpe=sharpe, maxdd=dd.max(),
                turnover=turn.sum() * A / len(net), avg_w=wt.mean(), net=net)
