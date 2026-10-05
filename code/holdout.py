"""Final hold-out: the 2026 year that was reserved before the design was frozen.

Everything is estimated on data through 2025-12-31 using the protocol already fixed in the paper.
This script is run once; its output is reported whatever it shows.
"""
import numpy as np, pandas as pd, pickle, json, time, os, warnings
warnings.filterwarnings('ignore')

import sys
STAGE = sys.argv[1] if len(sys.argv) > 1 else 'all'
if STAGE in ('econ', 'eval', 'all'):
    import ladder as L123                       # needs the econometrics environment (arch, statsmodels)
from evaluate import qlike, mse_var, rmse_vol, mae_vol, dm_hln, boot_ci

D = pd.read_parquet('analysis_daily.parquet')
GROUPS = json.load(open('groups.json', encoding='utf-8'))
FEATS = [c for g in GROUPS.values() for c in g]
HAR = GROUPS['G1 歷史已實現變異']
OPT = GROUPS['G3 選擇權前瞻']
Y = 2026
START = '2011-01-04'

def windows():
    tr = np.where((D.index >= START) & (D.index <= '2025-12-31'))[0][:-5]
    te = np.where((D.index >= '2026-01-01') & (D.index <= '2026-12-31'))[0]
    return tr, te

def main_econometrics():
    tr, te = windows()
    idx = D.index[te]
    P = {}
    for tgt in ['y_hf', 'y_cc']:
        P[(tgt, 'L0 Naive')] = pd.Series(L123.naive(tgt, te), idx)
        P[(tgt, 'L2 HAR-RV')] = pd.Series(L123.linreg(tgt, HAR, tr, te), idx)
        P[(tgt, 'L3 HAR-RV-X (opt only)')] = pd.Series(L123.linreg(tgt, HAR + OPT, tr, te), idx)
        P[(tgt, 'L3 HAR-RV-X (full)')] = pd.Series(L123.linreg(tgt, FEATS, tr, te), idx)
    for lab, gjr in [('L1 GARCH(1,1)', False), ('L1 GJR-GARCH', True)]:
        f, _ = L123.garch(tr, te, gjr)
        for tgt in ['y_hf', 'y_cc']: P[(tgt, lab)] = pd.Series(f, idx)
    f, par = L123.garch_x(tr, te)
    for tgt in ['y_hf', 'y_cc']: P[(tgt, 'L3 GARCH-X')] = pd.Series(f, idx)
    print('GARCH-X on the hold-out window:', {k: round(v, 4) for k, v in par.items()}, flush=True)
    return P, idx

def _tf(a):
    import torch; torch.set_num_threads(1)
    import l4
    seed, tgt = a
    cfg = pickle.load(open('l4_final10.pkl', 'rb'))['cfg']
    r = l4.run(Y, *cfg, seed, tgt=tgt)
    return ('Transformer', seed, tgt), r['pred'], r['te']

def _ls(a):
    import torch; torch.set_num_threads(1)
    import lstm
    seed, tgt = a
    r = lstm.run(Y, 22, 128, 1, 0.3, 3e-4, seed, tgt=tgt)
    return ('LSTM', seed, tgt), r['pred'], r['te']

if __name__ == '__main__':
    from multiprocessing import Pool
    t0 = time.time()
    _, te0 = windows(); idx = D.index[te0]

    if STAGE == 'econ':
        P, idx = main_econometrics()
        pickle.dump(P, open('pred_holdout_econ.pkl', 'wb'))
        print('econometrics done', round(time.time() - t0), 's'); sys.exit()

    if STAGE == 'nets':
        jobs = [(s, t) for s in range(10) for t in ['y_hf', 'y_cc']]
        nets = {}
        with Pool(int(os.environ.get('POOL', '3'))) as p:
            for fn, nm in ((_tf, 'Transformer'), (_ls, 'LSTM')):
                for (name, seed, tgt), pred, te in p.imap_unordered(fn, jobs):
                    nets.setdefault((tgt, 'L4 ' + name), []).append(pd.Series(pred, D.index[te]))
                print(nm, 'done', round(time.time() - t0), 's', flush=True)
        ens = {k: pd.concat(v, axis=1).mean(axis=1) for k, v in nets.items()}
        pickle.dump(ens, open('pred_holdout_nets.pkl', 'wb'))
        print('networks done', round(time.time() - t0), 's'); sys.exit()

    P = pickle.load(open('pred_holdout_econ.pkl', 'rb'))
    P.update(pickle.load(open('pred_holdout_nets.pkl', 'rb')))
    pickle.dump(P, open('pred_holdout2026.pkl', 'wb'))

    ORDER = ['L0 Naive', 'L1 GARCH(1,1)', 'L1 GJR-GARCH', 'L2 HAR-RV', 'L3 HAR-RV-X (opt only)',
             'L3 HAR-RV-X (full)', 'L3 GARCH-X', 'L4 Transformer', 'L4 LSTM']
    rows, dec = [], []
    for tgt in ['y_hf', 'y_cc']:
        y = D[tgt].reindex(idx).values
        ok = np.isfinite(y)
        for m in ORDER:
            f = P[(tgt, m)].reindex(idx).values
            rows.append(dict(target=tgt, model=m, n=int(ok.sum()), MAE=mae_vol(y[ok], f[ok]),
                             RMSE=rmse_vol(y[ok], f[ok]), QLIKE=qlike(y[ok], f[ok]).mean()))
        F = {k: P[(tgt, v)].reindex(idx).values[ok] for k, v in
             {'L1': 'L1 GJR-GARCH', 'L2': 'L2 HAR-RV', 'L3': 'L3 HAR-RV-X (full)', 'L4': 'L4 Transformer'}.items()}
        yy = y[ok]
        for lab, a, b in [('Δ_HF', 'L1', 'L2'), ('Δ_info', 'L2', 'L3'), ('Δ_arch', 'L3', 'L4')]:
            d = qlike(yy, F[a]) - qlike(yy, F[b]); lo, hi = boot_ci(d); _, pv = dm_hln(yy, F[b], F[a], qlike)
            dec.append(dict(target=tgt, step=lab, delta=d.mean(), ci_lo=lo, ci_hi=hi, dm_p=pv))
        fl = P[(tgt, 'L4 LSTM')].reindex(idx).values[ok]; l3 = F['L3']
        d = qlike(yy, l3) - qlike(yy, fl); lo, hi = boot_ci(d); _, pv = dm_hln(yy, fl, l3, qlike)
        dec.append(dict(target=tgt, step='Δ_arch (LSTM)', delta=d.mean(), ci_lo=lo, ci_hi=hi, dm_p=pv))
    M = pd.DataFrame(rows); DE = pd.DataFrame(dec)
    M.to_csv('res_holdout_main.csv', index=False); DE.to_csv('res_holdout_decomp.csv', index=False)
    pd.set_option('display.width', 200)
    print('\n=== 2026 hold-out, evaluation days:', int(np.isfinite(D['y_hf'].reindex(idx).values).sum()), '===')
    print(M.pivot(index='model', columns='target', values=['RMSE', 'QLIKE']).round(4).to_string())
    print('\n', DE.round(4).to_string(index=False))
    print('\nTOTAL', round(time.time() - t0), 's')
