"""Second-asset robustness: same ladder on QQQ and SPY, daily-only information set.

Cross-asset variable is the RELATIVE return (own minus the other ETF), not the other ETF's raw return,
because QQQ and SPY returns are 93% correlated (VIF 7.1) while the relative return has VIF 1.0."""
import numpy as np, pandas as pd, json, pickle, warnings
from arch import arch_model
warnings.filterwarnings('ignore')
A = 252
OH = pd.read_parquet('data/daily_ohlc.parquet')
X = pd.read_parquet('data/exog_raw.parquet')
VXN = pd.read_parquet('data/vxn.parquet')
START, TEST_YEARS = '2011-01-04', [2023, 2024, 2025]

def build(tkr):
    d = OH[tkr].copy()
    idx = d.index
    ex = X.reindex(X.index.union(idx)).ffill(limit=5).reindex(idx)
    vx = VXN.reindex(VXN.index.union(idx)).ffill(limit=5).reindex(idx)
    r = np.log(d.Close).diff()
    gk = 0.5 * np.log(d.High / d.Low) ** 2 - (2 * np.log(2) - 1) * np.log(d.Close / d.Open) ** 2
    gk = gk.clip(lower=1e-8)
    F = pd.DataFrame(index=idx)
    # G1: range-based realised variance (daily / weekly / monthly)
    F['lgk_d'] = np.log(A * gk)
    F['lgk_w'] = np.log(A * gk.rolling(5).mean())
    F['lgk_m'] = np.log(A * gk.rolling(22).mean())
    # G2: downside proxy from daily returns
    F['lrs_neg'] = np.log(A * (r ** 2 * (r < 0)).rolling(5).mean() + 1e-8)
    # G3: option-implied (VXN for QQQ, VIX for SPY) + common SPX 9-day term slope
    iv = vx.VXN if tkr == 'QQQ' else ex.VIX
    F['liv'] = 2 * np.log(iv / 100)
    F['vix_slope'] = np.log(ex.VIX9D / ex.VIX)
    # G4 returns
    F['r_cc'] = r * 100
    F['r_on'] = (np.log(d.Open) - np.log(d.Close.shift())) * 100
    F['r_w'] = (r.rolling(5).sum()) * 100
    F['r_m'] = (r.rolling(22).sum()) * 100
    # G5 rates (lagged), G6 dollar & cross-asset, G7 volume
    F['d_y10'] = ex.DGS10.diff().shift(1)
    F['term'] = (ex.DGS10 - ex.DGS3MO).shift(1)
    F['r_dxy'] = (np.log(ex.DTWEXBGS).diff() * 100).shift(1)
    for t2 in ['TLT', 'GLD']: F['r_' + t2.lower()] = np.log(ex[t2]).diff() * 100
    # relative return: own minus the other ETF (removes the common market component)
    r_other = np.log(OH['SPY' if tkr == 'QQQ' else 'QQQ'].Close).diff()
    F['r_rel'] = (r - r_other) * 100
    F['vol_rel'] = np.log(d.Volume) - np.log(d.Volume).rolling(22, min_periods=5).mean().shift()
    # target: 5-day ahead annualised close-to-close realised volatility
    fwd = (r ** 2)[::-1].rolling(5).sum()[::-1].shift(-1)
    F['y'] = np.sqrt(A / 5 * fwd)
    F['ret_pct'] = r * 100
    return F.loc[START:'2025-12-31'].dropna(subset=[c for c in F.columns if c != 'y'])

GROUPS = {'G1 區間變異': ['lgk_d', 'lgk_w', 'lgk_m'], 'G2 下跌': ['lrs_neg'],
          'G3 選擇權前瞻': ['liv', 'vix_slope'], 'G4 報酬': ['r_cc', 'r_on', 'r_w', 'r_m'],
          'G5 利率': ['d_y10', 'term'], 'G6 美元與跨資產': ['r_dxy', 'r_tlt', 'r_gld', 'r_rel'],
          'G7 交易量': ['vol_rel']}
FEATS = [c for g in GROUPS.values() for c in g]
HARC = GROUPS['G1 區間變異']

def windows(D):
    for Y in TEST_YEARS:
        tr = np.where((D.index >= START) & (D.index <= f'{Y-1}-12-31'))[0][:-5]
        te = np.where((D.index >= f'{Y}-01-01') & (D.index <= f'{Y}-12-31'))[0]
        yield Y, tr, te

def linreg(D, cols, tr, te):
    Xm = np.c_[np.ones(len(D)), D[cols].values]; y = np.log(D.y.values)
    ok = tr[np.isfinite(y[tr])]
    b = np.linalg.lstsq(Xm[ok], y[ok], rcond=None)[0]
    s2 = np.var(y[ok] - Xm[ok] @ b)
    return np.exp(Xm[te] @ b + 0.5 * s2)

def garch(D, tr, te, gjr):
    r = D.ret_pct.iloc[tr[0]:te[-1] + 1]
    am = arch_model(r, mean='Constant', vol='GARCH', p=1, o=1 if gjr else 0, q=1, dist='t')
    res = am.fit(last_obs=D.index[tr[-1]] + pd.Timedelta(days=1), disp='off')
    fc = res.forecast(horizon=5, start=D.index[te[0]], reindex=False).variance.reindex(D.index[te])
    return np.sqrt(A / 5 * fc.sum(axis=1).values) / 100

if __name__ == '__main__':
    store = {}
    for tkr in ['QQQ', 'SPY']:
        D = build(tkr); D.to_parquet(f'daily_{tkr}.parquet')
        print(tkr, D.shape, D.index.min().date(), D.index.max().date(), flush=True)
        preds = {}
        for Y, tr, te in windows(D):
            ix = D.index[te]
            preds.setdefault('L0 Naive', {})[Y] = pd.Series(np.exp(0.5 * D.lgk_w.values[te]), ix)
            preds.setdefault('L1 GARCH(1,1)', {})[Y] = pd.Series(garch(D, tr, te, False), ix)
            preds.setdefault('L1 GJR-GARCH', {})[Y] = pd.Series(garch(D, tr, te, True), ix)
            preds.setdefault('L2 HAR-GK', {})[Y] = pd.Series(linreg(D, HARC, tr, te), ix)
            preds.setdefault('L3 HAR-GK-X (opt only)', {})[Y] = pd.Series(linreg(D, HARC + GROUPS['G3 選擇權前瞻'], tr, te), ix)
            preds.setdefault('L3 HAR-GK-X (full)', {})[Y] = pd.Series(linreg(D, FEATS, tr, te), ix)
        store[tkr] = {k: pd.concat(v.values()).sort_index() for k, v in preds.items()}
    pickle.dump(store, open('pred_asset2.pkl', 'wb'))
    json.dump(GROUPS, open('groups2.json', 'w'), ensure_ascii=False)
    print('L1-L3 done')
