"""Evaluate the LSTM control and add it to the Level-4 comparison."""
import numpy as np, pandas as pd, pickle, json
from evaluate import mse_var, qlike, rmse_vol, mae_vol, dm_hln, boot_ci, mcs
D=pd.read_parquet('analysis_daily.parquet')
P=pickle.load(open('pred_all.pkl','rb'))
LS=pickle.load(open('lstm_final.pkl','rb'))
TF=pickle.load(open('l4_final10.pkl','rb'))
TEST=(D.index>='2023-01-01')&(D.index<='2025-12-31'); idx=D.index[TEST]
for tgt in ['y_hf','y_cc']:                      # rebuild the 10-seed Transformer ensembles
    per={}
    for (Y,cfg,seed,t),r in TF['runs']:
        if t==tgt: per.setdefault(Y,[]).append(pd.Series(r['pred'], D.index[r['te']]))
    P[(tgt,'L4 Transformer')]=pd.concat([pd.concat(v,axis=1).mean(axis=1) for v in per.values()]).sort_index()
rows=[]; seed_rows=[]
for tgt in ['y_hf','y_cc']:
    per={}
    for (Y,cfg,seed,t),r in LS['runs']:
        if t!=tgt: continue
        per.setdefault(seed,[]).append(pd.Series(r['pred'], D.index[r['te']]))
    y=D[tgt].values[TEST]
    for s,v in per.items():
        f=pd.concat(v).sort_index().reindex(idx).values
        seed_rows.append(dict(target=tgt, seed=s, QLIKE=qlike(y,f).mean(), RMSE=rmse_vol(y,f)))
    E=pd.concat([pd.concat(per[s]).sort_index() for s in sorted(per)],axis=1).mean(axis=1).sort_index()
    P[(tgt,'L4 LSTM')]=E
pickle.dump(P, open('pred_all.pkl','wb'))
SEED=pd.DataFrame(seed_rows); SEED.to_csv('res_lstm_seeds.csv',index=False)
ORDER=['L1 GJR-GARCH','L2 HAR-RV','L3 HAR-RV-X (full)','L4 Transformer','L4 LSTM']
for tgt in ['y_hf','y_cc']:
    y=D[tgt].values[TEST]
    for m in ORDER:
        f=P[(tgt,m)].reindex(idx).values
        rows.append(dict(target=tgt, model=m, MAE=mae_vol(y,f), RMSE=rmse_vol(y,f), QLIKE=qlike(y,f).mean()))
M=pd.DataFrame(rows); M.to_csv('res_lstm_main.csv',index=False)
pd.set_option('display.width',200)
print(M.pivot(index='model',columns='target',values=['RMSE','QLIKE']).round(4).to_string())
print('\n各種子 QLIKE（目標 A）:', np.round(sorted(SEED[SEED.target=="y_hf"].QLIKE),4))
print('LSTM 參數量', LS['params'], '| Transformer 26,817')
# Delta_arch for both architectures + head-to-head
out=[]
for tgt in ['y_hf','y_cc']:
    y=D[tgt].values[TEST]
    l3=P[(tgt,'L3 HAR-RV-X (full)')].reindex(idx).values
    for arch in ['L4 Transformer','L4 LSTM']:
        f=P[(tgt,arch)].reindex(idx).values
        d=qlike(y,l3)-qlike(y,f); lo,hi=boot_ci(d); _,p=dm_hln(y,f,l3,qlike)
        out.append(dict(target=tgt, arch=arch, delta_arch=d.mean(), ci_lo=lo, ci_hi=hi, dm_p=p))
    ft,fl=P[(tgt,'L4 Transformer')].reindex(idx).values,P[(tgt,'L4 LSTM')].reindex(idx).values
    _,p=dm_hln(y,ft,fl,qlike)
    out.append(dict(target=tgt, arch='Transformer − LSTM', delta_arch=qlike(y,ft).mean()-qlike(y,fl).mean(),
                    ci_lo=np.nan, ci_hi=np.nan, dm_p=p))
A=pd.DataFrame(out); A.to_csv('res_lstm_decomp.csv',index=False)
print('\n', A.round(4).to_string(index=False))
y=D['y_hf'].values[TEST]
LM=pd.DataFrame({m: qlike(y,P[('y_hf',m)].reindex(idx).values) for m in
                 ['L0 Naive','L1 GARCH(1,1)','L1 GJR-GARCH','L2 HAR-RV','L3 HAR-RV-X (opt only)','L3 HAR-RV-X (full)','L3 GARCH-X','L4 Transformer','L4 LSTM']})
alive,_=mcs(LM); json.dump({'alive':alive}, open('res_mcs_QLIKE_with_lstm.json','w'), ensure_ascii=False)
print('\nMCS(QLIKE, 90%) 含 LSTM:', alive)
