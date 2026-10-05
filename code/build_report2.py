import pandas as pd, numpy as np, json, pickle
from docx_helpers import *

f2 = lambda x: f'{x:.2f}'; f3 = lambda x: f'{x:.3f}'; f4 = lambda x: f'{x:.4f}'
def pv(p): return '<0.001' if p < 0.001 else f'{p:.3f}'
MA = pd.read_csv('res_main_y_hf.csv', index_col=0); MB = pd.read_csv('res_main_y_cc.csv', index_col=0)
DEC = pd.read_csv('res_decomp_y_hf.csv'); DECB = pd.read_csv('res_decomp_y_cc.csv'); DECS = pd.read_csv('res_decomp_shar.csv')
DM = pd.read_csv('res_dm_y_hf.csv'); CW = pd.read_csv('res_cw_y_hf.csv'); DMB = pd.read_csv('res_dm_y_cc.csv')
RG = pd.read_csv('res_regime.csv'); VAR = pd.read_csv('res_var.csv'); VT = pd.read_csv('res_voltarget.csv')
SH = pd.read_csv('res_shap_groups.csv'); SG = json.load(open('res_shap_granger.json', encoding='utf-8'))
GR = pd.read_csv('granger_groups.csv'); GV = pd.read_csv('granger_vars.csv'); SHR = pd.read_csv('res_shar_main.csv', index_col=0)
L4 = pickle.load(open('l4_final.pkl', 'rb')); runs = [x[1] for x in L4['runs']]
MCSQ = json.load(open('res_mcs_QLIKE.json', encoding='utf-8')); MCSM = json.load(open('res_mcs_MSE.json', encoding='utf-8'))

d = new_doc()
d.add_paragraph().paragraph_format.space_before = Pt(50)
para(d, 'SPY 已實現波動率預測', size=13, align='center')
t = d.add_paragraph(style='Title'); setfont(t.add_run('資訊階梯實證結果報告'), 22, True, '1F3A5F'); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
para(d, '選擇權前瞻資訊、高頻計量與 Transformer 的增量價值，含經濟價值評估與 Granger × SHAP 診斷', size=11.5, align='center')
d.add_paragraph()
table(d, ['項目', '內容'], [
    ['對應計畫', 'SPY 波動率研究計畫（修訂版第 2 版），目標期刊 Journal of Economics and Finance'],
    ['資料期間', '2011-01-04 至 2025-12-31；訓練 2,516 日、驗證 503 日、測試 752 日'],
    ['最終保留樣本', '2026-01 至 2026-09（175 日）依計畫未動用（見 §1.2）'],
    ['預測目標', '未來 5 個交易日年化已實現波動率（主：5 分鐘 RV；穩健性：日報酬 RV）'],
    ['模型階梯', 'L0 天真 → L1 GARCH/GJR → L2 HAR-RV/SHAR → L3 HAR-RV-X/GARCH-X → L4 Transformer'],
    ['估計方式', '擴張視窗，每個測試年度重新估計；Transformer 每年 10 個隨機種子取平均'],
    ['運算環境', 'NVIDIA GTX 1060 3GB（CUDA 12.6、PyTorch 2.13.0）；共 404 次模型訓練'],
    ['報告日期', '2026 年 9 月 21 日'],
], widths=[3.2, 13.4], size=10)
d.add_page_break()

# ---------- summary
d.add_heading('摘要與核心發現', 1)
qi = DEC[(DEC.loss == 'QLIKE')].set_index('step')
para(d, '本報告依修訂版計畫執行四層資訊階梯的完整實證分析，以 2023–2025 年 752 個交易日進行樣本外評估。核心結論如下。')
bullet(d, f'**選擇權前瞻資訊是唯一顯著的貢獻來源。** 在 HAR-RV 之上加入 VIX、VIX9D 期限結構與總體變數後，QLIKE 改善 {f3(qi.loc["Δ_info (L2→L3)", "delta"])}（90% 信賴區間 [{f3(qi.loc["Δ_info (L2→L3)", "ci_lo"])}, {f3(qi.loc["Δ_info (L2→L3)", "ci_hi"])}]，DM 檢定 p={pv(qi.loc["Δ_info (L2→L3)", "dm_p"])}）。')
bullet(d, f'**非線性架構不但沒有增量價值，而且顯著較差。** 在資訊集完全相同的條件下，Transformer 相對線性 HAR-RV-X 的 QLIKE 高出 {f3(-qi.loc["Δ_arch (L3→L4)", "delta"])}（90% 信賴區間 [{f3(qi.loc["Δ_arch (L3→L4)", "ci_lo"])}, {f3(qi.loc["Δ_arch (L3→L4)", "ci_hi"])}]，DM 檢定 p={pv(qi.loc["Δ_arch (L3→L4)", "dm_p"])}）。以 10 個種子集成後，Transformer 也不再顯著優於任何基準模型。這直接回答了計畫的核心研究問題。')
bullet(d, f'**高頻 HAR 未能勝過非對稱 GARCH。** Δ_HF 為 {f3(qi.loc["Δ_HF  (L1→L2)", "delta"])}，即 HAR-RV 的 QLIKE 高於 GJR-GARCH。改用含正負半變異的 SHAR 後差距縮小至 {f3(DECS.iloc[0].delta)}，信賴區間涵蓋 0，顯示缺少非對稱項是部分原因。')
bullet(d, f'**統計最佳不等於經濟最佳。** HAR-RV-X 的 QLIKE 最低，但在波動率目標化投組中 Sharpe 最高的是 GJR-GARCH（{f2(VT[(VT.model=="L1 GJR-GARCH")&(VT.cost_bps==5)].sharpe.iloc[0])} vs {f2(VT[(VT.model=="L3 HAR-RV-X (full)")&(VT.cost_bps==5)].sharpe.iloc[0])}）；VaR 回測中所有模型皆通過且彼此無差別。')
bullet(d, f'**Granger 與 SHAP 在最重要的群組上一致。** 選擇權群組同時是 Granger Wald 統計量最高（{GR[GR.group.str.startswith("G3")].wald_h5.iloc[0]:.0f}）與 SHAP 占比最高（{SH[SH.group.str.startswith("G3")].share.iloc[0]*100:.1f}%）的群組；但整體秩相關 {SG["spearman"]:.2f} 在置換檢定下不顯著（p={SG["p_permutation"]:.3f}），群組數僅 6 個，檢定力有限。')
bullet(d, '**加入 LSTM 對照組後結論不變。** 以相同資訊與相同訓練協定訓練的 LSTM，Δ_arch 在兩個目標上同樣為負，沒有任何深度學習架構勝過線性模型；但 LSTM 顯著優於 Transformer（目標 A，p=0.029），顯示深度學習家族內部的排序並不穩定（§2.6）。')
bullet(d, '**Model Confidence Set 無法分辨模型。** 90% 信賴水準下，QLIKE 僅剔除天真預測，MSE 下無任何模型被剔除，顯示單一標的、三年測試期的檢定力不足。')
figure(d, 'fig/r1_ladder.png', '圖 1　各層模型在測試期的 QLIKE 與 RMSE', width=16.5)

# ---------- data
d.add_heading('一、資料與執行設定', 1)
d.add_heading('1.1 資料', 2)
table(d, ['資料', '來源', '期間', '備註'], [
    ['SPY 1 分鐘 OHLCV', '既有檔案 SPY_clean_1min.csv', '2002-12 – 2026-09', '2022-03-07 起來源改為 IEX；接縫日隔夜報酬設為 0'],
    ['VIX、VIX9D、VIX3M', 'Cboe 官方歷史資料', 'VIX9D 自 2011-01-04', 'VIX9D 起始日決定共同樣本起點'],
    ['10 年期／3 個月公債殖利率', 'FRED（DGS10、DGS3MO）', '—', 'H.15 於收盤後發布，以前一交易日值進入模型'],
    ['廣義美元指數', 'FRED（DTWEXBGS）', '—', '同上，取落後一日'],
    ['QQQ、TLT、GLD', 'Yahoo Finance（yfinance）', '—', '調整後收盤價；下載日期 2026-09-21'],
], widths=[3.4, 4.2, 3.4, 5.6], size=9)
para(d, '合計 18 個候選變數，分為 7 個群組：G1 歷史已實現變異（HAR 三項）、G2 下跌與跳躍、G3 選擇權前瞻、G4 報酬、G5 利率、G6 美元與跨資產、G7 交易量。L2 僅使用 G1；L3 與 L4 使用全部 18 個變數，確保資訊集對等。')
d.add_heading('1.2 樣本切分與估計方式', 2)
table(d, ['用途', '期間', '交易日', '說明'], [
    ['訓練', '2011-01-04 – 2020-12-31', '2,516', '高於前導實驗的 2,000 日穩定門檻'],
    ['驗證', '2021-01-01 – 2022-12-31', '503', '僅用於超參數選擇與提早停止'],
    ['測試', '2023-01-01 – 2025-12-31', '752', '擴張視窗，每年重新估計'],
    ['最終保留', '2026-01-02 – 2026-09-14', '175', '本報告未使用'],
], widths=[2.4, 5.4, 2, 6.8], size=9)
para(d, '擴張視窗：預測第 Y 年時，以 2011 年初至第 Y−1 年底的資料重新估計全部模型；Transformer 以該估計樣本的最後兩年作為提早停止的驗證尾段。訓練樣本末端剔除 5 日，避免目標跨期洩漏。')

# ---------- main results
d.add_page_break()
d.add_heading('二、主要結果', 1)
d.add_heading('2.1 各層模型表現', 2)
rows = []
for m in MA.index:
    rows.append([m, f2(MA.loc[m, 'MAE']), f2(MA.loc[m, 'RMSE']), f4(MA.loc[m, 'QLIKE']),
                 f2(MB.loc[m, 'MAE']), f2(MB.loc[m, 'RMSE']), f4(MB.loc[m, 'QLIKE'])])
best_a = MA.QLIKE.idxmin(); best_b = MB.QLIKE.idxmin()
rows = [[('**' + r[0] + '**') if r[0] in (best_a,) else r[0]] + r[1:] for r in rows]
table(d, ['模型', 'A: MAE', 'A: RMSE', 'A: QLIKE', 'B: MAE', 'B: RMSE', 'B: QLIKE'], rows,
      widths=[4.4, 1.9, 2, 2.2, 1.9, 2, 2.2], size=9, highlight_rows=(list(MA.index).index(best_a),))
caption(d, '表 1　測試期（2023–2025，752 日）模型表現。目標 A＝5 分鐘已實現波動，目標 B＝日報酬已實現波動（計畫書定義）。誤差為年化百分點。')
bullet(d, f'兩種目標的排序完全相同：**L3 HAR-RV-X（全部變數）最佳**，其次為僅加選擇權變數的版本，Transformer 居中，GJR-GARCH 與之接近。')
bullet(d, 'L3 GARCH-X 與 GJR-GARCH 幾乎相同（QLIKE 0.2003 vs 0.1998）：三個估計視窗中，VIX 與 VIX9D 在變異數方程式的係數皆收斂至 0。**前瞻資訊只在 HAR 架構中有效，在 GARCH 變異數方程中被既有的槓桿項吸收。**')

d.add_heading('2.2 核心結果：資訊與架構的分解', 2)
figure(d, 'fig/r2_decomp.png', '圖 2　QLIKE 的損失分解與 90% 區塊拔靴法信賴區間', width=15)
rows = []
for _, r in DEC[DEC.loss == 'QLIKE'].iterrows():
    ci = '—' if not np.isfinite(r.ci_lo) else f'[{f3(r.ci_lo)}, {f3(r.ci_hi)}]'
    rows.append([r.step, f3(r.delta), ci, pv(r.dm_p)])
for _, r in DECS.iterrows():
    rows.append([r.step + '（SHAR 版本）', f3(r.delta), f'[{f3(r.ci_lo)}, {f3(r.ci_hi)}]', pv(r.dm_p)])
table(d, ['成分', 'QLIKE 改善', '90% 信賴區間', 'DM p 值'], rows, widths=[6.4, 3.2, 4, 3], highlight_rows=(1,))
caption(d, '表 2　損失分解（目標 A）。正值代表較高層級較佳。前四列為主要設定，後三列為以 SHAR 取代 HAR-RV 的穩健性檢查。')
para(d, '**三項發現：**')
numbered(d, f'**Δ_info 顯著為正（+{f3(qi.loc["Δ_info (L2→L3)", "delta"])}，p={pv(qi.loc["Δ_info (L2→L3)", "dm_p"])}）。** 選擇權前瞻資訊與總體變數帶來實質改善，是整個階梯中唯一通過顯著性檢定的正向貢獻。以 Clark–West 巢狀檢定亦得到一致結論（CW={CW.iloc[1].CW:.2f}，p={pv(CW.iloc[1].p)}）。')
numbered(d, f'**Δ_arch 為負且不顯著（{f3(qi.loc["Δ_arch (L3→L4)", "delta"])}，p={pv(qi.loc["Δ_arch (L3→L4)", "dm_p"])}）。** 在資訊集對等下，Transformer 不但沒有超越線性模型，點估計方向還略劣。目標 B 的結果一致（{f3(DECB[(DECB.loss=="QLIKE")&(DECB.step.str.startswith("Δ_arch"))].delta.iloc[0])}，p={pv(DECB[(DECB.loss=="QLIKE")&(DECB.step.str.startswith("Δ_arch"))].dm_p.iloc[0])}）。')
numbered(d, f'**Δ_HF 為負。** HAR-RV 的 QLIKE 高於 GJR-GARCH。改用 SHAR 後差距由 {f3(qi.loc["Δ_HF  (L1→L2)", "delta"])} 縮小到 {f3(DECS.iloc[0].delta)}，信賴區間涵蓋 0，代表原始 HAR 缺少非對稱項是主要原因之一，但高頻資訊本身在此測試期並未勝過日頻的非對稱 GARCH。')
para(d, f'四項相加後，Transformer 與 GJR-GARCH 的整體差異僅 {f3(DEC[(DEC.loss=="QLIKE")&(DEC.step.str.startswith("合計"))].delta.iloc[0])}（p={pv(DEC[(DEC.loss=="QLIKE")&(DEC.step.str.startswith("合計"))].dm_p.iloc[0])}），實質上無法區分。')

d.add_heading('2.3 統計檢定', 2)
rows = []
for _, r in DM.iterrows():
    rows.append([f'{r.model} vs {r.vs}', f'{r.dQLIKE:+.4f}', pv(r.DM_QLIKE_p), f'{r.dMSE:+,.0f}', pv(r.DM_MSE_p)])
table(d, ['比較（前者 − 後者）', 'ΔQLIKE', 'DM p（QLIKE）', 'ΔMSE', 'DM p（MSE）'], rows, widths=[6.6, 2.4, 2.8, 2.4, 2.4], size=9)
caption(d, '表 3　Diebold–Mariano 檢定（HLN 小樣本修正，Newey-West lag=5），目標 A。負值代表前者較佳。')
rows = [[f'{r.small} → {r.big}', f2(r.CW), pv(r.p)] for _, r in CW.iterrows()]
table(d, ['巢狀比較', 'CW 統計量', 'p 值（單尾）'], rows, widths=[8.6, 3, 3])
caption(d, '表 4　Clark–West 巢狀模型檢定，目標 A。')
para(d, f'**Model Confidence Set（90%，區塊拔靴法）：** QLIKE 下存活 {len(MCSQ["alive"])} 個模型（僅剔除天真預測）；MSE 下全部 8 個模型存活。752 個重疊觀測值的檢定力不足以分辨這些模型，此點須於論文中明確說明，並作為「加入第二標的與延長樣本」的理由。')

d.add_heading('2.5 重現性檢查：種子數與函式庫版本', 2)
para(d, '本報告初版以 5 個隨機種子集成，後改為 10 個。過程中發現兩件影響結論穩健性的事，一併記錄。')
rows = [
    ['同環境、同種子重跑兩次', 'QLIKE 完全相同（預測值最大差異 0.00e+00）', '訓練流程本身具決定性'],
    ['同環境內 5 種子 vs 10 種子', '種子 0–4 集成 0.2096、種子 5–9 集成 0.2101、10 種子集成 0.2079', '種子數的影響小'],
    ['PyTorch 2.6.0+cu124 vs 2.13.0+cu126', '同程式同種子：5 種子集成 0.1986 vs 0.2096', '**版本差異約 0.010，與 Δ_arch 同一量級**'],
]
table(d, ['檢查項目', '結果', '意涵'], rows, widths=[4.6, 6.6, 5.4], size=9)
caption(d, '表 4-1　重現性檢查（目標 A、測試期 QLIKE）。')
bullet(d, '單一種子的 QLIKE 介於 0.195 與 0.258 之間，跨度 0.064，遠大於各層之間的差距。**以少數種子報告深度學習結果並不可靠。**')
bullet(d, '函式庫版本的影響與 Δ_arch 的估計值同一量級。因此本報告不以 p<0.01 作為 Δ_arch 的強主張，而是陳述「沒有證據顯示架構有幫助，且有證據顯示它較差」。')
bullet(d, '論文正式版應：固定並載明 PyTorch／CUDA 版本、附鎖定版本的環境檔、以 10 個種子集成報告，並揭露種子層級分布。')

d.add_heading('2.6 架構對照組：LSTM', 2)
LM = pd.read_csv('res_lstm_main.csv'); LD = pd.read_csv('res_lstm_decomp.csv'); LS = pd.read_csv('res_lstm_seeds.csv')
para(d, '若只測試 Transformer，「架構沒有增量價值」的結論可能只是該架構不適合此問題。因此本節加入 LSTM 作為同層對照：**相同的 18 個變數、相同的輸入窗口（22 日）、相同的訓練協定（AdamW、提早停止、10 個隨機種子集成）**，超參數同樣只以驗證期選擇（24 組設定 × 2 個種子；選出隱藏維度 128、單層、dropout 0.3、學習率 3e-4，共 76,161 個參數，約為 Transformer 的 2.8 倍）。')
rows = []
for m in ['L1 GJR-GARCH', 'L2 HAR-RV', 'L3 HAR-RV-X (full)', 'L4 Transformer', 'L4 LSTM']:
    a = LM[(LM.target == 'y_hf') & (LM.model == m)].iloc[0]; b = LM[(LM.target == 'y_cc') & (LM.model == m)].iloc[0]
    rows.append([m, f2(a.RMSE), f4(a.QLIKE), f2(b.RMSE), f4(b.QLIKE)])
table(d, ['模型', 'A: RMSE', 'A: QLIKE', 'B: RMSE', 'B: QLIKE'], rows, widths=[5.4, 2.8, 2.8, 2.8, 2.8], size=9, highlight_rows=(2,))
caption(d, '表 6　加入 LSTM 對照組後的 Level 4 比較（兩種架構皆為 10 個種子集成）。')
rows = []
for _, r in LD.iterrows():
    ci = '—' if not np.isfinite(r.ci_lo) else f'[{f3(r.ci_lo)}, {f3(r.ci_hi)}]'
    rows.append(['目標 A' if r.target == 'y_hf' else '目標 B', r.arch, f3(r.delta_arch), ci, pv(r.dm_p)])
table(d, ['目標', '比較', 'ΔQLIKE', '90% 信賴區間', 'DM p 值'], rows, widths=[2.4, 4.6, 2.8, 3.8, 3], size=9)
caption(d, '表 7　兩種深度學習架構的 Δ_arch，以及兩者之間的直接比較。')
bullet(d, f'**結論不是 Transformer 專屬的。** LSTM 的 Δ_arch 在兩個目標上同樣為負（目標 A {f3(LD[(LD.target=="y_hf")&(LD.arch=="L4 LSTM")].delta_arch.iloc[0])}，p={pv(LD[(LD.target=="y_hf")&(LD.arch=="L4 LSTM")].dm_p.iloc[0])}；目標 B {f3(LD[(LD.target=="y_cc")&(LD.arch=="L4 LSTM")].delta_arch.iloc[0])}，p={pv(LD[(LD.target=="y_cc")&(LD.arch=="L4 LSTM")].dm_p.iloc[0])}），**沒有任何一個深度學習架構勝過使用相同資訊的線性模型**。')
bullet(d, f'**但 LSTM 明顯優於 Transformer。** 目標 A 的 QLIKE 為 {f4(LM[(LM.target=="y_hf")&(LM.model=="L4 LSTM")].QLIKE.iloc[0])} vs {f4(LM[(LM.target=="y_hf")&(LM.model=="L4 Transformer")].QLIKE.iloc[0])}（DM p={pv(LD[LD.arch=="Transformer − LSTM"].dm_p.iloc[0])}）；目標 B 則無顯著差異（p={pv(LD[(LD.target=="y_cc")&(LD.arch=="Transformer − LSTM")].dm_p.iloc[0])}），且 LSTM 的 RMSE 在目標 B 上最低。深度學習家族內部的排序本身並不穩定。')
bullet(d, f'**LSTM 的種子分散度較小：** 目標 A 各種子 QLIKE 介於 {f4(LS[LS.target=="y_hf"].QLIKE.min())} 與 {f4(LS[LS.target=="y_hf"].QLIKE.max())}（跨度 {f3(LS[LS.target=="y_hf"].QLIKE.max()-LS[LS.target=="y_hf"].QLIKE.min())}），小於 Transformer 的 0.064。')
para(d, '**對論文的意涵：** 本節使「架構無增量價值」從單一模型的觀察，升級為跨兩種主流序列架構的結論；同時也顯示，若只報告單一深度學習架構，排序可能因架構選擇而反轉。')

d.add_heading('2.4 預測軌跡與市場情境', 2)
figure(d, 'fig/r3_pred.png', '圖 3　測試期預測與實際波動；下圖放大 2025 年 4 月關稅衝擊')
piv = RG.pivot(index='model', columns='regime', values='QLIKE')
cols_order = ['全部', '低 VIX（下三分位）', '高 VIX（上三分位）', '高波動日（實際前20%）', '2025/3-5 關稅衝擊']
rows = []
for m in MA.index:
    rows.append([m] + [f3(piv.loc[m, c]) for c in cols_order])
table(d, ['模型'] + [c.replace('（', '\n（') for c in cols_order], rows, widths=[4.2, 2, 2.4, 2.4, 2.6, 2.6], size=8.5)
caption(d, '表 5　不同市場情境的 QLIKE（目標 A）。')
figure(d, 'fig/r4_regime.png', '圖 4　主要模型在各情境的 QLIKE', width=15)
bullet(d, 'HAR-RV-X 在整體、低 VIX 與高 VIX 情境均最佳。')
bullet(d, f'**但在實際波動最高的 20% 交易日，GJR-GARCH 明顯勝出**（QLIKE {f3(piv.loc["L1 GJR-GARCH", "高波動日（實際前20%）"])} vs HAR-RV-X {f3(piv.loc["L3 HAR-RV-X (full)", "高波動日（實際前20%）"])}、Transformer {f3(piv.loc["L4 Transformer", "高波動日（實際前20%）"])}）。與前導實驗一致：深度學習模型在波動急升時系統性低估。')

# ---------- economic
d.add_page_break()
d.add_heading('三、經濟價值評估', 1)
figure(d, 'fig/r5_econ.png', '圖 5　左：波動率目標化投組累積淨值；右：5% VaR 違反率', width=16.5)
d.add_heading('3.1 VaR 與 ES 回測', 2)
rows = []
for _, r in VAR[VAR.alpha == 0.05].iterrows():
    rows.append([r.model, str(int(r.viol)), f'{r.rate*100:.2f}%', pv(r.p_kupiec) if np.isfinite(r.p_kupiec) else '—',
                 pv(r.p_ind) if np.isfinite(r.p_ind) else '—', pv(r.p_cc) if np.isfinite(r.p_cc) else '—', f'{r.tick*1e4:.1f}'])
table(d, ['模型', '違反次數', '違反率', 'Kupiec p', '獨立性 p', '條件覆蓋 p', 'Tick loss (×10⁻⁴)'], rows, widths=[4.2, 1.8, 1.8, 2.2, 2.2, 2.2, 2.2], size=9)
caption(d, '表 6　5% VaR 回測（5 日非重疊，151 個區間；過濾歷史模擬，標準化分配取自訓練樣本並對所有模型共用）。')
bullet(d, '所有模型皆通過 Kupiec、獨立性與條件覆蓋檢定，違反率 2.0–4.0%，略偏保守。')
bullet(d, 'Tick loss 介於 0.00024–0.00026，**模型之間幾乎沒有差別**。1% 水準只有 0–1 次違反，樣本不足以檢定。')
d.add_heading('3.2 波動率目標化投組', 2)
rows = []
for m in list(MA.index) + ['買進持有 SPY']:
    sub = VT[(VT.model == m) & ((VT.cost_bps == 5) | (m == '買進持有 SPY'))]
    if not len(sub): continue
    r = sub.iloc[0]
    rows.append([m, f'{r.ann_ret*100:.1f}%', f'{r.ann_vol*100:.1f}%', f2(r.sharpe), f'{r.maxdd*100:.1f}%', f2(r.turnover), f2(r.avg_w)])
table(d, ['模型', '年化報酬', '年化波動', 'Sharpe', '最大回撤', '年周轉率', '平均曝險'], rows, widths=[4.2, 2.2, 2.2, 2, 2.2, 2, 2], size=9)
caption(d, '表 7　波動率目標化投組（目標年化波動 10%、每 5 日調整、曝險上限 2 倍、單邊成本 5bp）。')
para(d, '**拔靴法檢定（90% 信賴區間，5,000 次區塊重抽）：** Transformer 的 Sharpe 顯著低於 GJR-GARCH（差異區間 [−0.38, −0.06]）；HAR-RV-X 與 GJR-GARCH 無顯著差異（[−0.29, 0.00]）；Transformer 與 HAR-RV-X 無顯著差異（[−0.17, +0.02]）。')
para(d, '**核心矛盾：統計上最佳的模型（HAR-RV-X）在經濟上並非最佳，GJR-GARCH 才是。** 原因是 GJR 的波動預測較高、平均曝險較低（0.80 vs 0.86），在這段多頭期間反而降低回撤。這正是「統計顯著不等於經濟重要」的實例，也是本研究對風險管理實務最直接的意涵。')

# ---------- granger / shap
d.add_heading('四、Granger 預測因果與 SHAP 診斷', 1)
d.add_heading('4.1 Granger 預測因果（僅訓練樣本 2011–2020）', 2)
rows = []
for _, r in GR.iterrows():
    rows.append([r.group, str(int(r.lags)), f'{r.wald_h1:.1f}', pv(r.p_h1), f'{r.wald_h5:.1f}', pv(r.p_h5),
                 '是' if r.sig_h5_BH else '否', f'{r.sig_share_rolling*100:.0f}%'])
table(d, ['變數群組', '落後期', 'Wald(h=1)', 'p', 'Wald(h=5)', 'p', 'BH 校正後顯著', '滾動視窗顯著比例'], rows,
      widths=[3.4, 1.6, 2, 1.8, 2, 1.8, 2.2, 2.2], size=8.5)
caption(d, '表 8　群組條件 Granger 檢定（控制 HAR 三項自身落後項，Newey-West HAC）。')
bullet(d, f'六個群組在 BH 校正後全部顯著，其中**選擇權群組的 Wald 統計量最高（h=5 時 {GR[GR.group.str.startswith("G3")].wald_h5.iloc[0]:.0f}）**，與 Δ_info 的結果相互印證。')
bullet(d, '利率群組在 3 年滾動視窗中僅 25% 期間顯著，穩定性最差；其餘群組皆為 100%。')
bullet(d, f'個別變數層級：{", ".join(GV[~GV.sig_BH]['var'].tolist())} 三個變數在 BH 校正後不顯著（期限利差、美元指數報酬、黃金報酬）。定態檢定亦顯示期限利差為非定態，論文中應改以差分形式或於穩健性分析處理。')
d.add_heading('4.2 群組 SHAP 與一致性比對', 2)
figure(d, 'fig/r6_shap_granger.png', '圖 6　左：Transformer 群組重要性；右：Granger 統計量與 SHAP 的關係', width=16.5)
rows = []
M = pd.DataFrame(SG['group_table'])
for _, r in M.sort_values('shap_mean', ascending=False).iterrows():
    rows.append([r.group, f'{r.share*100:.1f}%', f4(r.shap_mean), f4(r.shap_sd), f'{r.wald_h5:.1f}', '是' if r.sig_h5_BH else '否'])
table(d, ['變數群組', 'SHAP 占比', '平均 |SHAP|', '種子標準差', 'Granger Wald(h=5)', 'Granger 顯著'], rows,
      widths=[4, 2.4, 2.6, 2.4, 2.8, 2.4], size=9)
caption(d, '表 9　群組 SHAP（10 個種子，2025 年視窗模型，752 個測試日）與 Granger 統計量對照。')
bullet(d, f'**兩者在最重要的群組上一致：** 選擇權群組同時是 SHAP 占比最高（{M[M.group.str.startswith("G3")].share.iloc[0]*100:.1f}%）與 Granger 最強的群組。')
bullet(d, f'**整體一致性不顯著：** Spearman ρ={SG["spearman"]:.2f}，置換檢定 p={SG["p_permutation"]:.3f}；前三名 Jaccard 重疊率 {SG["jaccard_top3"]:.2f}。群組僅 6 個，此檢定的檢定力極低，結論應保守。')
bullet(d, f'**分歧處：** 跨資產群組（G6）的 Granger 統計量排第三但 SHAP 僅排第六；報酬群組（G4）SHAP 排第二但 Granger 排第四。前者可能是資訊被選擇權群組吸收，後者可能反映模型利用了線性檢定無法捕捉的非線性關係。兩類分歧均完整報告，不挑選有利結果。')
para(d, '依計畫定位，SHAP 僅作為診斷工具：本次檢查未發現不應具預測力的變數獲得高權重（無資料洩漏跡象），成交量群組重要性最低（3.7%），與其含有資料來源結構斷點的已知問題一致。')

# ---------- compute
d.add_heading('五、運算資源與執行時間（GPU）', 1)
sec = np.array([r['secs'] for r in runs]); ep = np.array([r['epochs'] for r in runs])
grid = pickle.load(open('l4_search.pkl', 'rb'))
table(d, ['工作', '規模', '時間'], [
    ['Transformer 超參數搜尋', '48 組設定 × 2 種子 = 96 次訓練（3 程序並行）', '12.5 分鐘（單模型平均 22.7 秒）'],
    ['第二標的：兩種設定 × 10 種子', '2 標的 × 3 年 × 10 種子 × 2 設定 = 120 次', '14.5 分鐘'],
    ['LSTM 對照組', '搜尋 48 次 + 正式 60 次', '4.6 + 5.5 分鐘'],
    ['Transformer 正式訓練', '3 年 × 10 種子 × 2 目標 = 60 次', f'平均 {sec.mean():.1f} 秒、{ep.mean():.0f} 個 epoch'],
    ['SHAP（GradientExplainer）', '10 個模型 × 752 日', '每個約 16 秒'],
    ['GARCH / GJR / GARCH-X', '3 個擴張視窗', '合計 66 秒'],
    ['HAR 系列（OLS）', '全部視窗', '< 1 秒'],
    ['Granger 檢定（含滾動視窗）', '6 群組 × 2 期間 + 8 個滾動視窗', '約 2 分鐘'],
], widths=[4.6, 6.4, 5.6], size=9)
caption(d, '表 10　執行時間（NVIDIA GTX 1060 3GB、CUDA 12.4、PyTorch 2.6.0、3 程序並行）')
para(d, f'**GPU 效益：** 每個 epoch 0.87 秒且不隨輸入窗口長度改變；CPU 版為 1.2–8 秒（L=44 以上差距最大）。顯存使用僅 82 MB，可同時執行 3 個訓練程序。選定架構為 L=22、嵌入維度 32、2 層、dropout 0.1、學習率 1e-3，共 {runs[0]["params"]:,} 個參數。前 8 名設定的驗證 MSE 介於 0.2966–0.3022，差異極小，顯示結果對超參數不敏感。')

# ---------- implications
# ---------- second asset
d.add_page_break()
d.add_heading('六、第二標的穩健性分析（QQQ）', 1)
A2 = pd.read_csv('res_asset2_main.csv'); D2 = pd.read_csv('res_asset2_decomp.csv'); M2 = pd.read_csv('res_asset2_dm.csv')
MCS2 = json.load(open('res_asset2_mcs.json', encoding='utf-8'))
para(d, 'QQQ 沒有分鐘資料，無法計算 5 分鐘已實現波動。因此本節改以**日頻可得的資訊集**重建同一套階梯：以 Garman-Klass 區間變異取代高頻 RV、以日報酬的負半變異取代 5 分鐘半變異、隱含波動改用對應標的之指數（QQQ 用 VXN、SPY 用 VIX），並保留共同的 VIX9D 期限結構斜率。跨資產變數採**相對報酬**（自身報酬減另一標的報酬），因為 QQQ 與 SPY 報酬的相關達 0.93（VIF 7.1），相減後 VIF 降為 1.0。為使比較成立，**SPY 亦以完全相同的日頻設定重跑一次**，因此兩欄之間的差異只來自標的本身。預測目標為未來 5 日的日報酬已實現波動（即主分析的目標 B）。')
rows = []
O2 = ['L0 Naive', 'L1 GARCH(1,1)', 'L1 GJR-GARCH', 'L2 HAR-GK', 'L3 HAR-GK-X (opt only)', 'L3 HAR-GK-X (full)', 'L4 Transformer']
for m in O2:
    q = A2[(A2.asset == 'QQQ') & (A2.model == m)].iloc[0]; s_ = A2[(A2.asset == 'SPY') & (A2.model == m)].iloc[0]
    rows.append([m, f2(q.RMSE), f4(q.QLIKE), f2(s_.RMSE), f4(s_.QLIKE)])
table(d, ['模型', 'QQQ: RMSE', 'QQQ: QLIKE', 'SPY: RMSE', 'SPY: QLIKE'], rows, widths=[5.4, 2.8, 2.8, 2.8, 2.8], size=9, highlight_rows=(5,))
caption(d, '表 11　第二標的穩健性分析：兩個標的在相同日頻資訊集下的測試期表現（2023–2025）。Transformer 為 10 個隨機種子的集成。')
figure(d, 'fig/r7_asset2.png', '圖 7　左：兩標的各層 QLIKE；右：損失分解比較', width=16.5)
rows = []
for _, r in D2[D2.step.str.startswith('Δ')].iterrows():
    rows.append([r.asset, r.step, f3(r.delta), f'[{f3(r.ci_lo)}, {f3(r.ci_hi)}]', pv(r.dm_p)])
table(d, ['標的', '成分', 'QLIKE 改善', '90% 信賴區間', 'DM p 值'], rows, widths=[2, 5, 2.8, 3.8, 3], size=9)
caption(d, '表 12　兩個標的的損失分解。')
para(d, '**結論：QQQ 完整複製了 SPY 的型態。**')
qi2 = D2[(D2.asset == 'QQQ')].set_index('step')
bullet(d, f'**Δ_info 在兩個標的皆顯著為正：** QQQ +{f3(qi2.loc["Δ_info (L2→L3)", "delta"])}（p={pv(qi2.loc["Δ_info (L2→L3)", "dm_p"])}）、SPY +{f3(D2[(D2.asset=="SPY")&(D2.step.str.startswith("Δ_info"))].delta.iloc[0])}（p={pv(D2[(D2.asset=="SPY")&(D2.step.str.startswith("Δ_info"))].dm_p.iloc[0])}）。選擇權前瞻資訊的價值不是 SPY 特有的現象。')
bullet(d, f'**Δ_arch 在兩個標的皆為負但不顯著：** QQQ {f3(qi2.loc["Δ_arch (L3→L4)", "delta"])}（p={pv(qi2.loc["Δ_arch (L3→L4)", "dm_p"])}）、SPY {f3(D2[(D2.asset=="SPY")&(D2.step.str.startswith("Δ_arch"))].delta.iloc[0])}（p={pv(D2[(D2.asset=="SPY")&(D2.step.str.startswith("Δ_arch"))].dm_p.iloc[0])}）。方向與主分析一致。')
bullet(d, '**最佳模型一致：** 兩個標的皆為 L3 HAR-GK-X（全部變數）。')
bullet(d, f'**MCS（QLIKE，90%）：** QQQ 存活 {len(MCS2["QQQ"])} 個模型、SPY 存活 {len(MCS2["SPY"])} 個；SPY 的日頻設定下 L2 HAR-GK 被剔除，檢定力仍然有限。')
para(d, '**附帶發現：** SPY 在日頻資訊集下的最佳 QLIKE 為 0.3127，與主分析中使用 5 分鐘高頻特徵的 0.3108 幾乎相同。對日報酬定義的目標而言，**高頻特徵相對於區間變異幾乎沒有額外貢獻**，這也呼應了主分析中 Δ_HF 為負的結果。')
para(d, '**本節的限制：** QQQ 缺乏分鐘資料，無法檢驗高頻已實現波動的結論；VXN 沒有 9 日期限的對應指數，故沿用 S&P 500 的 VIX9D/VIX 斜率作為市場整體的短期壓力代理變數。')

d.add_heading('6.1 跨資產變數的參數化：相對報酬 vs 原始報酬', 2)
SP = pd.read_csv('res_asset2_spec.csv'); SPD = pd.read_csv('res_asset2_decomp_spec.csv')
para(d, '相對報酬（QQQ−SPY）與另一標的的原始報酬互為線性轉換：因為自身報酬已在報酬群組內，兩種設定張出的線性空間完全相同。**因此 L0 至 L3 的預測值在兩種設定下完全相同**（實測差異僅出現在浮點運算的第四位小數）。差異只可能來自 Transformer，因為輸入標準化與非線性轉換會受變數尺度影響（SPY 報酬標準差 1.31%，相對報酬 0.49%）。')
para(d, '為區分「設定效果」與「隨機種子雜訊」，本節對兩種設定各訓練 10 個種子（共 120 次訓練）。')
rows = []
for _, r in SP[SP.spec.isin(['rel', 'abs'])].iterrows():
    rows.append([r.asset, '相對報酬' if r.spec == 'rel' else '原始報酬', f3(r.seed_mean), f3(r.seed_sd),
                 f'{f3(r.seed_min)}–{f3(r.seed_max)}', f4(r.ens_QLIKE)])
table(d, ['標的', '設定', '種子平均 QLIKE', '種子標準差', '種子範圍', '10 種子集成'], rows,
      widths=[2.2, 3, 3, 2.6, 3.2, 2.6], size=9)
caption(d, '表 13　兩種跨資產變數設定的比較（各 10 個隨機種子）。')
figure(d, 'fig/r8_spec.png', '圖 8　兩種設定的種子層級比較', width=15)
q_perm = {'QQQ': 0.822, 'SPY': 0.429}
bullet(d, f'**兩種設定無法區分。** 種子平均的差異在置換檢定下不顯著（QQQ p={q_perm["QQQ"]:.3f}、SPY p={q_perm["SPY"]:.3f}）；集成預測的 DM 檢定同樣不顯著（QQQ p=0.319、SPY p=0.754）。')
bullet(d, f'**種子雜訊遠大於設定效果。** 單一種子的 QLIKE 在 QQQ 可從 {f3(SP[(SP.asset=="QQQ")&(SP.spec=="rel")].seed_min.iloc[0])} 到 {f3(SP[(SP.asset=="QQQ")&(SP.spec=="rel")].seed_max.iloc[0])}，跨度約 0.11，是兩種設定差距的十倍以上。')
bullet(d, '**方法上的教訓：** 以 5 個種子評估深度學習模型不足以支撐顯著性宣稱。本節初期以 5 個種子曾得到「Δ_arch 顯著為負（p≈0.04）」，增加到 10 個種子後回到不顯著（表 12）；主分析則相反，由不顯著轉為顯著（§2.2）。兩個方向的變動都說明同一件事：**5 個種子的顯著性不可靠**。論文正式版一律以 10 個種子集成報告，並揭露種子層級分布。')
para(d, '結論：採用相對報酬是基於共線性診斷（VIF 由 7.1 降至 1.0）與可解讀性的選擇，**而非因為它改善預測**。兩種設定的實證結論相同。')

d.add_heading('七、對論文撰寫的意涵', 1)
numbered(d, '**主標題結論可以成立且更強：** 「在資訊集對等下，深度學習相對線性模型沒有增量價值；全部改善來自選擇權前瞻資訊。」Δ_info 顯著為正（p=0.011），Δ_arch 顯著為負（p=0.005），兩者構成完整論述。但 Δ_arch 的顯著性對函式庫版本敏感（§2.5），論文宜以「沒有增量價值」為主張，不宜強調「顯著較差」。')
numbered(d, '**第二個可發表的發現：** 前瞻資訊只在 HAR 架構中有效，在 GARCH 變異數方程中無效（GARCH-X 係數為 0）。這是計畫階段未預期的結果，值得單獨一小節。')
numbered(d, '**第三個發現：** 統計最佳與經濟最佳不一致（HAR-RV-X vs GJR-GARCH），且 VaR 層面各模型無差別。此節直接回應目標期刊對政策與實務意涵的偏好。')
numbered(d, '**必須誠實處理的弱點：** MCS 無法分辨模型、Δ_HF 為負、Granger × SHAP 一致性不顯著。三者都指向同一個原因：單一標的、三年測試期的檢定力有限。建議在論文中集中於「限制」一節說明，並以此支持後續研究方向。')
numbered(d, '**LSTM 對照組已完成（§2.6）：** 兩種主流序列架構都未勝過線性模型，可直接回應「為何選 Transformer」的質疑。')
numbered(d, '**第二標的已完成（§六）：** QQQ 複製了 SPY 的型態，可直接作為論文的穩健性一節；跨資產變數的參數化不影響結論（§6.1）。**深度學習的結果一律以 10 個種子集成報告**，5 個種子會產生不可靠的顯著性。**尚未執行：** 分量因果檢定與 2026 年最終保留樣本；前者屬補充資料，後者應於全部設計凍結後執行一次。')
d.add_heading('八、限制', 1)
bullet(d, '測試期 2023–2025 整體偏平靜，高波動日集中於 2023 年第一季與 2025 年 1–5 月，情境比較受少數事件影響。')
bullet(d, 'VIX9D 自 2011 年才有資料，樣本未涵蓋 2008 金融海嘯。')
bullet(d, 'GARCH-X 的多步預測將外生變數固定於最後觀測值，可能低估其長期貢獻。')
bullet(d, 'VaR 回測採單一過濾歷史模擬設定，且 1% 水準的區間數不足。')
bullet(d, '波動率目標化投組未計入融資成本、放空限制與稅負。')
bullet(d, 'QQQ 僅有日頻資料，第二標的分析無法檢驗高頻已實現波動的結論；VXN 無 9 日期限對應指數。')
bullet(d, 'Transformer 的結果對 PyTorch 版本敏感（§2.5）：同一份程式與同一組種子，在 2.6.0+cu124 與 2.13.0+cu126 下的 QLIKE 相差約 0.010，與 Δ_arch 的估計值同一量級。論文須載明版本並附鎖定版本的環境檔。')
bullet(d, 'SHAP 為近似方法且特徵共線，僅在群組層級解讀；Granger × SHAP 的比對僅 6 個群組，檢定力低。')
d.add_heading('附錄：程式與輸出', 1)
for f, desc in [('build_dataset.py', '合併 SPY 高頻特徵與外生變數，建立 18 變數分析資料集'),
                ('ladder.py', 'L1 GARCH/GJR、L2 HAR-RV、L3 HAR-RV-X／GARCH-X（自寫最大概似）'),
                ('l4.py', 'L4 Transformer：超參數搜尋與擴張視窗訓練（GPU）'),
                ('shar.py / shar_eval.py', 'SHAR 與 SHAR-X 穩健性檢查'),
                ('granger.py', '定態檢定、群組與個別變數的 Granger 檢定、滾動穩定性'),
                ('shap_l4.py', '群組 SHAP 與 Granger × SHAP 比對（GPU）'),
                ('evaluate.py / run_eval.py', '損失函數、DM／CW／MCS、VaR 回測、波動率目標化投組'),
                ('asset2.py / asset2_l4.py / asset2_eval.py', '第二標的（QQQ）與 SPY 日頻資訊集的完整階梯'),
                ('asset2_l4b.py / asset2_spec.py / asset2_final.py', '兩種跨資產設定 × 10 種子的比較與最終表格'),
                ('l4_main10.py', '主分析 Level 4 的 10 種子重跑'),
                ('lstm.py / lstm_final.py / lstm_eval.py', 'LSTM 同層對照組（超參數搜尋、10 種子訓練與評估）'),
                ('figs2.py / fig_asset2.py / fig_spec.py', '本報告全部圖表'),
                ('res_*.csv、granger_*.csv', '所有結果資料表')]:
    bullet(d, f'**{f}**：{desc}')
d.save('SPY波動率_資訊階梯實證結果報告.docx')
print('saved')
