import yfinance as yf

for ticker in ['XAUUSD=X', 'GC=F', 'XAGUSD=X', 'SI=F']:
    t = yf.Ticker(ticker)
    hist = t.history(period='5d')
    if len(hist) > 0:
        last = hist['Close'].iloc[-1]
        print(f'{ticker}: {len(hist)} bars, last close={last:.2f}')
    else:
        print(f'{ticker}: NO DATA')
