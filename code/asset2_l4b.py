"""Both cross-asset parameterisations (relative vs raw return) x 10 seeds, to separate the
specification effect from seed noise."""
import numpy as np, pandas as pd, json, pickle, time, os, torch
import asset2_l4 as base

CFG = pickle.load(open('l4_final.pkl', 'rb'))['cfg']
VERSIONS = {'rel': 'r_rel', 'abs': 'r_other'}

def job(a):
    torch.set_num_threads(1)
    ver, tkr, Y, seed = a
    D = pd.read_parquet(f'daily_{tkr}_{ver}.parquet')
    base.FEATS = [c if c not in ('r_rel', 'r_other') else VERSIONS[ver] for c in base.FEATS]
    r = base.run(D, Y, *CFG, seed)
    return a, dict(pred=r['pred'], te=r['te'], val_mse=r['val_mse'], secs=r['secs'])

if __name__ == '__main__':
    from multiprocessing import Pool
    jobs = [(v, t, Y, s) for v in VERSIONS for t in ['QQQ', 'SPY'] for Y in [2023, 2024, 2025] for s in range(10)]
    print(len(jobs), 'runs on', base.DEV, flush=True)
    out = []; t0 = time.time()
    with Pool(int(os.environ.get('POOL', '3'))) as p:
        for i, (a, r) in enumerate(p.imap_unordered(job, jobs)):
            out.append((a, r))
            if i % 20 == 0: print(i, a, round(r['val_mse'], 4), f"{r['secs']:.0f}s", flush=True)
    pickle.dump(out, open('l4_asset2_both.pkl', 'wb'))
    print('TOTAL', round(time.time() - t0), 's')
