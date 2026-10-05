"""Levels 1-3 of the information ladder, expanding-window refit for each test year."""
import numpy as np, pandas as pd, json, time, warnings, pickle
from scipy.optimize import minimize
from scipy.special import gammaln
from arch import arch_model
warnings.filterwarnings('ignore')
A = 252
D = pd.read_parquet('analysis_daily.parquet')
GROUPS = json.load(open('groups.json', encoding='utf-8'))
FEATS = [c for g in GROUPS.values() for c in g]
HAR = GROUPS['G1 歷史已實現變異']
OPT = GROUPS['G3 選擇權前瞻']
TEST_YEARS = [2023, 2024, 2025]
START = '2011-01-04'

def windows():
    """For test year Y: estimation sample = START .. Y-1 end (targets purged 5 days)."""
    for Y in TEST_YEARS:
        est_end = pd.Timestamp(f'{Y-1}-12-31')
        te = np.where((D.index >= f'{Y}-01-01') & (D.index <= f'{Y}-12-31'))[0]
        tr = np.where((D.index >= START) & (D.index <= est_end))[0][:-5]
        yield Y, tr, te

def linreg(tgt, cols, tr, te):
    X = np.c_[np.ones(len(D)), D[cols].values]
    y = np.log(D[tgt].values)
    ok = tr[np.isfinite(y[tr])]
    b = np.linalg.lstsq(X[ok], y[ok], rcond=None)[0]
    s2 = np.var(y[ok] - X[ok] @ b)
    return np.exp(X[te] @ b + 0.5 * s2)

def naive(tgt, te):
    if tgt == 'y_hf':
        return np.exp(0.5 * D.lrv_w.values[te])
    r2 = (D.ret_pct.values / 100) ** 2
    return np.sqrt(A * pd.Series(r2).rolling(5).mean().values[te])

def garch(tr, te, gjr):
    r = D.ret_pct.iloc[tr[0]:te[-1] + 1]
    am = arch_model(r, mean='Constant', vol='GARCH', p=1, o=1 if gjr else 0, q=1, dist='t')
    res = am.fit(last_obs=D.index[tr[-1]] + pd.Timedelta(days=1), disp='off')
    fc = res.forecast(horizon=5, start=D.index[te[0]], reindex=False).variance.reindex(D.index[te])
    return np.sqrt(A / 5 * fc.sum(axis=1).values) / 100, res.params.to_dict()

# ---------------- GARCH-X (L3): GJR-GARCH(1,1) with option-implied variance in the variance equation
def _filter(p, r, Z):
    mu, om, al, ga, be = p[:5]
    d = p[5:5 + Z.shape[1]]
    e = r - mu
    h = np.empty(len(r)); h[0] = np.var(r)
    zc = Z @ d
    for t in range(1, len(r)):
        h[t] = om + (al + ga * (e[t-1] < 0)) * e[t-1]**2 + be * h[t-1] + zc[t-1]
        if h[t] < 1e-8: h[t] = 1e-8
    return e, h

def _nll(theta, r, Z):
    p, nu = theta[:-1], theta[-1]
    if min(p[1], p[2], p[3], p[4]) < 0 or nu <= 2.05: return 1e10
    if p[2] + p[3] / 2 + p[4] >= 0.999: return 1e10
    if np.any(p[5:] < 0): return 1e10
    e, h = _filter(p, r, Z)
    z2 = e**2 / h
    ll = (gammaln((nu + 1) / 2) - gammaln(nu / 2) - 0.5 * np.log(np.pi * (nu - 2))
          - 0.5 * np.log(h) - (nu + 1) / 2 * np.log1p(z2 / (nu - 2)))
    return -np.sum(ll) if np.isfinite(ll).all() else 1e10

def garch_x(tr, te):
    """Variance equation gets lagged VIX and VIX9D variances (daily, %^2)."""
    s = slice(tr[0], te[-1] + 1)
    r = D.ret_pct.values[s]
    vix2 = np.exp(D.lvix.values[s]) / A * 1e4                       # daily variance in %^2
    vix9d2 = np.exp(D.lvix.values[s] + 2 * D.vix_slope.values[s]) / A * 1e4
    Z = np.c_[vix2, vix9d2]
    n_tr = len(tr)
    th0 = np.array([r[:n_tr].mean(), 0.05, 0.02, 0.08, 0.90, 1e-4, 1e-4, 8.0])
    best = None
    for scale in (1.0, 0.5):
        t0 = th0.copy(); t0[5:7] *= scale
        res = minimize(_nll, t0, args=(r[:n_tr], Z[:n_tr]), method='Nelder-Mead',
                       options=dict(maxiter=20000, maxfev=20000, xatol=1e-6, fatol=1e-6))
        if best is None or res.fun < best.fun: best = res
    p = best.x[:-1]
    e, h = _filter(p, r, Z)                                          # filter through test with known exog
    pers = p[2] + p[3] / 2 + p[4]
    zc = Z @ p[5:5 + Z.shape[1]]
    out = []
    for i in te:
        t = i - tr[0]
        h1 = p[1] + (p[2] + p[3] * (e[t] < 0)) * e[t]**2 + p[4] * h[t] + zc[t]
        tot, hj = h1, h1
        for _ in range(4):
            hj = p[1] + pers * hj + zc[t]                            # exogenous held at its last value
            tot += hj
        out.append(np.sqrt(A / 5 * tot) / 100)
    return np.array(out), dict(zip(['mu','omega','alpha','gamma','beta','delta_vix','delta_vix9d','nu'], best.x))

if __name__ == '__main__':
    preds, params, t0 = {}, {}, time.time()
    for Y, tr, te in windows():
        idx = D.index[te]
        for tgt in ['y_hf', 'y_cc']:
            preds.setdefault((tgt, 'L0 Naive'), {})[Y] = pd.Series(naive(tgt, te), idx)
            preds.setdefault((tgt, 'L2 HAR-RV'), {})[Y] = pd.Series(linreg(tgt, HAR, tr, te), idx)
            preds.setdefault((tgt, 'L3 HAR-RV-X (opt only)'), {})[Y] = pd.Series(linreg(tgt, HAR + OPT, tr, te), idx)
            preds.setdefault((tgt, 'L3 HAR-RV-X (full)'), {})[Y] = pd.Series(linreg(tgt, FEATS, tr, te), idx)
        for lab, gjr in [('L1 GARCH(1,1)', False), ('L1 GJR-GARCH', True)]:
            f, pr = garch(tr, te, gjr)
            for tgt in ['y_hf', 'y_cc']: preds.setdefault((tgt, lab), {})[Y] = pd.Series(f, idx)
            params[(lab, Y)] = pr
        f, pr = garch_x(tr, te)
        for tgt in ['y_hf', 'y_cc']: preds.setdefault((tgt, 'L3 GARCH-X'), {})[Y] = pd.Series(f, idx)
        params[('L3 GARCH-X', Y)] = pr
        print(f'{Y}: n_train={len(tr)} done  ({time.time()-t0:.0f}s)', flush=True)
    P = {k: pd.concat(v.values()).sort_index() for k, v in preds.items()}
    pickle.dump(P, open('pred_l123.pkl', 'wb'))
    pickle.dump(params, open('params_l123.pkl', 'wb'))
    for k, v in params.items():
        print(k, {a: round(b, 4) for a, b in v.items()})
