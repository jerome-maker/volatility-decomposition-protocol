"""Verify every citation in the manuscript against Crossref."""
import requests, json, difflib, time, sys
REFS = [
 ("Aas et al. 2021","Explaining individual predictions when features are dependent: More accurate approximations to Shapley values"),
 ("Andersen et al. 2003","Modeling and forecasting realized volatility"),
 ("Barndorff-Nielsen & Shephard 2004","Power and bipower variation with stochastic volatility and jumps"),
 ("Bucci 2020","Realized volatility forecasting with neural networks"),
 ("Busch et al. 2011","The role of implied volatility in forecasting future realized volatility and jumps in foreign exchange, stock, and bond markets"),
 ("Christensen & Prabhala 1998","The relation between implied and realized volatility"),
 ("Christensen et al. 2023","A machine learning approach to volatility forecasting"),
 ("Christoffersen 1998","Evaluating interval forecasts"),
 ("Clark & West 2007","Approximately normal tests for equal predictive accuracy in nested models"),
 ("Corsi 2009","A simple approximate long-memory model of realized volatility"),
 ("Diebold & Mariano 1995","Comparing predictive accuracy"),
 ("Dufour & Renault 1998","Short run and long run causality in time series: theory"),
 ("Engle 1982","Autoregressive conditional heteroscedasticity with estimates of the variance of United Kingdom inflation"),
 ("Engle & Bollerslev 1986","Modelling the persistence of conditional variances"),
 ("Engle & Manganelli 2004","CAViaR: conditional autoregressive value at risk by regression quantiles"),
 ("Fleming et al. 2003","The economic value of volatility timing using realized volatility"),
 ("Giacomini & White 2006","Tests of conditional predictive ability"),
 ("Glosten et al. 1993","On the relation between the expected value and the volatility of the nominal excess return on stocks"),
 ("Granger 1969","Investigating causal relations by econometric models and cross-spectral methods"),
 ("Gu et al. 2020","Empirical asset pricing via machine learning"),
 ("Hansen 2005","A test for superior predictive ability"),
 ("Hansen & Lunde 2005","A forecast comparison of volatility models: does anything beat a GARCH(1,1)?"),
 ("Hansen et al. 2011","The model confidence set"),
 ("Harvey et al. 1997","Testing the equality of prediction mean squared errors"),
 ("Hochreiter & Schmidhuber 1997","Long short-term memory"),
 ("Jain & Wallace 2019","Attention is not explanation"),
 ("Kunsch 1989","The jackknife and the bootstrap for general stationary observations"),
 ("Kumar et al. 2020","Problems with Shapley-value-based explanations as feature importance measures"),
 ("Kupiec 1995","Techniques for verifying the accuracy of risk measurement models"),
 ("Lim et al. 2021","Temporal fusion transformers for interpretable multi-horizon time series forecasting"),
 ("Lundberg & Lee 2017","A unified approach to interpreting model predictions"),
 ("Moreira & Muir 2017","Volatility-managed portfolios"),
 ("Patton 2011","Volatility forecast comparison using imperfect volatility proxies"),
 ("Patton & Sheppard 2015","Good volatility, bad volatility: signed jumps and the persistence of volatility"),
 ("Rudin 2019","Stop explaining black box machine learning models for high stakes decisions and use interpretable models instead"),
 ("Toda & Yamamoto 1995","Statistical inference in vector autoregressions with possibly integrated processes"),
 ("Vaswani et al. 2017","Attention is all you need"),
 ("White 2000","A reality check for data snooping"),
 ("Zeng et al. 2023","Are transformers effective for time series forecasting?"),
 # reproducibility literature (new, to be confirmed)
 ("Kapoor & Narayanan 2023","Leakage and the reproducibility crisis in machine-learning-based science"),
 ("Pineau et al. 2021","Improving reproducibility in machine learning research"),
 ("Gundersen & Kjensmo 2018","State of the art: reproducibility in artificial intelligence"),
]
out=[]
for key,title in REFS:
    try:
        r=requests.get("https://api.crossref.org/works", params={"query.bibliographic":title,"rows":3,
            "select":"title,author,container-title,issued,volume,page,DOI,type"},
            headers={"User-Agent":"ref-check/1.0 (mailto:jerome.chou@mail.ntust.edu.tw)"}, timeout=40)
        items=r.json()["message"]["items"]
    except Exception as e:
        out.append(dict(key=key, status="ERROR "+str(e)[:40])); continue
    best=None
    for it in items:
        t=(it.get("title") or [""])[0]
        sim=difflib.SequenceMatcher(None, title.lower(), t.lower()).ratio()
        if best is None or sim>best[0]: best=(sim,it)
    sim,it=best
    au=it.get("author",[])
    first=(au[0].get("family","?") if au else "?")
    out.append(dict(key=key, sim=round(sim,2), matched=(it.get("title") or [""])[0][:70],
        first_author=first, n_authors=len(au), journal=(it.get("container-title") or [""])[0][:42],
        year=(it.get("issued",{}).get("date-parts",[[None]])[0][0]), vol=it.get("volume"),
        page=it.get("page"), doi=it.get("DOI"), type=it.get("type")))
    time.sleep(0.3)
import pandas as pd
df=pd.DataFrame(out); pd.set_option('display.width',260); pd.set_option('display.max_colwidth',44)
df.to_csv('ref_check.csv',index=False)
print(df[['key','sim','first_author','year','journal','vol','page','doi']].to_string(index=False))
print('\n低相似度（需人工確認）:'); print(df[df.sim<0.75][['key','sim','matched','journal','year']].to_string(index=False))
