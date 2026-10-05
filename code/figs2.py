import pickle, json, numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from evaluate import *
plt.rcParams.update({'font.family': 'Microsoft JhengHei', 'axes.unicode_minus': False, 'font.size': 10,
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': '#8a8984', 'axes.labelcolor': '#52514e',
    'xtick.color': '#52514e', 'ytick.color': '#52514e', 'axes.grid': True, 'grid.color': '#e6e5e0',
    'grid.linewidth': 0.6, 'figure.dpi': 150, 'savefig.bbox': 'tight', 'legend.frameon': False})
C = dict(l0='#8a8984', l1='#eb6834', l2='#eda100', l3='#1baf7a', l4='#2a78d6', act='#0b0b0b', vio='#4a3aa7')
D = pd.read_parquet('analysis_daily.parquet')
P = pickle.load(open('pred_all.pkl', 'rb'))
TEST = (D.index >= '2023-01-01') & (D.index <= '2025-12-31'); idx = D.index[TEST]; y = D.y_hf.values[TEST]
LVL = {'L0 Naive': 'l0', 'L1 GARCH(1,1)': 'l1', 'L1 GJR-GARCH': 'l1', 'L2 HAR-RV': 'l2', 'L2 SHAR': 'l2',
       'L3 HAR-RV-X (opt only)': 'l3', 'L3 HAR-RV-X (full)': 'l3', 'L3 SHAR-X': 'l3', 'L3 GARCH-X': 'l3', 'L4 Transformer': 'l4'}
ORDER = list(LVL)

# F1: ladder
q = {m: qlike(y, P[('y_hf', m)].reindex(idx).values).mean() for m in ORDER}
r = {m: rmse_vol(y, P[('y_hf', m)].reindex(idx).values) for m in ORDER}
fig, axs = plt.subplots(1, 2, figsize=(12, 4.2))
for ax, vals, t in [(axs[0], q, 'QLIKE'), (axs[1], r, 'RMSE（年化百分點）')]:
    ax.bar(range(len(ORDER)), [vals[m] for m in ORDER], color=[C[LVL[m]] for m in ORDER], width=0.7)
    ax.set_xticks(range(len(ORDER))); ax.set_xticklabels(ORDER, rotation=35, ha='right', fontsize=8.5)
    ax.set_title(f'測試期 {t}（越低越好）', loc='left', fontsize=10.5); ax.grid(axis='x', visible=False)
    best = min(vals, key=vals.get)
    ax.annotate('最佳', (ORDER.index(best), vals[best]), textcoords='offset points', xytext=(0, 4), ha='center', fontsize=8.5, color='#52514e')
from matplotlib.patches import Patch
axs[0].legend(handles=[Patch(color=C[k], label=l) for k, l in [('l0', 'L0 天真'), ('l1', 'L1 GARCH 類'), ('l2', 'L2 高頻 HAR'), ('l3', 'L3 多變量'), ('l4', 'L4 Transformer')]], fontsize=8.5, ncol=2)
fig.tight_layout(); fig.savefig('fig/r1_ladder.png'); plt.close()

# F2: decomposition forest
d1 = pd.read_csv('res_decomp_y_hf.csv'); d1 = d1[d1.loss == 'QLIKE'].head(3)
d2 = pd.read_csv('res_decomp_shar.csv')
fig, ax = plt.subplots(figsize=(8.5, 3.6))
labs, xs, los, his, cols = [], [], [], [], []
for _, row in d1.iterrows():
    labs.append(row.step.replace('L2', 'HAR-RV').replace('L3', 'HAR-RV-X')); xs.append(row.delta); los.append(row.ci_lo); his.append(row.ci_hi); cols.append(C['l4'])
for _, row in d2.iterrows():
    labs.append(row.step); xs.append(row.delta); los.append(row.ci_lo); his.append(row.ci_hi); cols.append(C['l3'])
ypos = np.arange(len(labs))[::-1]
ax.errorbar(xs, ypos, xerr=[np.array(xs) - np.array(los), np.array(his) - np.array(xs)], fmt='o', ms=7, capsize=4, lw=2, ecolor='#8a8984', mfc=None, ls='none')
for i, (x, yy, c) in enumerate(zip(xs, ypos, cols)):
    ax.plot(x, yy, 'o' if i < 3 else 's', ms=8, color=c)
ax.axvline(0, color='#0b0b0b', lw=1)
ax.set_yticks(ypos); ax.set_yticklabels(labs, fontsize=9)
ax.set_xlabel('QLIKE 改善（>0 表示上一層較佳；90% 區塊拔靴法信賴區間）')
ax.set_title('資訊與架構的損失分解（目標 A）', loc='left', fontsize=11)
ax.text(0.02, 0.06, '藍＝主要設定（HAR 系列）　綠＝SHAR 穩健性檢查', transform=ax.transAxes, fontsize=8.5, color='#52514e')
ax.grid(axis='y', visible=False)
fig.tight_layout(); fig.savefig('fig/r2_decomp.png'); plt.close()

# F3: predictions
fig, axs = plt.subplots(2, 1, figsize=(10, 6))
for ax, (a, b) in zip(axs, [('2023-01-01', '2025-12-31'), ('2025-02-15', '2025-06-30')]):
    mk = (idx >= a) & (idx <= b)
    ax.plot(idx[mk], y[mk] * 100, color=C['act'], lw=1.6, label='實際')
    for m, c in [('L1 GJR-GARCH', C['l1']), ('L3 HAR-RV-X (full)', C['l3']), ('L4 Transformer', C['l4'])]:
        ax.plot(idx[mk], P[('y_hf', m)].reindex(idx).values[mk] * 100, color=c, lw=1.5, label=m)
    ax.set_ylabel('年化波動率 (%)')
axs[0].set_title('測試期預測 vs 實際（未來 5 日已實現波動）', loc='left', fontsize=11)
axs[1].set_title('放大：2025 年 4 月關稅衝擊', loc='left', fontsize=10)
axs[0].legend(fontsize=8.5, ncol=4, loc='upper left')
fig.tight_layout(); fig.savefig('fig/r3_pred.png'); plt.close()

# F4: regimes
R = pd.read_csv('res_regime.csv')
mods = ['L1 GJR-GARCH', 'L2 HAR-RV', 'L3 HAR-RV-X (full)', 'L4 Transformer']
regs = list(R.regime.unique()); w = 0.2
fig, ax = plt.subplots(figsize=(10, 3.8))
for i, m in enumerate(mods):
    v = [R[(R.regime == g) & (R.model == m)].QLIKE.values[0] for g in regs]
    ax.bar(np.arange(len(regs)) + (i - 1.5) * w, v, w * 0.9, color=[C['l1'], C['l2'], C['l3'], C['l4']][i], label=m)
ax.set_xticks(range(len(regs)))
ax.set_xticklabels([f'{g}\n(n={R[R.regime==g].n.iloc[0]})' for g in regs], fontsize=8.5)
ax.set_ylabel('QLIKE'); ax.set_title('不同市場情境的 QLIKE（目標 A）', loc='left', fontsize=11)
ax.legend(fontsize=8.5, ncol=2); ax.grid(axis='x', visible=False)
fig.tight_layout(); fig.savefig('fig/r4_regime.png'); plt.close()

# F5: volatility-targeted portfolio
ret = D.ret_pct.values[TEST]
fig, axs = plt.subplots(1, 2, figsize=(11.5, 3.8), gridspec_kw=dict(width_ratios=[2, 1]))
S = pd.read_csv('res_voltarget.csv'); S5 = S[(S.cost_bps == 5) | (S.model == '買進持有 SPY')].set_index('model')
for m, c in [('L1 GJR-GARCH', C['l1']), ('L2 HAR-RV', C['l2']), ('L3 HAR-RV-X (full)', C['l3']), ('L4 Transformer', C['l4'])]:
    net = vol_target(idx, P[('y_hf', m)].reindex(idx).values, ret, cost_bps=5.0)['net']
    axs[0].plot(idx, np.cumprod(1 + net), color=c, lw=1.8, label=f'{m}（Sharpe {S5.loc[m, "sharpe"]:.2f}）')
axs[0].plot(idx, np.cumprod(1 + ret / 100), color=C['act'], lw=1.5, ls='--', label=f'買進持有（Sharpe {S5.loc["買進持有 SPY", "sharpe"]:.2f}）')
axs[0].set_ylabel('累積淨值'); axs[0].legend(fontsize=8.5)
axs[0].set_title('波動率目標化投組（目標 10%、成本 5bp）', loc='left', fontsize=10.5)
V = pd.read_csv('res_var.csv'); V5 = V[V.alpha == 0.05]
mm = [m for m in ORDER if m in set(V5.model)]
axs[1].bar(range(len(mm)), [V5[V5.model == m].rate.values[0] * 100 for m in mm], color=[C[LVL[m]] for m in mm], width=0.7)
axs[1].axhline(5, color=C['vio'], lw=1.5, ls='--'); axs[1].text(0.5, 5.15, '理論 5%', fontsize=8.5, color=C['vio'])
axs[1].set_xticks(range(len(mm))); axs[1].set_xticklabels(mm, rotation=40, ha='right', fontsize=7.5)
axs[1].set_ylabel('VaR 違反率 (%)'); axs[1].set_title('5% VaR 違反率（5 日非重疊）', loc='left', fontsize=10.5)
axs[1].grid(axis='x', visible=False)
fig.tight_layout(); fig.savefig('fig/r5_econ.png'); plt.close()

# F6: SHAP vs Granger
res = json.load(open('res_shap_granger.json', encoding='utf-8'))
M = pd.DataFrame(res['group_table'])
fig, axs = plt.subplots(1, 2, figsize=(11.5, 3.9))
o = M.sort_values('share')
axs[0].barh(o.group, o.share * 100, color=C['l4'], height=0.6, xerr=o.shap_sd / M.shap_mean.sum() * 100,
            capsize=3, error_kw=dict(ecolor='#52514e', lw=1))
axs[0].set_xlabel('群組 |SHAP| 占比 (%)'); axs[0].set_title('Transformer 群組重要性（5 種子）', loc='left', fontsize=10.5)
axs[0].grid(axis='y', visible=False)
axs[1].scatter(M.wald_h5, M.shap_mean, s=70, color=C['l3'])
for _, row in M.iterrows():
    axs[1].annotate(row.group, (row.wald_h5, row.shap_mean), textcoords='offset points', xytext=(6, 4), fontsize=8)
axs[1].set_xscale('log'); axs[1].set_xlabel('Granger Wald 統計量（訓練樣本，對數刻度）'); axs[1].set_ylabel('平均 |SHAP|')
axs[1].set_title(f'Granger vs SHAP（Spearman ρ={res["spearman"]:.2f}，置換檢定 p={res["p_permutation"]:.3f}）', loc='left', fontsize=10.5)
fig.tight_layout(); fig.savefig('fig/r6_shap_granger.png'); plt.close()
print('figures done')
