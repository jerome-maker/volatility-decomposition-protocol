"""Figure: seed-level comparison of the two cross-asset specifications."""
import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'Microsoft JhengHei','axes.unicode_minus':False,'font.size':10,
 'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#8a8984','axes.labelcolor':'#52514e',
 'xtick.color':'#52514e','ytick.color':'#52514e','axes.grid':True,'grid.color':'#e6e5e0','grid.linewidth':0.6,
 'figure.dpi':150,'savefig.bbox':'tight','legend.frameon':False})
S=pd.read_csv('res_asset2_spec_seeds.csv'); R=pd.read_csv('res_asset2_spec.csv')
R=R[R.spec.isin(['rel','abs'])].set_index(['asset','spec'])
lab={'rel':'相對報酬 (QQQ-SPY)','abs':'原始報酬 (另一標的)'}
C={'rel':'#2a78d6','abs':'#eb6834'}
fig,ax=plt.subplots(figsize=(8.6,3.8))
pos={('QQQ','rel'):0,('QQQ','abs'):0.8,('SPY','rel'):2.2,('SPY','abs'):3.0}
for (a,v),x in pos.items():
    q=S[(S.asset==a)&(S.spec==v)].QLIKE.values
    ax.scatter(np.full_like(q,x)+np.random.default_rng(0).normal(0,0.05,len(q)), q, s=38, color=C[v], alpha=0.75,
               label=lab[v] if a=='QQQ' else None, zorder=3)
    ax.hlines(q.mean(), x-0.28, x+0.28, color=C[v], lw=2.5, zorder=4)
    ax.scatter([x],[R.loc[(a,v),'ens_QLIKE']], marker='D', s=70, facecolor='white', edgecolor=C[v], lw=2, zorder=5)
ax.set_xticks([0.4,2.6]); ax.set_xticklabels(['QQQ','SPY'])
ax.set_ylabel('測試期 QLIKE'); ax.grid(axis='x',visible=False)
ax.set_title('兩種跨資產變數設定的比較（每點為一個隨機種子，橫線＝種子平均，菱形＝10 種子集成）',loc='left',fontsize=10)
ax.legend(fontsize=9, loc='upper right')
fig.tight_layout(); fig.savefig('fig/r8_spec.png')
