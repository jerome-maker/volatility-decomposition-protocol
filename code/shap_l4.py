"""Group-level SHAP diagnostics for the Level-4 Transformer (GPU), and the Granger x SHAP comparison."""
import numpy as np, pandas as pd, json, pickle, time, torch, torch.nn as nn
import shap
from scipy.stats import spearmanr
import l4

D = pd.read_parquet('analysis_daily.parquet')
GROUPS = json.load(open('groups.json', encoding='utf-8'))
FEATS = [c for g in GROUPS.values() for c in g]
DEV = l4.DEV

class Wrap(nn.Module):
    def __init__(s, m): super().__init__(); s.m = m
    def forward(s, x): return s.m(x).unsqueeze(-1)

def main(seeds=10):
    cfg = pickle.load(open('l4_final10.pkl', 'rb'))['cfg']
    L, d, layers, drop, lr = cfg
    runs = []
    for seed in range(seeds):
        r = l4.run(2025, L, d, layers, drop, lr, seed, keep=True)   # last expanding window
        m, bg = r['model'], r['Xtr']
        g = torch.Generator(device='cpu').manual_seed(seed)
        sel = torch.randperm(len(bg), generator=g)[:200]
        t0 = time.perf_counter()
        ex = shap.GradientExplainer(Wrap(m), bg[sel])
        sv = np.asarray(ex.shap_values(r['Xte'], nsamples=100, rseed=seed)).reshape(tuple(r['Xte'].shape))
        runs.append(dict(sv=sv, te=r['te'], secs=r['secs'], shap_secs=time.perf_counter() - t0))
        print(f'seed {seed}: train {r["secs"]:.0f}s, shap {runs[-1]["shap_secs"]:.0f}s', flush=True)
    pickle.dump(dict(cfg=cfg, cols=FEATS, runs=runs), open('shap_l4.pkl', 'wb'))

    # ---- group importance
    agg = [r['sv'].sum(1) for r in runs]                            # (N, F) per seed
    imp = np.array([np.abs(a).mean(0) for a in agg])
    gi = {}
    for g_, cols in GROUPS.items():
        gi[g_] = np.array([sum(imp[s][FEATS.index(c)] for c in cols) for s in range(len(runs))])
    G = pd.DataFrame({'group': list(gi), 'shap_mean': [v.mean() for v in gi.values()],
                      'shap_sd': [v.std() for v in gi.values()]})
    G['share'] = G.shap_mean / G.shap_mean.sum()

    # ---- Granger x SHAP comparison (groups other than the HAR control)
    GR = pd.read_csv('granger_groups.csv')
    M = GR.merge(G, on='group')
    rho, p_rho = spearmanr(M.wald_h5, M.shap_mean)
    rng = np.random.default_rng(0)
    perm = np.array([spearmanr(M.wald_h5, rng.permutation(M.shap_mean.values))[0] for _ in range(10000)])
    p_perm = (perm >= rho).mean()
    k = 3
    top_g = set(M.nlargest(k, 'wald_h5').group); top_s = set(M.nlargest(k, 'shap_mean').group)
    jac = len(top_g & top_s) / len(top_g | top_s)
    res = dict(spearman=float(rho), p_spearman=float(p_rho), p_permutation=float(p_perm),
               jaccard_top3=jac, top3_granger=sorted(top_g), top3_shap=sorted(top_s),
               group_table=M[['group', 'wald_h5', 'p_h5', 'sig_h5_BH', 'shap_mean', 'shap_sd', 'share']].to_dict('records'),
               shap_secs=[r['shap_secs'] for r in runs], device=str(DEV))
    G.to_csv('res_shap_groups.csv', index=False)
    json.dump(res, open('res_shap_granger.json', 'w'), ensure_ascii=False, indent=1, default=float)
    print(G.round(4).to_string(index=False))
    print(json.dumps({k: v for k, v in res.items() if k != 'group_table'}, ensure_ascii=False, indent=1, default=float))

if __name__ == '__main__':
    main()
