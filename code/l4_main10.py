"""Re-run the main-analysis Level 4 with 10 seeds (hyperparameters unchanged, taken from the original search)."""
import numpy as np, pandas as pd, pickle, time, os, torch
import l4

CFG = pickle.load(open('l4_final.pkl', 'rb'))['cfg']

def job(a):
    torch.set_num_threads(1)
    Y, seed, tgt = a
    r = l4.run(Y, *CFG, seed, tgt=tgt)
    return a, {k: r[k] for k in ('pred', 'te', 'val_mse', 'secs', 'epochs', 'best_ep', 'n_train', 'params')}

if __name__ == '__main__':
    from multiprocessing import Pool
    jobs = [(Y, s, t) for Y in [2023, 2024, 2025] for s in range(10) for t in ['y_hf', 'y_cc']]
    print(len(jobs), 'runs on', l4.DEV, '| cfg', CFG, flush=True)
    out = []; t0 = time.time()
    with Pool(int(os.environ.get('POOL', '3'))) as p:
        for i, (a, r) in enumerate(p.imap_unordered(job, jobs)):
            out.append(((a[0], CFG, a[1], a[2]), r))          # keep the original key layout
            if i % 15 == 0: print(i, a, round(r['val_mse'], 4), f"{r['secs']:.0f}s", flush=True)
    pickle.dump(dict(cfg=CFG, runs=out, n_seeds=10), open('l4_final10.pkl', 'wb'))
    print('TOTAL', round(time.time() - t0), 's')
