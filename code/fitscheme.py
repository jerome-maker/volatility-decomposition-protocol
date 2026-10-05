"""Fitting-scheme robustness, motivated by Audrino and Chassot (2024/2026).

They show that HAR's performance depends heavily on the training window and the re-estimation
frequency, and that studies which re-estimate infrequently tend to find machine learning ahead.
Our linear models are re-estimated annually, which by their evidence is a conservative choice
for the linear side. This script re-estimates them daily to see how far the decomposition moves.
"""
import numpy as np, pandas as pd, pickle, json
from evaluate import qlike, rmse_vol, dm_hln, boot_ci

D = pd.read_parquet('analysis_daily.parquet')
GROUPS = json.load(open('groups.json', encoding='utf-8'))
FEATS = [c for g in GROUPS.values() for c in g]
HAR = GROUPS['G1 歷史已實現變異']
P = pickle.load(open('pred_all.pkl', 'rb'))
HOLD = pickle.load(open('pred_holdout2026.pkl', 'rb'))

def ols_forecast(cols, tgt, test_mask, scheme, window=630, start='2011-01-04'):
    X = np.c_[np.ones(len(D)), D[cols].values]
    y = np.log(D[tgt].values)
    idx = np.where(test_mask)[0]
    out = np.empty(len(idx))
    s0 = D.index.searchsorted(pd.Timestamp(start))
    for k, t in enumerate(idx):
        hi = t - 5                                    # purge: targets must not overlap day t
        lo = s0 if scheme == 'expanding' else max(s0, hi - window)
        sl = slice(lo, hi)
        ok = np.isfinite(y[sl])
        Xi, yi = X[sl][ok], y[sl][ok]
        b = np.linalg.lstsq(Xi, yi, rcond=None)[0]
        s2 = np.var(yi - Xi @ b)
        out[k] = np.exp(X[t] @ b + 0.5 * s2)
    return pd.Series(out, D.index[idx])

def run(period):
    if period == 'test':
        mask = (D.index >= '2023-01-01') & (D.index <= '2025-12-31'); src = P
    else:
        mask = (D.index >= '2026-01-01') & (D.index <= '2026-12-31'); src = HOLD
    idx = D.index[mask]; y = D['y_hf'].reindex(idx).values; ok = np.isfinite(y)
    rows = []
    preds = {}
    for name, cols in [('HAR-RV', HAR), ('HAR-RV-X', FEATS)]:
        preds[(name, 'annual')] = src[('y_hf', 'L2 HAR-RV' if name == 'HAR-RV' else 'L3 HAR-RV-X (full)')].reindex(idx)
        preds[(name, 'daily expanding')] = ols_forecast(cols, 'y_hf', mask, 'expanding')
        preds[(name, 'daily rolling 630')] = ols_forecast(cols, 'y_hf', mask, 'rolling')
    for (name, sch), f in preds.items():
        v = f.reindex(idx).values
        rows.append(dict(period=period, model=name, scheme=sch, QLIKE=qlike(y[ok], v[ok]).mean(), RMSE=rmse_vol(y[ok], v[ok])))
    tf = src[('y_hf', 'L4 Transformer')].reindex(idx).values
    dec = []
    for sch in ['annual', 'daily expanding', 'daily rolling 630']:
        l2 = preds[('HAR-RV', sch)].reindex(idx).values[ok]
        l3 = preds[('HAR-RV-X', sch)].reindex(idx).values[ok]
        yy = y[ok]
        di = qlike(yy, l2) - qlike(yy, l3); lo1, hi1 = boot_ci(di); _, p1 = dm_hln(yy, l3, l2, qlike)
        da = qlike(yy, l3) - qlike(yy, tf[ok]); lo2, hi2 = boot_ci(da); _, p2 = dm_hln(yy, tf[ok], l3, qlike)
        dec.append(dict(period=period, scheme=sch, delta_info=di.mean(), info_lo=lo1, info_hi=hi1, info_p=p1,
                        delta_arch=da.mean(), arch_lo=lo2, arch_hi=hi2, arch_p=p2))
    return pd.DataFrame(rows), pd.DataFrame(dec)

if __name__ == '__main__':
    R = []; DE = []
    for per in ['test', 'holdout']:
        r, d = run(per); R.append(r); DE.append(d)
    R = pd.concat(R); DE = pd.concat(DE)
    R.to_csv('res_fitscheme.csv', index=False); DE.to_csv('res_fitscheme_decomp.csv', index=False)
    pd.set_option('display.width', 220)
    print(R.pivot(index=['period', 'model'], columns='scheme', values='QLIKE').round(4).to_string())
    print()
    print(DE.round(4).to_string(index=False))
