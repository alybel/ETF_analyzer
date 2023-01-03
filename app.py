import numpy as np
import streamlit as st
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import lib
import pandas as pd
import pickle

st.set_page_config(layout="wide")
c1, c2 = st.columns([1, 2])

if "selected_tickers" not in st.session_state:
    st.session_state.selected_tickers = []

if "pf_weight" not in st.session_state:
    st.session_state.pf_weight = {}

if 'portfolio_tickers' not in st.session_state:
    st.session_state.portfolio_tickers = []


@st.cache
def get_data(ticker):
    df = lib.get_data(ticker=ticker)
    return df


def store_portfolio():
    d = {
        'pf_weight': st.session_state.pf_weight,
        'portfolio_tickers': st.session_state.portfolio_tickers,
        'selected_tickers': st.session_state.selected_tickers
    }
    pickle.dump(d, open('portfolio_dump.pcl', 'wb'))


def load_portfolio():
    d = pickle.load(open('portfolio_dump.pcl', 'rb'))
    st.session_state.pf_weight = d['pf_weight']
    st.session_state.portfolio_tickers = d['portfolio_tickers']
    st.session_state.selected_tickers = d['selected_tickers']


with c1:
    st.text_input(label='Find Ticker', value='MSFT', key='selected_ticker')
    df = get_data(ticker=st.session_state.selected_ticker)
    if df.shape[0] == 0:
        st.write('Ticker not found')
        st.stop()


    def add_ticker():
        if st.session_state.selected_ticker in st.session_state.selected_tickers:
            st.write('Ticker already in Portfolio List')
        else:
            st.session_state.selected_tickers.append(st.session_state.selected_ticker)
            st.session_state.portfolio_tickers.append(st.session_state.selected_ticker)


    fig = make_subplots(rows=1, cols=1, shared_xaxes=True, )
    fig.add_trace(
        go.Scatter(x=df.index, y=df['Close'], name=st.session_state.selected_ticker,
                   line=dict(color='grey', width=4)),
        row=1, col=1,

    )

    fig.update_layout(height=300, width=400, title_text="price development of %s " % st.session_state.selected_ticker)
    fig.update_xaxes(rangeslider_visible=False, rangeselector=dict(
        buttons=list([
            dict(count=1, label="1m", step="month", stepmode="backward"),
            dict(count=6, label="6m", step="month", stepmode="backward"),
            dict(count=1, label="YTD", step="year", stepmode="todate"),
            dict(count=1, label="1y", step="year", stepmode="backward"),
            dict(step="all")
        ]))
                     )

    st.plotly_chart(fig, use_container_width=True)
    st.button(label='add %s to portfolio' % st.session_state.selected_ticker, on_click=add_ticker)
    st.button(label='Store Portfolio', on_click=store_portfolio)
    st.button(label='Load Portfolio', on_click=load_portfolio)
    # st.write(df.tail())


def add_weights_to_pf_weights():
    for ticker in st.session_state.portfolio_tickers:
        if '%s_weight' % ticker in st.session_state:
            st.session_state.pf_weight[ticker] = st.session_state['%s_weight' % ticker]


def run_analytics():
    add_weights_to_pf_weights()
    d = pd.DataFrame()
    for ticker in st.session_state.portfolio_tickers:
        ticker_returns = get_data(ticker)['Close'].pct_change()
        ticker_returns = ticker_returns.rename('%s_return' % ticker)
        ticker_returns = ticker_returns * st.session_state.pf_weight[ticker]
        if d.shape[0] == 0:
            d = ticker_returns.copy()
        else:
            d = pd.concat([d, ticker_returns], axis=1, join='inner')

    if isinstance(d, pd.Series):
        p_returns = d.to_frame().sum(axis=1)
    else:
        p_returns = d.sum(axis=1)
    p_returns.index = pd.to_datetime(p_returns.index)
    s = p_returns[p_returns.index.map(lambda x: x.date) >= st.session_state.start_analysis_date]
    s = s.add(1).cumprod()
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, )
    fig.add_trace(
        go.Scatter(x=s.index, y=s, name='Portfolio Performance',
                   line=dict(color='grey', width=4)),
        row=1, col=1,

    )

    benchmark = get_data('SPY')['Close'].pct_change().rename('benchmark')
    active_returns = p_returns - benchmark
    s2 = active_returns[active_returns.index.map(lambda x: x.date) >= st.session_state.start_analysis_date]
    bm_r = benchmark[benchmark.index.map(lambda x: x.date) >= st.session_state.start_analysis_date]
    s2 = s2.add(1).cumprod()
    bm = bm_r.add(1).cumprod()

    fig.add_trace(
        go.Scatter(x=bm.index, y=bm, name='Benchmark (SPY)',
                   line=dict(color='red', width=4)),
        row=1, col=1,
    )

    fig.add_trace(
        go.Scatter(x=s2.index, y=s2, name='Portfolio Active Performance',
                   line=dict(color='blue', width=4)),
        row=2, col=1,
    )

    fig.update_layout(height=500, width=400,
                      title_text="price development of Portfolio")
    fig.update_xaxes(rangeslider_visible=False, rangeselector=dict(
        buttons=list([
            dict(count=1, label="1m", step="month", stepmode="backward"),
            dict(count=6, label="6m", step="month", stepmode="backward"),
            dict(count=1, label="YTD", step="year", stepmode="todate"),
            dict(count=1, label="1y", step="year", stepmode="backward"),
            dict(step="all")
        ]))
                     )

    all = pd.concat([bm_r, p_returns], axis=1, join='inner')
    all = all[all.index.map(lambda x: x.date) >= st.session_state.start_analysis_date]
    corr = all.corr().values[0][1]

    st.plotly_chart(fig, use_container_width=True)
    d = {
        'Correlation between Portfolio and Benchmark': corr
    }
    print(d)
    st.table(pd.DataFrame([d]).T)


with c2:
    st.multiselect(label='selected tickers', default=st.session_state.portfolio_tickers,
                   options=st.session_state.selected_tickers, key='portfolio_tickers')
    st.write(st.session_state.portfolio_tickers)

    for ticker in st.session_state.portfolio_tickers:
        st.number_input(label='%s weight' % ticker, value=1 / len(st.session_state.portfolio_tickers) if not ticker in st.session_state.pf_weight else st.session_state.pf_weight[ticker],
                        key='%s_weight' % ticker)

    st.date_input(label='Begin Analysis from', key='start_analysis_date',
                  value=pd.to_datetime(pd.Timestamp.today() - pd.Timedelta(days=5 * 365)))
    st.button(label='Run Portfolio Analytics', on_click=run_analytics)
