"""LSTM control at Level 4: same information set, same training protocol and same evaluation as the
Transformer, so that 'the architecture adds nothing' is not a statement about one architecture only."""
import numpy as np, pandas as pd, json, time, itertools, pickle, os
import torch, torch.nn as nn
from l4 import split, wins, DEV, D, FEATS

TEST_YEARS = [2023, 2024, 2025]

class LSTM(nn.Module):
    def __init__(s, F, hidden=64, layers=1, drop=0.1):
        super().__init__()
        s.rnn = nn.LSTM(F, hidden, num_layers=layers, batch_first=True,
                        dropout=drop if layers > 1 else 0.0)
        s.head = nn.Sequential(nn.LayerNorm(hidden), nn.Dropout(drop), nn.Linear(hidden, 1))
    def forward(s, x):
        h, _ = s.rnn(x)
        return s.head(h[:, -1]).squeeze(-1)

def run(Y, L, hidden, layers, drop, lr, seed, tgt='y_hf', cols=FEATS,
        max_ep=300, patience=25, bs=64):
    tr, va, te = split(Y, L)
    X = D[cols].values; mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-8
    Xs = (X - mu) / sd
    y = np.log(D[tgt].values); ym, ys = y[tr].mean(), y[tr].std()
    Xtr, Xva, Xte = [torch.tensor(wins(Xs, p, L)).to(DEV) for p in (tr, va, te)]
    ytr = torch.tensor(((y[tr] - ym) / ys).astype(np.float32)).to(DEV)
    yva = torch.tensor(((y[va] - ym) / ys).astype(np.float32)).to(DEV)
    torch.manual_seed(seed); np.random.seed(seed)
    m = LSTM(len(cols), hidden=int(hidden), layers=int(layers), drop=float(drop)).to(DEV)
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
    return dict(pred=np.exp(pte + 0.5 * s2), te=te, val_mse=best[0], secs=time.perf_counter() - t0,
                epochs=ep + 1, params=sum(p.numel() for p in m.parameters()))

def _search(a):
    torch.set_num_threads(1)
    hidden, layers, drop, lr, seed = a
    r = run(2023, 22, hidden, layers, drop, lr, seed)
    return a, r['val_mse'], r['secs'], r['params']

def _final(a):
    torch.set_num_threads(1)
    Y, cfg, seed, tgt = a
    r = run(Y, 22, *cfg, seed, tgt=tgt)
    return a, {k: r[k] for k in ('pred', 'te', 'val_mse', 'secs', 'epochs', 'params')}

if __name__ == '__main__':
    from multiprocessing import Pool
    POOL = int(os.environ.get('POOL', '3'))
    print('device', DEV, flush=True)
    GRID = list(itertools.product([32, 64, 128], [1, 2], [0.1, 0.3], [3e-4, 1e-3], [0, 1]))
    t0 = time.time(); res = []
    with Pool(POOL) as p:
        for i, (a, vm, s, npar) in enumerate(p.imap_unordered(_search, GRID)):
            res.append((a, vm, s, npar))
            if i % 12 == 0: print(f'search {i}/{len(GRID)} {a} val={vm:.4f} {s:.0f}s {npar} params', flush=True)
    S = pd.DataFrame([dict(hidden=a[0], layers=a[1], drop=a[2], lr=a[3], seed=a[4], val=v, params=n)
                      for a, v, s, n in res])
    g = S.groupby(['hidden', 'layers', 'drop', 'lr']).val.mean().sort_values()
    print('search wall', round(time.time() - t0), '\n', g.head(6).round(4).to_string(), flush=True)
    cfg = tuple(np.asarray(g.index[0]).tolist())
    print('chosen LSTM config (hidden, layers, drop, lr):', cfg, flush=True)
    jobs = [(Y, cfg, s, t) for Y in TEST_YEARS for s in range(10) for t in ['y_hf', 'y_cc']]
    out = []
    with Pool(POOL) as p:
        for i, (a, r) in enumerate(p.imap_unordered(_final, jobs)):
            out.append((a, r))
            if i % 15 == 0: print('final', i, a[0], a[2], a[3], round(r['val_mse'], 4), flush=True)
    pickle.dump(dict(cfg=cfg, runs=out, search=res, n_seeds=10), open('lstm_final.pkl', 'wb'))
    print('params', out[0][1]['params'], '| TOTAL', round(time.time() - t0), 's')
