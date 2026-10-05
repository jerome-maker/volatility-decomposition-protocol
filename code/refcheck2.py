"""Second pass: force the published journal version by filtering on container title."""
import requests, difflib, time, pandas as pd
WANT = [
 ("Andersen et al. 2003","Modeling and forecasting realized volatility","Econometrica"),
 ("Busch et al. 2011","The role of implied volatility in forecasting future realized volatility and jumps","Journal of Econometrics"),
 ("Christensen & Prabhala 1998","The relation between implied and realized volatility","Journal of Financial Economics"),
 ("Clark & West 2007","Approximately normal tests for equal predictive accuracy in nested models","Journal of Econometrics"),
 ("Diebold & Mariano 1995","Comparing predictive accuracy","Journal of Business & Economic Statistics"),
 ("Engle 1982","Autoregressive conditional heteroscedasticity with estimates of the variance of United Kingdom inflation","Econometrica"),
 ("Engle & Manganelli 2004","CAViaR: conditional autoregressive value at risk by regression quantiles","Journal of Business & Economic Statistics"),
 ("Fleming et al. 2003","The economic value of volatility timing using realized volatility","Journal of Financial Economics"),
 ("Giacomini & White 2006","Tests of conditional predictive ability","Econometrica"),
 ("Glosten et al. 1993","On the relation between the expected value and the volatility of the nominal excess return on stocks","Journal of Finance"),
 ("Gu et al. 2020","Empirical asset pricing via machine learning","Review of Financial Studies"),
 ("Hansen 2005","A test for superior predictive ability","Journal of Business & Economic Statistics"),
 ("Hansen & Lunde 2005","A forecast comparison of volatility models: does anything beat a GARCH(1,1)?","Journal of Applied Econometrics"),
 ("Hochreiter & Schmidhuber 1997","Long short-term memory","Neural Computation"),
 ("Moreira & Muir 2017","Volatility-managed portfolios","Journal of Finance"),
 ("Patton 2011","Volatility forecast comparison using imperfect volatility proxies","Journal of Econometrics"),
 ("Christensen et al. 2023","A machine learning approach to volatility forecasting","Journal of Financial Econometrics"),
 ("Pineau et al. 2021","Improving reproducibility in machine learning research","Journal of Machine Learning Research"),
 ("Corsi 2009","A simple approximate long-memory model of realized volatility","Journal of Financial Econometrics"),
]
rows=[]
for key,title,journal in WANT:
    r=requests.get("https://api.crossref.org/works", params={"query.bibliographic":title+" "+journal,"rows":5,
        "filter":"type:journal-article","select":"title,author,container-title,issued,volume,page,DOI"},
        headers={"User-Agent":"ref-check/1.0 (mailto:jerome.chou@mail.ntust.edu.tw)"}, timeout=40)
    best=None
    for it in r.json()["message"]["items"]:
        ct=(it.get("container-title") or [""])[0]
        t=(it.get("title") or [""])[0]
        score=difflib.SequenceMatcher(None,title.lower(),t.lower()).ratio()+ (0.5 if journal.lower().split()[0] in ct.lower() else 0)
        if best is None or score>best[0]: best=(score,it,ct,t)
    sc,it,ct,t=best; au=it.get("author",[])
    rows.append(dict(key=key, journal=ct[:40], year=it.get("issued",{}).get("date-parts",[[None]])[0][0],
                     vol=it.get("volume"), page=it.get("page"), doi=it.get("DOI"),
                     first=au[0].get("family","?") if au else "?", n=len(au), title=t[:52]))
    time.sleep(0.3)
df=pd.DataFrame(rows); pd.set_option('display.width',260); pd.set_option('display.max_colwidth',40)
df.to_csv('ref_check2.csv',index=False)
print(df.to_string(index=False))
