"""Compare the two cross-asset parameterisations (relative vs raw return) with 10 seeds each."""
import numpy as np, pandas as pd, pickle, json
from evaluate import qlike, rmse_vol, dm_hln, boot_ci

L = pickle.load(open('l4_asset2_both.pkl', 'rb'))
P123 = pickle.load(open('pred_asset2.pkl', 'rb'))          # L0-L3 (identical across the two versions)
rng = np.random.default_rng(11)
rows, ens_store, seed_store = [], {}, []

for tkr in ['QQQ', 'SPY']:
    D = pd.read_parquet(f'daily_{tkr}.parquet')
    m = (D.index >= '2023-01-01') & (D.index <= '2025-12-31'); ix = D.index[m]
    y = D.y.values[m]; ok = np.isfinite(y); yy = y[ok]
    for ver in ['rel', 'abs']:
        per = {}
        for (v, t, Y, seed), r in L:
            if v != ver or t != tkr: continue
            per.setdefault(seed, []).append(pd.Series(r['pred'], D.index[r['te']]))
        seeds = sorted(per)
        q = []
        for s in seeds:
            f = pd.concat(per[s]).sort_index().reindex(ix).values[ok]
            q.append(qlike(yy, f).mean()); seed_store.append(dict(asset=tkr, spec=ver, seed=s, QLIKE=q[-1]))
        E = pd.concat([pd.concat(per[s]).sort_index() for s in seeds], axis=1).mean(axis=1).reindex(ix)
        ens_store[(tkr, ver)] = E
        f = E.values[ok]
        rows.append(dict(asset=tkr, spec=ver, n_seeds=len(seeds), seed_mean=np.mean(q), seed_sd=np.std(q),
                         seed_min=min(q), seed_max=max(q), ens_QLIKE=qlike(yy, f).mean(), ens_RMSE=rmse_vol(yy, f)))
    # paired comparison between the two specifications
    fr = ens_store[(tkr, 'rel')].values[ok]; fa = ens_store[(tkr, 'abs')].values[ok]
    d = qlike(yy, fr) - qlike(yy, fa)
    lo, hi = boot_ci(d)
    stat, p = dm_hln(yy, fr, fa, qlike)
    # seed-level permutation test: is the specification gap larger than seed reshuffling implies?
    qr = [s['QLIKE'] for s in seed_store if s['asset'] == tkr and s['spec'] == 'rel']
    qa = [s['QLIKE'] for s in seed_store if s['asset'] == tkr and s['spec'] == 'abs']
    obs = np.mean(qr) - np.mean(qa)
    pool = np.array(qr + qa); perm = []
    for _ in range(10000):
        p2 = rng.permutation(pool)
        perm.append(p2[:len(qr)].mean() - p2[len(qr):].mean())
    p_perm = (np.abs(perm) >= abs(obs)).mean()
    rows.append(dict(asset=tkr, spec='rel − abs（差異）', n_seeds=np.nan, seed_mean=obs, seed_sd=np.nan,
                     seed_min=lo, seed_max=hi, ens_QLIKE=qlike(yy, fr).mean() - qlike(yy, fa).mean(), ens_RMSE=p))
    print(f'{tkr}: 種子平均差 {obs:+.4f}（置換檢定 p={p_perm:.3f}）；集成差 {qlike(yy,fr).mean()-qlike(yy,fa).mean():+.4f}'
          f'（DM p={p:.3f}，拔靴法 90% 區間 [{lo:+.4f}, {hi:+.4f}]）')

R = pd.DataFrame(rows); S = pd.DataFrame(seed_store)
R.to_csv('res_asset2_spec.csv', index=False); S.to_csv('res_asset2_spec_seeds.csv', index=False)
pickle.dump(ens_store, open('pred_asset2_spec.pkl', 'wb'))
pd.set_option('display.width', 200)
print('\n', R.round(4).to_string(index=False))

# decomposition under each specification (L1-L3 are invariant, only Delta_arch moves)
dec = []
for tkr in ['QQQ', 'SPY']:
    D = pd.read_parquet(f'daily_{tkr}.parquet')
    m = (D.index >= '2023-01-01') & (D.index <= '2025-12-31'); ix = D.index[m]
    y = D.y.values[m]; ok = np.isfinite(y); yy = y[ok]
    l3 = P123[tkr]['L3 HAR-GK-X (full)'].reindex(ix).values[ok]
    for ver in ['rel', 'abs']:
        f = ens_store[(tkr, ver)].values[ok]
        d = qlike(yy, l3) - qlike(yy, f); lo, hi = boot_ci(d); _, p = dm_hln(yy, f, l3, qlike)
        dec.append(dict(asset=tkr, spec=ver, delta_arch=d.mean(), ci_lo=lo, ci_hi=hi, dm_p=p))
DEC = pd.DataFrame(dec); DEC.to_csv('res_asset2_decomp_spec.csv', index=False)
print('\nΔ_arch（10 個種子集成）\n', DEC.round(4).to_string(index=False))
