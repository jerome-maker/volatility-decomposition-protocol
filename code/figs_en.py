"""Regenerate every figure with English labelling, in the manuscript's typeface."""
import pickle, json, numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from evaluate import qlike, rmse_vol, vol_target

plt.rcParams.update({'font.family': 'Times New Roman', 'mathtext.fontset': 'stix',
    'axes.unicode_minus': False, 'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False,
    'axes.edgecolor': '#8a8984', 'axes.labelcolor': '#333333', 'xtick.color': '#333333', 'ytick.color': '#333333',
    'axes.grid': True, 'grid.color': '#e6e5e0', 'grid.linewidth': 0.6, 'figure.dpi': 200,
    'savefig.bbox': 'tight', 'legend.frameon': False})
C = dict(l0='#8a8984', l1='#eb6834', l2='#eda100', l3='#1baf7a', l4='#2a78d6', act='#0b0b0b',
         vio='#4a3aa7', qqq='#2a78d6', spy='#eb6834')

D = pd.read_parquet('analysis_daily.parquet')
P = pickle.load(open('pred_all.pkl', 'rb'))
TEST = (D.index >= '2023-01-01') & (D.index <= '2025-12-31'); idx = D.index[TEST]; y = D.y_hf.values[TEST]
LVL = {'L0 Naive': 'l0', 'L1 GARCH(1,1)': 'l1', 'L1 GJR-GARCH': 'l1', 'L2 HAR-RV': 'l2', 'L2 SHAR': 'l2',
       'L3 HAR-RV-X (opt only)': 'l3', 'L3 HAR-RV-X (full)': 'l3', 'L3 SHAR-X': 'l3', 'L3 GARCH-X': 'l3',
       'L4 Transformer': 'l4', 'L4 LSTM': 'l4'}
SHORT = {'L0 Naive': 'Random walk', 'L1 GARCH(1,1)': 'GARCH(1,1)', 'L1 GJR-GARCH': 'GJR-GARCH',
         'L2 HAR-RV': 'HAR-RV', 'L2 SHAR': 'SHAR', 'L3 HAR-RV-X (opt only)': 'HAR-RV-X (option)',
         'L3 HAR-RV-X (full)': 'HAR-RV-X', 'L3 SHAR-X': 'SHAR-X', 'L3 GARCH-X': 'GARCH-X',
         'L4 Transformer': 'Transformer', 'L4 LSTM': 'LSTM'}
REG = {'全部': 'All', '低 VIX（下三分位）': 'Low VIX', '高 VIX（上三分位）': 'High VIX',
       '高波動日（實際前20%）': 'Top 20% realized', '2025/3-5 關稅衝擊': 'Mar–May 2025'}
GRP = {'G1 歷史已實現變異': 'G1 Realized variance', 'G2 下跌與跳躍': 'G2 Downside & jumps',
       'G3 選擇權前瞻': 'G3 Option-implied', 'G4 報酬': 'G4 Returns', 'G5 利率': 'G5 Interest rates',
       'G6 美元與跨資產': 'G6 Dollar & cross-asset', 'G7 交易量': 'G7 Trading activity'}
ORDER = ['L0 Naive', 'L1 GARCH(1,1)', 'L1 GJR-GARCH', 'L2 HAR-RV', 'L3 HAR-RV-X (opt only)',
         'L3 HAR-RV-X (full)', 'L3 GARCH-X', 'L4 Transformer']

# ---- Figure 2: the ladder
q = {m: qlike(y, P[('y_hf', m)].reindex(idx).values).mean() for m in ORDER}
r = {m: rmse_vol(y, P[('y_hf', m)].reindex(idx).values) for m in ORDER}
fig, axs = plt.subplots(1, 2, figsize=(11, 3.8))
for ax, vals, t in [(axs[0], q, 'QLIKE'), (axs[1], r, 'RMSE (annualized percentage points)')]:
    ax.bar(range(len(ORDER)), [vals[m] for m in ORDER], color=[C[LVL[m]] for m in ORDER], width=0.7)
    ax.set_xticks(range(len(ORDER))); ax.set_xticklabels([SHORT[m] for m in ORDER], rotation=35, ha='right', fontsize=8.5)
    ax.set_title(f'Out-of-sample {t}, lower is better', loc='left', fontsize=10.5); ax.grid(axis='x', visible=False)
    best = min(vals, key=vals.get)
    ax.annotate('best', (ORDER.index(best), vals[best]), textcoords='offset points', xytext=(0, 4), ha='center', fontsize=8.5)
axs[0].legend(handles=[Patch(color=C[k], label=l) for k, l in
                       [('l0', 'Level 0'), ('l1', 'Level 1'), ('l2', 'Level 2'), ('l3', 'Level 3'), ('l4', 'Level 4')]],
              fontsize=8.5, ncol=2)
fig.tight_layout(); fig.savefig('fig/r1_ladder.png'); plt.close()

# ---- Figure 3: decomposition
d1 = pd.read_csv('res_decomp_y_hf.csv'); d1 = d1[d1.loss == 'QLIKE'].head(3)
d2 = pd.read_csv('res_decomp_shar.csv')
lab_map = {'Δ_HF  (L1→L2)': r'$\Delta_{HF}$  (L1$\rightarrow$L2)', 'Δ_info (L2→L3)': r'$\Delta_{info}$  (L2$\rightarrow$L3)',
           'Δ_arch (L3→L4)': r'$\Delta_{arch}$  (L3$\rightarrow$L4)', 'Δ_HF  (L1→L2 SHAR)': r'$\Delta_{HF}$  (SHAR)',
           'Δ_info (L2→L3 SHAR-X)': r'$\Delta_{info}$  (SHAR-X)', 'Δ_arch (L3→L4)*': r'$\Delta_{arch}$  (SHAR-X)'}
rows = [(lab_map.get(x.step, x.step), x.delta, x.ci_lo, x.ci_hi, C['l4'], 'o') for _, x in d1.iterrows()]
shar_lab = [r'$\Delta_{HF}$  (SHAR)', r'$\Delta_{info}$  (SHAR-X)', r'$\Delta_{arch}$  (SHAR-X)']
rows += [(shar_lab[i], x.delta, x.ci_lo, x.ci_hi, C['l3'], 's') for i, (_, x) in enumerate(d2.iterrows())]
fig, ax = plt.subplots(figsize=(8.4, 3.5))
ypos = np.arange(len(rows))[::-1]
for (lab, v, lo, hi, col, mk), yp in zip(rows, ypos):
    ax.plot([lo, hi], [yp, yp], color='#8a8984', lw=2, zorder=2)
    ax.plot([lo, lo, np.nan, hi, hi], [yp - .12, yp + .12, np.nan, yp - .12, yp + .12], color='#8a8984', lw=1.4)
    ax.plot(v, yp, mk, ms=8, color=col, zorder=3)
ax.axvline(0, color='#0b0b0b', lw=1)
ax.set_yticks(ypos); ax.set_yticklabels([r[0] for r in rows], fontsize=9.5)
ax.set_xlabel('QLIKE improvement (positive favours the higher level); 90% block bootstrap interval')
ax.set_title('Decomposition of the out-of-sample gain', loc='left', fontsize=11)
from matplotlib.lines import Line2D
ax.legend(handles=[Line2D([], [], marker='o', ls='none', color=C['l4'], ms=8, label='Main specification'),
                   Line2D([], [], marker='s', ls='none', color=C['l3'], ms=8, label='SHAR robustness')],
          fontsize=9, loc='lower right', bbox_to_anchor=(1.0, -0.04))
ax.set_ylim(-0.8, len(rows) - 0.2)
ax.grid(axis='y', visible=False)
fig.tight_layout(); fig.savefig('fig/r2_decomp.png'); plt.close()

# ---- Figure 4: forecast paths
fig, axs = plt.subplots(2, 1, figsize=(10, 6))
for ax, (a, b, ttl) in zip(axs, [('2023-01-01', '2025-12-31', 'Forecasts and realized volatility, 2023–2025'),
                                 ('2025-02-15', '2025-06-30', 'Detail: the April 2025 episode')]):
    mk = (idx >= a) & (idx <= b)
    ax.plot(idx[mk], y[mk] * 100, color=C['act'], lw=1.6, label='Realized (next five days)')
    for m, c in [('L1 GJR-GARCH', C['l1']), ('L3 HAR-RV-X (full)', C['l3']), ('L4 Transformer', C['l4'])]:
        ax.plot(idx[mk], P[('y_hf', m)].reindex(idx).values[mk] * 100, color=c, lw=1.5, label=SHORT[m])
    ax.set_ylabel('Annualized volatility (%)'); ax.set_title(ttl, loc='left', fontsize=10.5)
axs[0].legend(fontsize=8.5, ncol=4, loc='upper left')
fig.tight_layout(); fig.savefig('fig/r3_pred.png'); plt.close()

# ---- Figure 5: market conditions
R = pd.read_csv('res_regime.csv'); R['regime'] = R.regime.map(REG).fillna(R.regime)
mods = ['L1 GJR-GARCH', 'L2 HAR-RV', 'L3 HAR-RV-X (full)', 'L4 Transformer']
regs = [REG[k] for k in ['全部', '低 VIX（下三分位）', '高 VIX（上三分位）', '高波動日（實際前20%）', '2025/3-5 關稅衝擊']]
fig, ax = plt.subplots(figsize=(9.6, 3.6)); w = 0.2
for i, m in enumerate(mods):
    v = [R[(R.regime == g) & (R.model == m)].QLIKE.values[0] for g in regs]
    ax.bar(np.arange(len(regs)) + (i - 1.5) * w, v, w * 0.9, color=[C['l1'], C['l2'], C['l3'], C['l4']][i], label=SHORT[m])
ax.set_xticks(range(len(regs)))
ax.set_xticklabels([f'{g}\n(n={R[R.regime==g].n.iloc[0]})' for g in regs], fontsize=9)
ax.set_ylabel('QLIKE'); ax.set_title('QLIKE by market condition', loc='left', fontsize=11)
ax.legend(fontsize=8.5, ncol=2); ax.grid(axis='x', visible=False)
fig.tight_layout(); fig.savefig('fig/r4_regime.png'); plt.close()

# ---- Figure 6: economic value
ret = D.ret_pct.values[TEST]
S = pd.read_csv('res_voltarget10.csv'); V = pd.read_csv('res_var10.csv'); V5 = V[V.alpha == 0.05]
S5 = S[(S.cost_bps == 5) | (S.model == 'Buy and hold')].set_index('model')
fig, axs = plt.subplots(1, 2, figsize=(11.5, 3.7), gridspec_kw=dict(width_ratios=[2, 1]))
for m, c in [('L1 GJR-GARCH', C['l1']), ('L2 HAR-RV', C['l2']), ('L3 HAR-RV-X (full)', C['l3']), ('L4 Transformer', C['l4'])]:
    net = vol_target(idx, P[('y_hf', m)].reindex(idx).values, ret, cost_bps=5.0)['net']
    axs[0].plot(idx, np.cumprod(1 + net), color=c, lw=1.7, label=f'{SHORT[m]} (Sharpe {S5.loc[m, "sharpe"]:.2f})')
axs[0].plot(idx, np.cumprod(1 + ret / 100), color=C['act'], lw=1.4, ls='--',
            label=f'Buy and hold (Sharpe {S5.loc["Buy and hold", "sharpe"]:.2f})')
axs[0].set_ylabel('Cumulative net value'); axs[0].legend(fontsize=8.5)
axs[0].set_title('Volatility-targeted portfolios, 10% target, 5 bp cost', loc='left', fontsize=10.5)
mm = [m for m in ORDER if m in set(V5.model)]
axs[1].bar(range(len(mm)), [V5[V5.model == m].rate.values[0] * 100 for m in mm], color=[C[LVL[m]] for m in mm], width=0.7)
axs[1].axhline(5, color=C['vio'], lw=1.4, ls='--'); axs[1].text(0.4, 5.12, 'nominal 5%', fontsize=8.5, color=C['vio'])
axs[1].set_xticks(range(len(mm))); axs[1].set_xticklabels([SHORT[m] for m in mm], rotation=40, ha='right', fontsize=8)
axs[1].set_ylabel('Violation rate (%)'); axs[1].set_title('5% value-at-risk, five-day blocks', loc='left', fontsize=10.5)
axs[1].grid(axis='x', visible=False)
fig.tight_layout(); fig.savefig('fig/r5_econ.png'); plt.close()

# ---- Figure 7: second application
A2 = pd.read_csv('res_asset2_main.csv'); DEC2 = pd.read_csv('res_asset2_decomp.csv')
O2 = ['L0 Naive', 'L1 GARCH(1,1)', 'L1 GJR-GARCH', 'L2 HAR-GK', 'L3 HAR-GK-X (opt only)', 'L3 HAR-GK-X (full)', 'L4 Transformer']
S2 = {'L0 Naive': 'Random walk', 'L1 GARCH(1,1)': 'GARCH(1,1)', 'L1 GJR-GARCH': 'GJR-GARCH', 'L2 HAR-GK': 'HAR-GK',
      'L3 HAR-GK-X (opt only)': 'HAR-GK-X (option)', 'L3 HAR-GK-X (full)': 'HAR-GK-X', 'L4 Transformer': 'Transformer'}
fig, axs = plt.subplots(1, 2, figsize=(11.5, 3.8)); w = 0.38
for i, (a, c) in enumerate([('QQQ', C['qqq']), ('SPY', C['spy'])]):
    v = [A2[(A2.asset == a) & (A2.model == m)].QLIKE.values[0] for m in O2]
    axs[0].bar(np.arange(len(O2)) + (i - 0.5) * w, v, w * 0.9, color=c, label=a)
axs[0].set_xticks(range(len(O2))); axs[0].set_xticklabels([S2[m] for m in O2], rotation=32, ha='right', fontsize=8.5)
axs[0].set_ylabel('QLIKE'); axs[0].legend(fontsize=9); axs[0].grid(axis='x', visible=False)
axs[0].set_title('Daily-only information set: QLIKE by level', loc='left', fontsize=10.5)
steps = ['Δ_HF  (L1→L2)', 'Δ_info (L2→L3)', 'Δ_arch (L3→L4)']
nice = [r'$\Delta_{HF}$', r'$\Delta_{info}$', r'$\Delta_{arch}$']
for i, (a, c) in enumerate([('QQQ', C['qqq']), ('SPY', C['spy'])]):
    sub = DEC2[DEC2.asset == a].set_index('step').loc[steps]
    yp = np.arange(len(steps))[::-1] + (0.5 - i) * 0.22
    axs[1].errorbar(sub.delta, yp, xerr=[sub.delta - sub.ci_lo, sub.ci_hi - sub.delta], fmt='o', ms=7,
                    color=c, ecolor=c, capsize=4, lw=2, label=a)
axs[1].axvline(0, color='#0b0b0b', lw=1)
axs[1].set_yticks(np.arange(len(steps))[::-1]); axs[1].set_yticklabels(nice, fontsize=11)
axs[1].set_xlabel('QLIKE improvement; 90% interval'); axs[1].legend(fontsize=9)
axs[1].set_title('Decomposition: QQQ against SPY', loc='left', fontsize=10.5); axs[1].grid(axis='y', visible=False)
fig.tight_layout(); fig.savefig('fig/r7_asset2.png'); plt.close()

# ---- Figure 8: parameterization
SP = pd.read_csv('res_asset2_spec.csv'); SE = pd.read_csv('res_asset2_spec_seeds.csv')
SPi = SP[SP.spec.isin(['rel', 'abs'])].set_index(['asset', 'spec'])
lab = {'rel': 'Relative return (own − other)', 'abs': 'Raw return of the other ETF'}
col = {'rel': C['l4'], 'abs': C['l1']}
fig, ax = plt.subplots(figsize=(8.6, 3.7))
pos = {('QQQ', 'rel'): 0, ('QQQ', 'abs'): 0.8, ('SPY', 'rel'): 2.2, ('SPY', 'abs'): 3.0}
rng = np.random.default_rng(0)
for (a, v), x in pos.items():
    qs = SE[(SE.asset == a) & (SE.spec == v)].QLIKE.values
    ax.scatter(np.full_like(qs, x) + rng.normal(0, 0.05, len(qs)), qs, s=36, color=col[v], alpha=0.75,
               label=lab[v] if a == 'QQQ' else None, zorder=3)
    ax.hlines(qs.mean(), x - 0.28, x + 0.28, color=col[v], lw=2.4, zorder=4)
    ax.scatter([x], [SPi.loc[(a, v), 'ens_QLIKE']], marker='D', s=66, facecolor='white', edgecolor=col[v], lw=2, zorder=5)
ax.set_xticks([0.4, 2.6]); ax.set_xticklabels(['QQQ', 'SPY'], fontsize=11)
ax.set_ylabel('QLIKE'); ax.grid(axis='x', visible=False)
ax.set_title('Cross-asset parameterization: one point per seed, bar = seed mean, diamond = ten-seed ensemble',
             loc='left', fontsize=10)
ax.legend(fontsize=9, loc='upper right')
fig.tight_layout(); fig.savefig('fig/r8_spec.png'); plt.close()

# ---- Figure 9: attribution against predictive precedence
res = json.load(open('res_shap_granger.json', encoding='utf-8'))
M = pd.DataFrame(res['group_table']); M['grp'] = M.group.map(GRP).fillna(M.group)
fig, axs = plt.subplots(1, 2, figsize=(11.5, 3.8))
o = M.sort_values('share')
axs[0].barh(o.grp, o.share * 100, color=C['l4'], height=0.6,
            xerr=o.shap_sd / M.shap_mean.sum() * 100, capsize=3, error_kw=dict(ecolor='#555555', lw=1))
axs[0].set_xlabel('Share of total attribution (%)')
axs[0].set_title('Attribution by predictor block, ten seeds', loc='left', fontsize=10.5)
axs[0].grid(axis='y', visible=False)
axs[1].scatter(M.wald_h5, M.shap_mean, s=66, color=C['l3'])
for _, row in M.iterrows():
    axs[1].annotate(row.grp.split(' ', 1)[0], (row.wald_h5, row.shap_mean), textcoords='offset points',
                    xytext=(6, 4), fontsize=9)
axs[1].set_xscale('log'); axs[1].set_xlabel('Granger Wald statistic, training sample (log scale)')
axs[1].set_ylabel('Mean |attribution|')
axs[1].set_title(f'Attribution against precedence (Spearman {res["spearman"]:.2f}, permutation p = {res["p_permutation"]:.3f})',
                 loc='left', fontsize=10)
fig.tight_layout(); fig.savefig('fig/r6_shap_granger.png'); plt.close()
print('all figures regenerated in English')
