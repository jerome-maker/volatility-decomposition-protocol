import requests, pandas as pd, io, time, json
meta={}
def cboe(name):
    u=f"https://cdn.cboe.com/api/global/us_indices/daily_prices/{name}_History.csv"
    r=requests.get(u, timeout=90); r.raise_for_status()
    d=pd.read_csv(io.StringIO(r.text))
    d.columns=[c.strip().upper() for c in d.columns]
    d['DATE']=pd.to_datetime(d['DATE'])
    d=d.set_index('DATE')[['CLOSE']].rename(columns={'CLOSE':name})
    meta[name]=dict(url=u, bytes=len(r.content), start=str(d.index.min().date()), end=str(d.index.max().date()), n=len(d))
    return d
def fred(sid):
    u=f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
    r=requests.get(u, timeout=90); r.raise_for_status()
    d=pd.read_csv(io.StringIO(r.text))
    d.columns=['DATE',sid]; d['DATE']=pd.to_datetime(d['DATE'])
    d=d.set_index('DATE'); d[sid]=pd.to_numeric(d[sid], errors='coerce')
    meta[sid]=dict(url=u, bytes=len(r.content), start=str(d.index.min().date()), end=str(d.index.max().date()), n=int(d[sid].notna().sum()))
    return d
X=pd.concat([cboe('VIX'), cboe('VIX9D'), cboe('VIX3M'), fred('DGS10'), fred('DGS3MO'), fred('DTWEXBGS')], axis=1)
import yfinance as yf
px=yf.download(['QQQ','TLT','GLD'], start='2002-12-01', end='2026-09-16', auto_adjust=True, progress=False)['Close']
meta['yfinance']=dict(tickers=['QQQ','TLT','GLD'], start=str(px.index.min().date()), end=str(px.index.max().date()), n=len(px), downloaded=time.strftime('%Y-%m-%d %H:%M'))
X=X.join(px, how='outer').sort_index()
X.to_parquet('data/exog_raw.parquet')
json.dump(meta, open('data/exog_meta.json','w'), indent=1)
print(json.dumps(meta, indent=1))
print(X.loc['2011':].head(3)); print(X.tail(3)); print(X.loc['2011-01-03':].isna().mean().round(4))
