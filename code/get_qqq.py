import requests, pandas as pd, io, json, yfinance as yf, numpy as np, time
u="https://cdn.cboe.com/api/global/us_indices/daily_prices/VXN_History.csv"
r=requests.get(u, timeout=90); r.raise_for_status()
v=pd.read_csv(io.StringIO(r.text)); v.columns=[c.strip().upper() for c in v.columns]
v['DATE']=pd.to_datetime(v['DATE']); v=v.set_index('DATE')[['CLOSE']].rename(columns={'CLOSE':'VXN'})
print('VXN', len(v), v.index.min().date(), v.index.max().date())
px=yf.download(['QQQ','SPY'], start='2010-01-01', end='2026-09-16', auto_adjust=True, progress=False)
out={}
for t in ['QQQ','SPY']:
    d=pd.DataFrame({c: px[c][t] for c in ['Open','High','Low','Close','Volume']}).dropna()
    out[t]=d
    print(t, len(d), d.index.min().date(), d.index.max().date())
pd.concat({k: v2 for k,v2 in out.items()}, axis=1).to_parquet('data/daily_ohlc.parquet')
v.to_parquet('data/vxn.parquet')
meta=json.load(open('data/exog_meta.json'))
meta['VXN']=dict(url=u, bytes=len(r.content), start=str(v.index.min().date()), end=str(v.index.max().date()), n=len(v))
meta['QQQ_SPY_daily_ohlc']=dict(source='yfinance', downloaded=time.strftime('%Y-%m-%d %H:%M'), n=len(out['QQQ']))
json.dump(meta, open('data/exog_meta.json','w'), indent=1)
