"""Final LSTM runs with the configuration already selected on the validation sample."""
import numpy as np, pickle, time, os, torch
import lstm
CFG = (128, 1, 0.3, 3e-4)      # chosen by validation MSE over 24 configurations x 2 seeds
def job(a):
    torch.set_num_threads(1)
    Y, seed, tgt = a
    r = lstm.run(Y, 22, *CFG, seed, tgt=tgt)
    return (Y, CFG, seed, tgt), {k: r[k] for k in ('pred','te','val_mse','secs','epochs','params')}
if __name__ == '__main__':
    from multiprocessing import Pool
    jobs=[(Y,s,t) for Y in [2023,2024,2025] for s in range(10) for t in ['y_hf','y_cc']]
    out=[]; t0=time.time()
    with Pool(int(os.environ.get('POOL','3'))) as p:
        for i,(a,r) in enumerate(p.imap_unordered(job, jobs)):
            out.append((a,r))
            if i%15==0: print(i, a[0], a[2], a[3], round(r['val_mse'],4), flush=True)
    search=pickle.load(open('lstm_search.pkl','rb')) if os.path.exists('lstm_search.pkl') else None
    pickle.dump(dict(cfg=CFG, runs=out, n_seeds=10, params=out[0][1]['params']), open('lstm_final.pkl','wb'))
    print('params', out[0][1]['params'], '| TOTAL', round(time.time()-t0), 's')
