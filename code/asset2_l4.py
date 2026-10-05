"""Level 4 for the second-asset robustness check (QQQ and SPY, daily information set), on GPU."""
import numpy as np, pandas as pd, json, pickle, time, os
import torch, torch.nn as nn
from l4 import TF, wins
DEV = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
GROUPS = json.load(open('groups2.json', encoding='utf-8'))
FEATS = [c for g in GROUPS.values() for c in g]
START, TEST_YEARS = '2011-01-04', [2023, 2024, 2025]
CFG = pickle.load(open('l4_final.pkl', 'rb'))['cfg']          # reuse the config chosen for SPY (no new search)

def split(D, Y, L):
    idx = D.index; pos = np.arange(len(idx))
    s = idx.searchsorted(pd.Timestamp(START))
    val_lo, val_hi = pd.Timestamp(f'{Y-2}-01-01'), pd.Timestamp(f'{Y-1}-12-31')
    tr = np.where((idx >= START) & (idx < val_lo) & (pos >= s + L - 1))[0][:-5]
    va = np.where((idx >= val_lo) & (idx <= val_hi))[0][:-5]
    te = np.where((idx >= f'{Y}-01-01') & (idx <= f'{Y}-12-31'))[0]
    return tr, va, te

def run(D, Y, L, d, layers, drop, lr, seed, max_ep=300, patience=25, bs=64):
    tr, va, te = split(D, Y, L)
    X = D[FEATS].values; mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-8
    Xs = (X - mu) / sd
    y = np.log(D.y.values); ym, ys = y[tr].mean(), y[tr].std()
    Xtr, Xva, Xte = [torch.tensor(wins(Xs, p, L)).to(DEV) for p in (tr, va, te)]
    ytr = torch.tensor(((y[tr] - ym) / ys).astype(np.float32)).to(DEV)
    yva = torch.tensor(((y[va] - ym) / ys).astype(np.float32)).to(DEV)
    torch.manual_seed(seed); np.random.seed(seed)
    m = TF(len(FEATS), L, d=d, heads=4, layers=layers, drop=drop).to(DEV)
    opt = torch.optim.AdamW(m.parameters(), lr=lr, weight_decay=1e-3)
    best = (1e9, None, 0); t0 = time.perf_counter(); n = len(tr)
    for ep in range(max_ep):
        m.train(); perm = torch.randperm(n, device=DEV)
        for i in range(0, n, bs):
            b = perm[i:i + bs]; opt.zero_grad()
            nn.functional.mse_loss(m(Xtr[b]), ytr[b]).backward()
            nn.utils.clip_grad_norm_(m.parameters(), 1.0); opt.step()
        m.eval()
        with torch.no_grad(): vl = nn.functional.mse_loss(m(Xva), yva).item()
        if vl < best[0] - 1e-4: best = (vl, {k: v.clone() for k, v in m.state_dict().items()}, ep)
        elif ep - best[2] >= patience: break
    m.load_state_dict(best[1]); m.eval()
    with torch.no_grad():
        pva = m(Xva).cpu().numpy() * ys + ym; pte = m(Xte).cpu().numpy() * ys + ym
    s2 = np.var(y[va] - pva)
    return dict(pred=np.exp(pte + 0.5 * s2), te=te, val_mse=best[0], secs=time.perf_counter() - t0, epochs=ep + 1)

def job(a):
    torch.set_num_threads(1)
    tkr, Y, seed = a
    D = pd.read_parquet(f'daily_{tkr}.parquet')
    r = run(D, Y, *CFG, seed)
    return a, r

if __name__ == '__main__':
    from multiprocessing import Pool
    jobs = [(t, Y, s) for t in ['QQQ', 'SPY'] for Y in TEST_YEARS for s in range(5)]
    out = []
    t0 = time.time()
    with Pool(int(os.environ.get('POOL', '3'))) as p:
        for a, r in p.imap_unordered(job, jobs):
            out.append((a, r)); print(a, round(r['val_mse'], 4), f"{r['secs']:.0f}s", flush=True)
    pickle.dump(out, open('l4_asset2.pkl', 'wb'))
    print('TOTAL', time.time() - t0)
