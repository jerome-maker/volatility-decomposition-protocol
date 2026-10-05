"""Build all result tables for the information-ladder study."""
import numpy as np, pandas as pd, pickle, json
from evaluate import *
from evaluate import D as DD

D = pd.read_parquet('analysis_daily.parquet')
GROUPS = json.load(open('groups.json', encoding='utf-8'))
FEATS = [c for g in GROUPS.values() for c in g]
HAR = GROUPS['G1 歷史已實現變異']
P = pickle.load(open('pred_l123.pkl', 'rb'))
L4 = pickle.load(open('l4_final10.pkl', 'rb'))

TEST = (D.index >= '2023-01-01') & (D.index <= '2025-12-31')
idx = D.index[TEST]

# Transformer: mean of 5 seeds per test year
for tgt in ['y_hf', 'y_cc']:
    per_year = {}
    for (Y, cfg, seed, t), r in L4['runs']:
        if t != tgt: continue
        per_year.setdefault(Y, []).append(pd.Series(r['pred'], D.index[r['te']]))
    P[(tgt, 'L4 Transformer')] = pd.concat([pd.concat(v, axis=1).mean(axis=1) for v in per_year.values()]).sort_index()

ORDER = ['L0 Naive', 'L1 GARCH(1,1)', 'L1 GJR-GARCH', 'L2 HAR-RV',
         'L3 HAR-RV-X (opt only)', 'L3 HAR-RV-X (full)', 'L3 GARCH-X', 'L4 Transformer']
LADDER = {'L1': 'L1 GJR-GARCH', 'L2': 'L2 HAR-RV', 'L3': 'L3 HAR-RV-X (full)', 'L4': 'L4 Transformer'}

def table(tgt):
    y = D[tgt].values[TEST]
    rows = []
    for m in ORDER:
        f = P[(tgt, m)].reindex(idx).values
        rows.append(dict(model=m, MAE=mae_vol(y, f), RMSE=rmse_vol(y, f),
                         MSE_var=mse_var(y, f).mean(), QLIKE=qlike(y, f).mean()))
    return pd.DataFrame(rows).set_index('model')

def decomposition(tgt, loss, name):
    y = D[tgt].values[TEST]
    F = {k: P[(tgt, v)].reindex(idx).values for k, v in LADDER.items()}
    rows = []
    steps = [('Δ_HF  (L1→L2)', 'L1', 'L2'), ('Δ_info (L2→L3)', 'L2', 'L3'), ('Δ_arch (L3→L4)', 'L3', 'L4')]
    tot = loss(y, F['L1']).mean() - loss(y, F['L4']).mean()
    for lab, a, b in steps:
        d = loss(y, F[a]) - loss(y, F[b])
        lo, hi = boot_ci(d)
        stat, p = dm_hln(y, F[b], F[a], loss)
        rows.append(dict(step=lab, delta=d.mean(), ci_lo=lo, ci_hi=hi,
                         share=d.mean() / tot if tot != 0 else np.nan, dm_stat=stat, dm_p=p))
    rows.append(dict(step='合計 (L1→L4)', delta=tot, ci_lo=np.nan, ci_hi=np.nan, share=1.0,
                     dm_stat=dm_hln(y, F['L4'], F['L1'], loss)[0], dm_p=dm_hln(y, F['L4'], F['L1'], loss)[1]))
    R = pd.DataFrame(rows); R.insert(0, 'loss', name)
    return R

def pairwise(tgt):
    y = D[tgt].values[TEST]
    out = []
    pairs = [('L4 Transformer', 'L1 GARCH(1,1)'), ('L4 Transformer', 'L1 GJR-GARCH'),
             ('L4 Transformer', 'L2 HAR-RV'), ('L4 Transformer', 'L3 HAR-RV-X (full)'),
             ('L3 HAR-RV-X (full)', 'L2 HAR-RV'), ('L3 GARCH-X', 'L1 GJR-GARCH'),
             ('L2 HAR-RV', 'L1 GJR-GARCH'), ('L3 HAR-RV-X (opt only)', 'L2 HAR-RV')]
    for a, b in pairs:
        fa, fb = P[(tgt, a)].reindex(idx).values, P[(tgt, b)].reindex(idx).values
        r = dict(model=a, vs=b)
        for nm, L in [('MSE', mse_var), ('QLIKE', qlike)]:
            s, p = dm_hln(y, fa, fb, L)
            r[f'd{nm}'] = L(y, fa).mean() - L(y, fb).mean(); r[f'DM_{nm}_p'] = p
        out.append(r)
    R = pd.DataFrame(out)
    # Clark-West for nested pairs
    cw = []
    for small, big in [('L2 HAR-RV', 'L3 HAR-RV-X (opt only)'), ('L2 HAR-RV', 'L3 HAR-RV-X (full)'),
                       ('L3 HAR-RV-X (opt only)', 'L3 HAR-RV-X (full)')]:
        s, p = clark_west(y, P[(tgt, small)].reindex(idx).values, P[(tgt, big)].reindex(idx).values)
        cw.append(dict(small=small, big=big, CW=s, p=p))
    return R, pd.DataFrame(cw)

def regimes(tgt):
    y = D[tgt].values[TEST]
    vix = np.exp(0.5 * D.lvix.values[TEST])
    masks = {'全部': np.ones(len(y), bool),
             '低 VIX（下三分位）': vix <= np.quantile(vix, 1/3),
             '高 VIX（上三分位）': vix >= np.quantile(vix, 2/3),
             '高波動日（實際前20%）': y >= np.quantile(y, .8),
             '2025/3-5 關稅衝擊': (idx >= '2025-03-01') & (idx <= '2025-05-31')}
    rows = []
    for nm, mk in masks.items():
        for m in ORDER:
            f = P[(tgt, m)].reindex(idx).values
            rows.append(dict(regime=nm, n=int(mk.sum()), model=m,
                             RMSE=rmse_vol(y[mk], f[mk]), QLIKE=qlike(y[mk], f[mk]).mean()))
    return pd.DataFrame(rows)

def economic(tgt='y_hf'):
    # 5-day forward simple return aligned with the forecast date
    r = D.ret_pct.values / 100
    fwd5 = pd.Series(r).rolling(5).sum().shift(-5).values         # t+1..t+5 log return
    # FHS quantiles from the training sample, common to all models (HAR-RV in-sample fit)
    tr = (D.index >= '2011-01-04') & (D.index <= '2020-12-31')
    X = np.c_[np.ones(len(D)), D[HAR].values]; ylog = np.log(D[tgt].values)
    ok = tr & np.isfinite(ylog)
    b = np.linalg.lstsq(X[ok], ylog[ok], rcond=None)[0]
    fit = np.exp(X @ b + 0.5 * np.var(ylog[ok] - X[ok] @ b))
    z = (fwd5 / (fit * np.sqrt(5 / 252)))[ok & np.isfinite(fwd5)]
    zq = {0.05: np.quantile(z, 0.05), 0.01: np.quantile(z, 0.01)}
    rows, sharpe_rows = [], []
    sel = np.where(TEST)[0]
    nonov = sel[::5]                                              # non-overlapping 5-day blocks
    for m in ORDER:
        f_all = P[(tgt, m)].reindex(idx).values
        f_no = pd.Series(f_all, idx).values[::5]
        ret_no = fwd5[nonov]
        keep = np.isfinite(ret_no)
        for a in (0.05, 0.01):
            res = var_backtest(idx[::5][keep], None, f_no[keep], ret_no[keep], zq[a], a)
            rows.append(dict(model=m, alpha=a, **res))
        for c in (1.0, 5.0, 10.0):
            vt = vol_target(idx, f_all, D.ret_pct.values[TEST], cost_bps=c)
            sharpe_rows.append(dict(model=m, cost_bps=c, **{k: v for k, v in vt.items() if k != 'net'}))
    # buy and hold benchmark
    rr = D.ret_pct.values[TEST] / 100
    cum = np.cumprod(1 + rr)
    sharpe_rows.append(dict(model='買進持有 SPY', cost_bps=0, ann_ret=cum[-1] ** (252 / len(rr)) - 1,
                            ann_vol=rr.std() * np.sqrt(252), sharpe=(cum[-1] ** (252 / len(rr)) - 1) / (rr.std() * np.sqrt(252)),
                            maxdd=(1 - cum / np.maximum.accumulate(cum)).max(), turnover=0, avg_w=1.0))
    return pd.DataFrame(rows), pd.DataFrame(sharpe_rows)

if __name__ == '__main__':
    pd.set_option('display.width', 200); pd.set_option('display.max_columns', 40)
    for tgt in ['y_hf', 'y_cc']:
        T = table(tgt); T.to_csv(f'res_main_{tgt}.csv')
        print(f'\n=== 主表 {tgt} ===\n', T.round(4).to_string())
    for tgt in ['y_hf', 'y_cc']:
        dec = pd.concat([decomposition(tgt, mse_var, 'MSE(變異數)'), decomposition(tgt, qlike, 'QLIKE')])
        dec.to_csv(f'res_decomp_{tgt}.csv', index=False)
        print(f'\n=== 分解 {tgt} ===\n', dec.round(4).to_string(index=False))
    for tgt in ['y_hf', 'y_cc']:
        pw, cw = pairwise(tgt); pw.to_csv(f'res_dm_{tgt}.csv', index=False); cw.to_csv(f'res_cw_{tgt}.csv', index=False)
        print(f'\n=== DM {tgt} ===\n', pw.round(4).to_string(index=False))
        print(f'--- Clark-West {tgt} ---\n', cw.round(4).to_string(index=False))
    y = D['y_hf'].values[TEST]
    for nm, L in [('QLIKE', qlike), ('MSE', mse_var)]:
        LM = pd.DataFrame({m: L(y, P[('y_hf', m)].reindex(idx).values) for m in ORDER})
        alive, pv = mcs(LM)
        print(f'\n=== MCS ({nm}, 90%) 存活模型 ===\n', alive)
        json.dump({'loss': nm, 'alive': alive}, open(f'res_mcs_{nm}.json', 'w'), ensure_ascii=False)
    R = regimes('y_hf'); R.to_csv('res_regime.csv', index=False)
    print('\n=== 市場情境 (y_hf) ===\n', R.pivot(index='model', columns='regime', values='QLIKE').round(3).to_string())
    V, S = economic('y_hf'); V.to_csv('res_var.csv', index=False); S.to_csv('res_voltarget.csv', index=False)
    print('\n=== VaR 回測 ===\n', V.round(4).to_string(index=False))
    print('\n=== 波動率目標化投組 ===\n', S.round(4).to_string(index=False))
