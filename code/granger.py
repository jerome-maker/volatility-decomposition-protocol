"""Granger predictive-causality tests, estimated on the training sample only (2011-2020)."""
import numpy as np, pandas as pd, json, statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, kpss
from scipy.stats import chi2
import warnings; warnings.filterwarnings('ignore')

D = pd.read_parquet('analysis_daily.parquet')
GROUPS = json.load(open('groups.json', encoding='utf-8'))
TR = (D.index >= '2011-01-04') & (D.index <= '2020-12-31')
HAR = GROUPS['G1 歷史已實現變異']

def stationarity():
    rows = []
    for c in [c for g in GROUPS.values() for c in g]:
        x = D[c][TR].dropna().values
        try: p_adf = adfuller(x, autolag='AIC')[1]
        except Exception: p_adf = np.nan
        try: p_kpss = kpss(x, regression='c', nlags='auto')[1]
        except Exception: p_kpss = np.nan
        rows.append(dict(var=c, adf_p=p_adf, kpss_p=p_kpss,
                         verdict='定態' if (p_adf < 0.05 and p_kpss > 0.05) else ('非定態' if p_adf > 0.05 else '邊際')))
    return pd.DataFrame(rows)

def wald(dep, xcols, lags, hac):
    """Test that all lags of xcols are jointly zero, controlling for HAR terms."""
    Z = pd.DataFrame(index=D.index)
    for c in HAR: Z[c] = D[c]
    names = []
    for c in xcols:
        for l in range(lags):
            Z[f'{c}_l{l}'] = D[c].shift(l); names.append(f'{c}_l{l}')
    Z['dep'] = dep
    Z = Z[TR].dropna()
    X = sm.add_constant(Z.drop(columns='dep'))
    m = sm.OLS(Z.dep, X).fit(cov_type='HAC', cov_kwds={'maxlags': hac})
    R = np.zeros((len(names), X.shape[1]))
    for i, nm in enumerate(names): R[i, list(X.columns).index(nm)] = 1
    t = m.wald_test(R, use_f=False, scalar=True)
    return float(t.statistic), float(t.pvalue), len(names), int(Z.shape[0])

def bic_lag(xcols, dep, maxlag=5):
    best = (np.inf, 1)
    for p in range(1, maxlag + 1):
        Z = pd.DataFrame({c: D[c] for c in HAR})
        for c in xcols:
            for l in range(p): Z[f'{c}_l{l}'] = D[c].shift(l)
        Z['dep'] = dep; Z = Z[TR].dropna()
        m = sm.OLS(Z.dep, sm.add_constant(Z.drop(columns='dep'))).fit()
        if m.bic < best[0]: best = (m.bic, p)
    return best[1]

def bh(pvals, q=0.05):
    p = np.asarray(pvals); o = np.argsort(p); n = len(p)
    thr = q * (np.arange(1, n + 1)) / n
    passed = p[o] <= thr
    k = np.where(passed)[0].max() + 1 if passed.any() else 0
    out = np.zeros(n, bool); out[o[:k]] = True
    return out

def run():
    dep1 = D.lrv_d.shift(-1)                      # next-day log realized variance
    dep5 = np.log(D.y_hf ** 2)                    # 5-day ahead annualized log variance (overlapping)
    rows = []
    for g, cols in GROUPS.items():
        if g.startswith('G1'): continue           # G1 is the control
        p = bic_lag(cols, dep1)
        w1, p1, k1, n1 = wald(dep1, cols, p, hac=5)
        w5, p5, k5, n5 = wald(dep5, cols, p, hac=10)
        rows.append(dict(group=g, vars=len(cols), lags=p, wald_h1=w1, p_h1=p1, wald_h5=w5, p_h5=p5, n=n1))
    R = pd.DataFrame(rows)
    R['sig_h1_BH'] = bh(R.p_h1.values); R['sig_h5_BH'] = bh(R.p_h5.values)
    # individual variables (h=5), for the SHAP comparison
    ind = []
    for g, cols in GROUPS.items():
        for c in cols:
            if c in HAR: continue
            w, pv, _, _ = wald(dep5, [c], bic_lag([c], dep1), hac=10)
            ind.append(dict(group=g, var=c, wald_h5=w, p_h5=pv))
    I = pd.DataFrame(ind); I['sig_BH'] = bh(I.p_h5.values)
    # rolling 3-year stability (h=1)
    roll = []
    global TR
    years = range(2011, 2019)
    for y0 in years:
        lo, hi = pd.Timestamp(f'{y0}-01-01'), pd.Timestamp(f'{y0+2}-12-31')
        save = TR; TR = (D.index >= lo) & (D.index <= hi)
        for g, cols in GROUPS.items():
            if g.startswith('G1'): continue
            try:
                _, pv, _, _ = wald(dep1, cols, 1, hac=5)
            except Exception: pv = np.nan
            roll.append(dict(window=f'{y0}-{y0+2}', group=g, p=pv))
        TR = save
    RO = pd.DataFrame(roll)
    share = RO.assign(sig=RO.p < 0.05).groupby('group').sig.mean()
    return R, I, share

if __name__ == '__main__':
    S = stationarity(); S.to_csv('granger_stationarity.csv', index=False)
    print(S.round(3).to_string(), '\n')
    R, I, share = run()
    R['sig_share_rolling'] = R.group.map(share)
    R.to_csv('granger_groups.csv', index=False); I.to_csv('granger_vars.csv', index=False)
    print(R.round(4).to_string(), '\n')
    print(I.round(4).to_string())
