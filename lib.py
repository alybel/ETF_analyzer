import pandas as pd
import yfinance as yf

etfs_test = ["0P0000IXA4.F", "BATE.F"]


def get_data(ticker='MSFT'):
    iticker = yf.Ticker(ticker)
    df = iticker.history(period='max')
    df['Date'] = pd.to_datetime(df.index.date)
    df = df.set_index('Date', drop=True)
    df = df.sort_index(ascending=True)
    df = df.drop_duplicates(keep='last')
    return df


if __name__ == '__main__':
    store = {}
    for etf in etfs_test:
        data = get_data(ticker=etf)
        store[etf] = data.copy()

    d = pd.DataFrame()
    for ticker in ['AAPL', 'MSFT']:  # st.session_state.portfolio_tickers:
        ticker_returns = get_data(ticker)['Close'].pct_change()
        #ticker_returns = ticker_returns.rename('%s_return' % ticker)
        if d.shape[0] == 0:
            d = ticker_returns.copy()
        else:
            d = pd.concat([d, ticker_returns], axis=1, join='inner')

    s = d.sum(axis=1).add(1).cumprod()
    a = 1
