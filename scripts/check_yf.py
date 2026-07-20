import yfinance as yf
for ticker in ['DX-Y.NYB', '^VIX', '^TNX']:
    try:
        data = yf.download(ticker, period='1mo', interval='1d', progress=False)
        if len(data) > 0:
            print(f'{ticker}: {len(data)} rows, latest={data.index[-1].date()}')
        else:
            print(f'{ticker}: empty')
    except Exception as e:
        print(f'{ticker}: ERROR - {e}')
