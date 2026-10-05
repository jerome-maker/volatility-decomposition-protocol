"""Add SHAR / SHAR-X to the ladder and re-examine Delta_HF."""
import numpy as np, pandas as pd, pickle, json
from evaluate import *
D=pd.read_parquet('analysis_daily.parquet')
GROUPS=json.load(open('groups.json',encoding='utf-8')); FEATS=[c for g in GROUPS.values() for c in g]
P=pickle.load(open('pred_l123.pkl','rb')); L4=pickle.load(open('l4_final10.pkl','rb'))
TEST=(D.index>='2023-01-01')&(D.index<='2025-12-31'); idx=D.index[TEST]
per={}
for (Y,cfg,seed,t),r in L4['runs']:
    if t=='y_hf': per.setdefault(Y,[]).append(pd.Series(r['pred'], D.index[r['te']]))
P[('y_hf','L4 Transformer')]=pd.concat([pd.concat(v,axis=1).mean(axis=1) for v in per.values()]).sort_index()
SHAR=['lrs_pos','lrs_neg','lrv_w','lrv_m']
SHARX=SHAR+[c for c in FEATS if c not in ('lrv_d','lrs_neg')]
def lin(cols,tgt='y_hf'):
    out=[]
    for Y in [2023,2024,2025]:
        tr=np.where((D.index>='2011-01-04')&(D.index<=f'{Y-1}-12-31'))[0][:-5]
        te=np.where((D.index>=f'{Y}-01-01')&(D.index<=f'{Y}-12-31'))[0]
        X=np.c_[np.ones(len(D)), D[cols].values]; y=np.log(D[tgt].values)
        ok=tr[np.isfinite(y[tr])]; b=np.linalg.lstsq(X[ok],y[ok],rcond=None)[0]
        s2=np.var(y[ok]-X[ok]@b)
        out.append(pd.Series(np.exp(X[te]@b+0.5*s2), D.index[te]))
    return pd.concat(out).sort_index()
P[('y_hf','L2 SHAR')]=lin(SHAR); P[('y_hf','L3 SHAR-X')]=lin(SHARX)
pickle.dump(P, open('pred_all.pkl','wb'))
y=D.y_hf.values[TEST]
rows=[]
for m in ['L1 GJR-GARCH','L2 HAR-RV','L2 SHAR','L3 HAR-RV-X (full)','L3 SHAR-X','L4 Transformer']:
    f=P[('y_hf',m)].reindex(idx).values
    rows.append(dict(model=m, MAE=mae_vol(y,f), RMSE=rmse_vol(y,f), QLIKE=qlike(y,f).mean()))
T=pd.DataFrame(rows).set_index('model'); print(T.round(4).to_string())
print()
pairs=[('L2 SHAR','L2 HAR-RV'),('L2 SHAR','L1 GJR-GARCH'),('L3 SHAR-X','L3 HAR-RV-X (full)'),('L4 Transformer','L3 SHAR-X')]
out=[]
for a,b in pairs:
    fa,fb=P[('y_hf',a)].reindex(idx).values,P[('y_hf',b)].reindex(idx).values
    s,p=dm_hln(y,fa,fb,qlike); d=qlike(y,fa).mean()-qlike(y,fb).mean()
    out.append(dict(model=a, vs=b, dQLIKE=d, DM_p=p))
print(pd.DataFrame(out).round(4).to_string(index=False))
print()
# revised decomposition using SHAR as L2 and SHAR-X as L3
F={'L1':P[('y_hf','L1 GJR-GARCH')].reindex(idx).values,'L2':P[('y_hf','L2 SHAR')].reindex(idx).values,
   'L3':P[('y_hf','L3 SHAR-X')].reindex(idx).values,'L4':P[('y_hf','L4 Transformer')].reindex(idx).values}
rows=[]
for lab,a,b in [('Δ_HF  (L1→L2 SHAR)','L1','L2'),('Δ_info (L2→L3 SHAR-X)','L2','L3'),('Δ_arch (L3→L4)','L3','L4')]:
    d=qlike(y,F[a])-qlike(y,F[b]); lo,hi=boot_ci(d); s,p=dm_hln(y,F[b],F[a],qlike)
    rows.append(dict(step=lab, delta=d.mean(), ci_lo=lo, ci_hi=hi, dm_p=p))
R=pd.DataFrame(rows); R.to_csv('res_decomp_shar.csv',index=False); T.to_csv('res_shar_main.csv')
print(R.round(4).to_string(index=False))
# regimes for SHAR
vix=np.exp(0.5*D.lvix.values[TEST])
for nm,mk in [('高波動日（前20%）', y>=np.quantile(y,.8)), ('高 VIX（上三分位）', vix>=np.quantile(vix,2/3))]:
    print('\n'+nm, {m: round(qlike(y[mk],P[('y_hf',m)].reindex(idx).values[mk]).mean(),3) for m in T.index})
