import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'Microsoft JhengHei','axes.unicode_minus':False,'font.size':10,
 'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#8a8984','axes.labelcolor':'#52514e',
 'xtick.color':'#52514e','ytick.color':'#52514e','axes.grid':True,'grid.color':'#e6e5e0','grid.linewidth':0.6,
 'figure.dpi':150,'savefig.bbox':'tight','legend.frameon':False})
C=dict(qqq='#2a78d6', spy='#eb6834')
M=pd.read_csv('res_asset2_main.csv'); DEC=pd.read_csv('res_asset2_decomp.csv')
ORDER=['L0 Naive','L1 GARCH(1,1)','L1 GJR-GARCH','L2 HAR-GK','L3 HAR-GK-X (opt only)','L3 HAR-GK-X (full)','L4 Transformer']
fig,axs=plt.subplots(1,2,figsize=(12,4.0))
w=0.38
for i,(a,c) in enumerate([('QQQ',C['qqq']),('SPY',C['spy'])]):
    v=[M[(M.asset==a)&(M.model==m)].QLIKE.values[0] for m in ORDER]
    axs[0].bar(np.arange(len(ORDER))+(i-0.5)*w, v, w*0.9, color=c, label=a)
axs[0].set_xticks(range(len(ORDER))); axs[0].set_xticklabels(ORDER, rotation=32, ha='right', fontsize=8.5)
axs[0].set_ylabel('QLIKE'); axs[0].legend(fontsize=9); axs[0].grid(axis='x',visible=False)
axs[0].set_title('兩個標的的測試期 QLIKE（日頻資訊集）', loc='left', fontsize=10.5)
D=DEC[DEC.step.str.startswith('Δ')]
steps=['Δ_HF  (L1→L2)','Δ_info (L2→L3)','Δ_arch (L3→L4)']
for i,(a,c) in enumerate([('QQQ',C['qqq']),('SPY',C['spy'])]):
    sub=D[D.asset==a].set_index('step').loc[steps]
    ypos=np.arange(len(steps))[::-1]+(0.5-i)*0.22
    axs[1].errorbar(sub.delta, ypos, xerr=[sub.delta-sub.ci_lo, sub.ci_hi-sub.delta], fmt='o', ms=7,
                    color=c, ecolor=c, capsize=4, lw=2, label=a)
axs[1].axvline(0,color='#0b0b0b',lw=1)
axs[1].set_yticks(np.arange(len(steps))[::-1]); axs[1].set_yticklabels(steps, fontsize=9)
axs[1].set_xlabel('QLIKE 改善（>0 表示上一層較佳；90% 信賴區間）'); axs[1].legend(fontsize=9)
axs[1].set_title('損失分解：QQQ vs SPY', loc='left', fontsize=10.5); axs[1].grid(axis='y',visible=False)
fig.tight_layout(); fig.savefig('fig/r7_asset2.png'); plt.close(); print('ok')
