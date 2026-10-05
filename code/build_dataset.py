import pandas as pd, numpy as np
D=pd.read_parquet('daily.parquet')            # SPY 1-min derived daily features + targets
X=pd.read_parquet('data/exog_raw.parquet')
X=X.reindex(X.index.union(D.index)).sort_index()
X[['VIX','VIX9D','VIX3M','DGS10','DGS3MO','DTWEXBGS','QQQ','TLT','GLD']]=X[['VIX','VIX9D','VIX3M','DGS10','DGS3MO','DTWEXBGS','QQQ','TLT','GLD']].ffill(limit=5)
X=X.reindex(D.index)
F=pd.DataFrame(index=D.index)
# G1 historical realized variance (HAR)
F['lrv_d']=D.lrv_d; F['lrv_w']=D.lrv_w; F['lrv_m']=D.lrv_m
# G2 downside / jump
F['lrs_neg']=D.lrs_neg; F['jump']=D.jump
# G3 option-implied (same-day close, known at 16:15 ET)
F['lvix']=2*np.log(X.VIX/100)
F['vix_slope']=np.log(X.VIX9D/X.VIX)
# G4 returns
F['r_cc']=D.r_cc; F['r_on']=D.r_on; F['r_w']=D.r_w; F['r_m']=D.r_m
# G5 rates (FRED H.15 published after the close -> use previous trading day)
F['d_y10']=X.DGS10.diff().shift(1)
F['term']=(X.DGS10-X.DGS3MO).shift(1)
# G6 dollar and cross-asset (dollar index is FRED -> lagged; ETFs are close-to-close, same day)
F['r_dxy']=(np.log(X.DTWEXBGS).diff()*100).shift(1)
for t in ['QQQ','TLT','GLD']: F['r_'+t.lower()]=np.log(X[t]).diff()*100
# G7 volume
F['vol_rel']=D.vol_rel
GROUPS={'G1 歷史已實現變異':['lrv_d','lrv_w','lrv_m'],'G2 下跌與跳躍':['lrs_neg','jump'],
 'G3 選擇權前瞻':['lvix','vix_slope'],'G4 報酬':['r_cc','r_on','r_w','r_m'],
 'G5 利率':['d_y10','term'],'G6 美元與跨資產':['r_dxy','r_qqq','r_tlt','r_gld'],'G7 交易量':['vol_rel']}
FEATS=[c for g in GROUPS.values() for c in g]
out=F[FEATS].join(D[['y_hf','y_cc','ret_pct']])
out=out.loc['2011-01-04':]
print('rows before dropna', len(out), '\nNaN counts:\n', out.isna().sum()[lambda s:s>0])
out=out.dropna(subset=FEATS)
out.to_parquet('analysis_daily.parquet')
import json; json.dump(GROUPS, open('groups.json','w'), ensure_ascii=False)
print(out.shape, out.index.min().date(), out.index.max().date())
print(out[FEATS].describe().T[['mean','std','min','max']].round(3))
for a,b,n in [('2011-01-04','2020-12-31','train'),('2021-01-01','2022-12-31','val'),('2023-01-01','2025-12-31','test'),('2026-01-01','2026-12-31','holdout')]:
    m=(out.index>=a)&(out.index<=b); print(n, m.sum())
