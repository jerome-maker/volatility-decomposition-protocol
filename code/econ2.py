"""Economic evaluation with the current 10-seed ensembles, including the LSTM control."""
import numpy as np, pandas as pd, pickle
from evaluate import *
D=pd.read_parquet('analysis_daily.parquet'); P=pickle.load(open('pred_all.pkl','rb'))
TEST=(D.index>='2023-01-01')&(D.index<='2025-12-31'); idx=D.index[TEST]
MODELS=['L0 Naive','L1 GARCH(1,1)','L1 GJR-GARCH','L2 HAR-RV','L3 HAR-RV-X (opt only)','L3 HAR-RV-X (full)','L3 GARCH-X','L4 Transformer','L4 LSTM']
HAR=['lrv_d','lrv_w','lrv_m']
r=D.ret_pct.values/100
fwd5=pd.Series(r).rolling(5).sum().shift(-5).values
tr=(D.index>='2011-01-04')&(D.index<='2020-12-31')
X=np.c_[np.ones(len(D)), D[HAR].values]; yl=np.log(D.y_hf.values); ok=tr&np.isfinite(yl)
b=np.linalg.lstsq(X[ok],yl[ok],rcond=None)[0]
fit=np.exp(X@b+0.5*np.var(yl[ok]-X[ok]@b))
z=(fwd5/(fit*np.sqrt(5/252)))[ok&np.isfinite(fwd5)]
zq={0.05:np.quantile(z,0.05),0.01:np.quantile(z,0.01)}
sel=np.where(TEST)[0]; nonov=sel[::5]
rows=[]
for m in MODELS:
    f=P[('y_hf',m)].reindex(idx).values; fno=f[::5]; rno=fwd5[nonov]; keep=np.isfinite(rno)
    for a in (0.05,0.01):
        rows.append(dict(model=m, alpha=a, **var_backtest(idx[::5][keep], None, fno[keep], rno[keep], zq[a], a)))
V=pd.DataFrame(rows); V.to_csv('res_var10.csv',index=False)
ret=D.ret_pct.values[TEST]
srows=[]; nets={}
for m in MODELS:
    f=P[('y_hf',m)].reindex(idx).values
    for c in (1.0,5.0,10.0):
        vt=vol_target(idx,f,ret,cost_bps=c)
        if c==5.0: nets[m]=vt['net']
        srows.append(dict(model=m, cost_bps=c, **{k:v for k,v in vt.items() if k!='net'}))
cum=np.cumprod(1+ret/100)
srows.append(dict(model='Buy and hold', cost_bps=0, ann_ret=cum[-1]**(252/len(ret))-1, ann_vol=(ret/100).std()*np.sqrt(252),
                  sharpe=(cum[-1]**(252/len(ret))-1)/((ret/100).std()*np.sqrt(252)), maxdd=(1-cum/np.maximum.accumulate(cum)).max(), turnover=0, avg_w=1.0))
S=pd.DataFrame(srows); S.to_csv('res_voltarget10.csv',index=False)
pd.set_option('display.width',220)
print(V[V.alpha==0.05].round(4).to_string(index=False))
print()
print(S[(S.cost_bps==5)|(S.model=='Buy and hold')].round(4).to_string(index=False))
# Sharpe differences, block bootstrap
def sr(x): return x.mean()/x.std()*np.sqrt(252)
idxb=block_boot_idx(len(ret),2000,20)
print('\nSharpe（成本 5bp）與差異的 90% 拔靴法區間')
base='L1 GJR-GARCH'
res=[]
for m in ['L3 HAR-RV-X (full)','L4 Transformer','L4 LSTM','L2 HAR-RV']:
    d=[sr(nets[m][i])-sr(nets[base][i]) for i in idxb]
    lo,hi=np.percentile(d,[5,95]); res.append(dict(model=m, vs=base, sharpe=sr(nets[m]), lo=lo, hi=hi))
base2='L3 HAR-RV-X (full)'
for m in ['L4 Transformer','L4 LSTM']:
    d=[sr(nets[m][i])-sr(nets[base2][i]) for i in idxb]
    lo,hi=np.percentile(d,[5,95]); res.append(dict(model=m, vs=base2, sharpe=sr(nets[m]), lo=lo, hi=hi))
R=pd.DataFrame(res); R.to_csv('res_sharpe_ci.csv',index=False)
print('GJR Sharpe %.2f'%sr(nets[base]))
print(R.round(3).to_string(index=False))
