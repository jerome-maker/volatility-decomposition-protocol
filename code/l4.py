"""Level 4: Transformer on the same information set as L3 (full), expanding-window refit."""
import numpy as np, pandas as pd, json, time, itertools, pickle, os
import torch, torch.nn as nn

DEV = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
A = 252
D = pd.read_parquet('analysis_daily.parquet')
GROUPS = json.load(open('groups.json', encoding='utf-8'))
FEATS = [c for g in GROUPS.values() for c in g]
TEST_YEARS = [2023, 2024, 2025]
START = '2011-01-04'

def split(Y, L):
    """Estimation sample = START..Y-1; its last two calendar years are the validation tail."""
    idx = D.index
    val_lo, val_hi = pd.Timestamp(f'{Y-2}-01-01'), pd.Timestamp(f'{Y-1}-12-31')
    pos = np.arange(len(idx))
    s = idx.searchsorted(pd.Timestamp(START))
    tr = np.where((idx >= START) & (idx < val_lo) & (pos >= s + L - 1))[0][:-5]
    va = np.where((idx >= val_lo) & (idx <= val_hi))[0][:-5]
    te = np.where((idx >= f'{Y}-01-01') & (idx <= f'{Y}-12-31'))[0]
    return tr, va, te

class TF(nn.Module):
    def __init__(s, F, L, d=32, heads=4, layers=2, drop=0.1):
        super().__init__()
        s.inp = nn.Linear(F, d); s.pos = nn.Parameter(torch.randn(1, L, d) * 0.02)
        el = nn.TransformerEncoderLayer(d, heads, 4 * d, drop, batch_first=True, norm_first=True)
        s.enc = nn.TransformerEncoder(el, layers, enable_nested_tensor=False)
        s.head = nn.Sequential(nn.LayerNorm(d), nn.Linear(d, 1))
    def forward(s, x):
        h = s.enc(s.inp(x) + s.pos)
        return s.head(h[:, -1] + h.mean(1)).squeeze(-1)

def wins(X, pos, L):
    return np.stack([X[p - L + 1:p + 1] for p in pos]).astype(np.float32)

def run(Y, L, d, layers, drop, lr, seed, tgt='y_hf', cols=FEATS, max_ep=300, patience=25, bs=64, keep=False):
    tr, va, te = split(Y, L)
    X = D[cols].values; mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-8
    Xs = (X - mu) / sd
    y = np.log(D[tgt].values); ym, ys = y[tr].mean(), y[tr].std()
    Xtr, Xva, Xte = [torch.tensor(wins(Xs, p, L)).to(DEV) for p in (tr, va, te)]
    ytr = torch.tensor(((y[tr] - ym) / ys).astype(np.float32)).to(DEV)
    yva = torch.tensor(((y[va] - ym) / ys).astype(np.float32)).to(DEV)
    torch.manual_seed(seed); np.random.seed(seed)
    heads = 4 if d % 4 == 0 else 2
    m = TF(len(cols), L, d=d, heads=heads, layers=layers, drop=drop).to(DEV)
    opt = torch.optim.AdamW(m.parameters(), lr=lr, weight_decay=1e-3)
    best = (1e9, None, 0); t0 = time.perf_counter(); n = len(tr)
    for ep in range(max_ep):
        m.train(); perm = torch.randperm(n, device=DEV)
        for i in range(0, n, bs):
            b = perm[i:i + bs]; opt.zero_grad()
            loss = nn.functional.mse_loss(m(Xtr[b]), ytr[b]); loss.backward()
            nn.utils.clip_grad_norm_(m.parameters(), 1.0); opt.step()
        m.eval()
        with torch.no_grad(): vl = nn.functional.mse_loss(m(Xva), yva).item()
        if vl < best[0] - 1e-4: best = (vl, {k: v.clone() for k, v in m.state_dict().items()}, ep)
        elif ep - best[2] >= patience: break
    secs = time.perf_counter() - t0
    m.load_state_dict(best[1]); m.eval()
    with torch.no_grad():
        pva = m(Xva).cpu().numpy() * ys + ym
        pte = m(Xte).cpu().numpy() * ys + ym
    s2 = np.var(y[va] - pva)
    out = dict(val_mse=best[0], secs=secs, epochs=ep + 1, best_ep=best[2], n_train=n,
               pred=np.exp(pte + 0.5 * s2), te=te, params=sum(p.numel() for p in m.parameters()))
    if keep: out.update(model=m, Xte=Xte, Xtr=Xtr, mu=mu, sd=sd, ys=ys, ym=ym)
    return out

def _search_job(a):
    torch.set_num_threads(1)
    L, d, layers, drop, lr, seed = a
    r = run(2023, L, d, layers, drop, lr, seed)
    return a, r['val_mse'], r['secs'], r['best_ep']

def _final_job(a):
    torch.set_num_threads(1)
    Y, cfg, seed, tgt = a
    r = run(Y, *cfg, seed, tgt=tgt)
    return a, {k: r[k] for k in ('pred', 'te', 'val_mse', 'secs', 'epochs', 'best_ep', 'n_train', 'params')}

if __name__ == '__main__':
    from multiprocessing import Pool
    POOL = int(os.environ.get('POOL', '3'))
    print('device', DEV, '| cuda available:', torch.cuda.is_available(), flush=True)
    GRID = list(itertools.product([22, 44], [16, 32, 64], [1, 2], [0.1, 0.3], [3e-4, 1e-3], [0, 1]))
    t0 = time.time(); res = []
    with Pool(POOL) as p:
        for i, (a, vm, s, be) in enumerate(p.imap_unordered(_search_job, GRID)):
            res.append((a, vm, s, be))
            if i % 12 == 0: print(f'search {i}/{len(GRID)} {a} val={vm:.4f} {s:.0f}s', flush=True)
    pickle.dump(res, open('l4_search.pkl', 'wb'))
    S = pd.DataFrame([dict(L=a[0], d=a[1], layers=a[2], drop=a[3], lr=a[4], seed=a[5], val=v, secs=s) for a, v, s, _ in res])
    g = S.groupby(['L', 'd', 'layers', 'drop', 'lr']).val.mean().sort_values()
    print('search wall', time.time() - t0, '\n', g.head(8).round(4).to_string(), flush=True)
    cfg = g.index[0]                                   # (L, d, layers, drop, lr)
    print('chosen config', cfg, flush=True)
    jobs = [(Y, cfg, seed, tgt) for Y in TEST_YEARS for seed in range(5) for tgt in ['y_hf', 'y_cc']]
    out = []
    with Pool(POOL) as p:
        for a, r in p.imap_unordered(_final_job, jobs):
            out.append((a, r)); print('final', a[0], a[2], a[3], round(r['val_mse'], 4), f"{r['secs']:.0f}s", flush=True)
    pickle.dump(dict(cfg=cfg, runs=out, grid=res), open('l4_final.pkl', 'wb'))
    print('TOTAL', time.time() - t0)
