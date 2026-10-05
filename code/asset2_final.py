"""Rebuild the second-asset result tables using the 10-seed ensemble (relative-return specification)."""
import numpy as np, pandas as pd, pickle, json
from evaluate import mse_var, qlike, rmse_vol, mae_vol, dm_hln, clark_west, boot_ci, mcs
P=pickle.load(open('pred_asset2.pkl','rb')); ENS=pickle.load(open('pred_asset2_spec.pkl','rb'))
ORDER=['L0 Naive','L1 GARCH(1,1)','L1 GJR-GARCH','L2 HAR-GK','L3 HAR-GK-X (opt only)','L3 HAR-GK-X (full)','L4 Transformer']
LAD={'L1':'L1 GJR-GARCH','L2':'L2 HAR-GK','L3':'L3 HAR-GK-X (full)'}
main=[]; dec=[]; dm=[]; mcsr={}
for tkr in ['QQQ','SPY']:
    D=pd.read_parquet(f'daily_{tkr}.parquet')
    m=(D.index>='2023-01-01')&(D.index<='2025-12-31'); ix=D.index[m]
    y=D.y.values[m]; ok=np.isfinite(y); yy=y[ok]
    P[tkr]['L4 Transformer']=ENS[(tkr,'rel')]
    for mod in ORDER:
        f=P[tkr][mod].reindex(ix).values[ok]
        main.append(dict(asset=tkr, model=mod, MAE=mae_vol(yy,f), RMSE=rmse_vol(yy,f), QLIKE=qlike(yy,f).mean()))
    F={k:P[tkr][v].reindex(ix).values[ok] for k,v in LAD.items()}; F['L4']=ENS[(tkr,'rel')].values[ok]
    for lab,a,b in [('Δ_HF  (L1→L2)','L1','L2'),('Δ_info (L2→L3)','L2','L3'),('Δ_arch (L3→L4)','L3','L4')]:
        d=qlike(yy,F[a])-qlike(yy,F[b]); lo,hi=boot_ci(d); _,p=dm_hln(yy,F[b],F[a],qlike)
        dec.append(dict(asset=tkr, step=lab, delta=d.mean(), ci_lo=lo, ci_hi=hi, dm_p=p))
    cw=clark_west(yy, F['L2'], F['L3'])
    dec.append(dict(asset=tkr, step='Clark-West (L2→L3)', delta=cw[0], ci_lo=np.nan, ci_hi=np.nan, dm_p=cw[1]))
    for a,b in [('L4 Transformer','L3 HAR-GK-X (full)'),('L4 Transformer','L1 GJR-GARCH'),('L3 HAR-GK-X (full)','L2 HAR-GK'),('L2 HAR-GK','L1 GJR-GARCH')]:
        fa,fb=P[tkr][a].reindex(ix).values[ok],P[tkr][b].reindex(ix).values[ok]
        _,p=dm_hln(yy,fa,fb,qlike)
        dm.append(dict(asset=tkr, model=a, vs=b, dQLIKE=qlike(yy,fa).mean()-qlike(yy,fb).mean(), DM_p=p))
    LM=pd.DataFrame({mod: qlike(yy, P[tkr][mod].reindex(ix).values[ok]) for mod in ORDER})
    mcsr[tkr]=mcs(LM)[0]
pd.DataFrame(main).to_csv('res_asset2_main.csv',index=False)
pd.DataFrame(dec).to_csv('res_asset2_decomp.csv',index=False)
pd.DataFrame(dm).to_csv('res_asset2_dm.csv',index=False)
json.dump(mcsr, open('res_asset2_mcs.json','w'), ensure_ascii=False)
pickle.dump(P, open('pred_asset2_all.pkl','wb'))
pd.set_option('display.width',200)
print(pd.DataFrame(main).pivot(index='model',columns='asset',values=['RMSE','QLIKE']).round(4).to_string())
print('\n', pd.DataFrame(dec).round(4).to_string(index=False))
print('\nMCS:', {k:len(v) for k,v in mcsr.items()})
