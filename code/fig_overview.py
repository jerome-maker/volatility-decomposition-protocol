"""Figure 1: the realized volatility series and the sample split (English, current design)."""
import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'Times New Roman','axes.unicode_minus':False,'font.size':10,
 'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#8a8984','axes.labelcolor':'#333333',
 'xtick.color':'#333333','ytick.color':'#333333','axes.grid':True,'grid.color':'#e6e5e0','grid.linewidth':0.6,
 'figure.dpi':300,'savefig.bbox':'tight','savefig.dpi':300,'legend.frameon':False})
D=pd.read_parquet('analysis_daily.parquet')
fig,ax=plt.subplots(figsize=(9,3.2))
ax.plot(D.index, np.exp(0.5*D.lrv_m)*100, color='#2a78d6', lw=1.1)
bands=[('2011-01-04','2020-12-31','Estimation','#dbe8f8'),('2021-01-01','2022-12-31','Validation','#fde3d6'),
       ('2023-01-01','2025-12-31','Evaluation','#d6f1e6'),('2026-01-01','2026-09-14','Hold-out','#ece3f7')]
ymax=float(np.nanmax(np.exp(0.5*D.lrv_m)*100))*1.12
for a,b,lab,c in bands:
    ax.axvspan(pd.Timestamp(a),pd.Timestamp(b),color=c,zorder=0,lw=0)
    ax.text(pd.Timestamp(a)+(pd.Timestamp(b)-pd.Timestamp(a))/2, ymax*0.93, lab, ha='center', fontsize=9, color='#333333')
ax.set_ylim(0,ymax); ax.set_ylabel('Annualized volatility (%)')
ax.set_title('SPY 22-day realized volatility and the sample split', loc='left', fontsize=11)
fig.savefig('fig/f1_overview.png'); print('fig/f1_overview.png written')
