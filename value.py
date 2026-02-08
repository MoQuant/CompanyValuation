import requests
import numpy as np
import pandas as pd
import time
import datetime

def CleanSheet(fun):
    def Solve(*a, **b):
        url = fun(*a, **b)
        resp = requests.get(url).json()
        time.sleep(2)
        df = pd.DataFrame(resp)
        dates = df['date'].values
        del df['date']
        cols = df.columns
        df = df.T.values
        return pd.DataFrame(df, index=cols, columns=dates)
    return Solve

def QuoteParse(fun):
    def GTA(*a, **b):
        url = fun(*a, **b)
        resp = requests.get(url).json()
        time.sleep(2)
        stock_price = resp[0]['price']
        market_cap = resp[0]['marketCap']
        shares = int(market_cap / stock_price)
        return stock_price, shares
    return GTA

def RiskFree(xbox):
    def Calculate(*a, **b):
        url = xbox(*a, **b)
        resp = requests.get(url).json()
        time.sleep(2)
        rf = resp[0]['month1'] / 100.0
        return rf
    return Calculate

def ParseStock(ps5):
    def Dealer(*a, **b):
        url = ps5(*a, **b)
        resp = requests.get(url).json()
        time.sleep(2)
        df = pd.DataFrame(resp)[::-1]
        return df
    return Dealer

def key():
    return open('key.txt','r').read()

@QuoteParse
def stock_quote(ticker):
    return f'https://financialmodelingprep.com/stable/quote?symbol={ticker}&apikey={key()}'

@ParseStock
def stock_hist(ticker):
    return f'https://financialmodelingprep.com/stable/historical-price-eod/light?symbol={ticker}&apikey={key()}'

@CleanSheet
def income_statement(ticker):
    return f'https://financialmodelingprep.com/stable/income-statement?symbol={ticker}&period=quarter&apikey={key()}'

@CleanSheet
def balance_sheet(ticker):
    return f'https://financialmodelingprep.com/stable/balance-sheet-statement?symbol={ticker}&period=quarter&apikey={key()}'

@CleanSheet
def cashflow_statement(ticker):
    return f'https://financialmodelingprep.com/stable/cash-flow-statement?symbol={ticker}&period=quarter&apikey={key()}'

@RiskFree
def treasuries():
    return f'https://financialmodelingprep.com/stable/treasury-rates?apikey={key()}'

def ReturnOnEquity(stock, the_dates):
    T0 = time.mktime(datetime.datetime.strptime(the_dates[-1], '%Y-%m-%d').timetuple())
    T1 = T0 - 60*60*24*30*3
    TX = datetime.datetime.fromtimestamp(int(T1)).strftime('%Y-%m-%d')
    the_dates.append(TX)
    A = stock_hist('SPY')
    B = stock_hist(stock)
    rf = treasuries()
    result = []
    for i in range(1, len(the_dates)):
        d0 = the_dates[i-1]
        d1 = the_dates[i]
        x = A[(A['date'] >= d1) & (A['date'] < d0)]
        y = B[(B['date'] >= d1) & (B['date'] < d0)]

        rx = x['price'].pct_change().dropna()
        ry = y['price'].pct_change().dropna()

        covariance = np.cov(rx, ry)
        beta = covariance[0, 1] / covariance[0, 0]

        market_rate = x['price'].iloc[-1] / x['price'].iloc[0] - 1.0

        capm = rf + beta*(market_rate - rf)
        result.append(capm)

    return np.array(result)

stock = input('Enter your stock to be valued: ')
growth = 0.01
tax = 0.25

income = income_statement(stock)
balance = balance_sheet(stock)
cashflow = cashflow_statement(stock)

the_dates = income.columns.tolist()

ebit = income.loc["ebit"]
nopat = ebit*(1 - tax)
da = income.loc["depreciationAndAmortization"]
capex = cashflow.loc["capitalExpenditure"]

current_assets = balance.loc["totalCurrentAssets"]
current_liab = balance.loc["totalCurrentLiabilities"]

nwc = current_assets - current_liab

cash = balance.loc["cashAndCashEquivalents"]

fcf = nopat + da - capex - nwc

E = balance.loc["totalEquity"]
D = balance.loc["totalDebt"]
V = E + D

re = ReturnOnEquity(stock, the_dates)

int_exp = income.loc["interestExpense"]
rd = (int_exp/D)*(1-tax)

wacc = (E/V)*re + (D/V)*rd

fcf = fcf.values
wacc = wacc.values

TV = (fcf[0]*(1+growth))/(wacc[0] - growth)

EV = TV + sum([fcf[t-1]/pow(1+wacc[t-1], t) for t in range(len(wacc), 0, -1)])

Equity = EV - D + cash
Equity = Equity.values

price, shares = stock_quote(stock)

estimated_price = np.max([Equity[0] / shares, 0])

print(f"Stock Price for {stock}: ", price)
print("Estimated Price: ", estimated_price)
print("Value: ", 'Over' if estimated_price < price else 'Under')