import numpy as np, pandas as pd, pickle, json
from evaluate import mse_var, qlike, rmse_vol, mae_vol, dm_hln, clark_west, boot_ci, mcs
S=pickle.load(open('pred_asset2.pkl','rb')); L4=pickle.load(open('l4_asset2.pkl','rb'))
for tkr in ['QQQ','SPY']:
    per={}
    for (t,Y,seed),r in L4:
        if t!=tkr: continue
        D=pd.read_parquet(f'daily_{tkr}.parquet'); per.setdefault(Y,[]).append(pd.Series(r['pred'], D.index[r['te']]))
    S[tkr]['L4 Transformer']=pd.concat([pd.concat(v,axis=1).mean(axis=1) for v in per.values()]).sort_index()
ORDER=['L0 Naive','L1 GARCH(1,1)','L1 GJR-GARCH','L2 HAR-GK','L3 HAR-GK-X (opt only)','L3 HAR-GK-X (full)','L4 Transformer']
LAD={'L1':'L1 GJR-GARCH','L2':'L2 HAR-GK','L3':'L3 HAR-GK-X (full)','L4':'L4 Transformer'}
main=[]; dec=[]; dm=[]; mcsres={}
for tkr in ['QQQ','SPY']:
    D=pd.read_parquet(f'daily_{tkr}.parquet')
    TEST=(D.index>='2023-01-01')&(D.index<='2025-12-31'); idx=D.index[TEST]; y=D.y.values[TEST]
    ok=np.isfinite(y)
    for m in ORDER:
        f=S[tkr][m].reindex(idx).values
        main.append(dict(asset=tkr, model=m, MAE=mae_vol(y[ok],f[ok]), RMSE=rmse_vol(y[ok],f[ok]), QLIKE=qlike(y[ok],f[ok]).mean()))
    F={k:S[tkr][v].reindex(idx).values[ok] for k,v in LAD.items()}
    yy=y[ok]
    for lab,a,b in [('Δ_HF  (L1→L2)','L1','L2'),('Δ_info (L2→L3)','L2','L3'),('Δ_arch (L3→L4)','L3','L4')]:
        d=qlike(yy,F[a])-qlike(yy,F[b]); lo,hi=boot_ci(d); _,p=dm_hln(yy,F[b],F[a],qlike)
        dec.append(dict(asset=tkr, step=lab, delta=d.mean(), ci_lo=lo, ci_hi=hi, dm_p=p))
    for a,b in [('L4 Transformer','L3 HAR-GK-X (full)'),('L4 Transformer','L1 GJR-GARCH'),('L3 HAR-GK-X (full)','L2 HAR-GK'),('L2 HAR-GK','L1 GJR-GARCH')]:
        fa,fb=S[tkr][a].reindex(idx).values[ok],S[tkr][b].reindex(idx).values[ok]
        _,p=dm_hln(yy,fa,fb,qlike)
        dm.append(dict(asset=tkr, model=a, vs=b, dQLIKE=qlike(yy,fa).mean()-qlike(yy,fb).mean(), DM_p=p))
    cw=clark_west(yy, S[tkr]['L2 HAR-GK'].reindex(idx).values[ok], S[tkr]['L3 HAR-GK-X (full)'].reindex(idx).values[ok])
    dec.append(dict(asset=tkr, step='Clark-West (L2→L3)', delta=cw[0], ci_lo=np.nan, ci_hi=np.nan, dm_p=cw[1]))
    LM=pd.DataFrame({m: qlike(yy, S[tkr][m].reindex(idx).values[ok]) for m in ORDER})
    mcsres[tkr]=mcs(LM)[0]
M=pd.DataFrame(main); DEC=pd.DataFrame(dec); DM=pd.DataFrame(dm)
M.to_csv('res_asset2_main.csv',index=False); DEC.to_csv('res_asset2_decomp.csv',index=False); DM.to_csv('res_asset2_dm.csv',index=False)
json.dump({k:v for k,v in mcsres.items()}, open('res_asset2_mcs.json','w'), ensure_ascii=False)
pickle.dump(S, open('pred_asset2_all.pkl','wb'))
pd.set_option('display.width',200)
print(M.pivot(index='model',columns='asset',values=['RMSE','QLIKE']).round(4).to_string())
print('\n', DEC.round(4).to_string(index=False))
print('\n', DM.round(4).to_string(index=False))
print('\nMCS(QLIKE, 90%):', {k: len(v) for k,v in mcsres.items()}, mcsres)
