import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime
import logging

logger = logging.getLogger()

class Stock:
    def __init__(self, code: str, name: str = None, quot_date=None):
        self.code = code
        self.name = name or code
        self.ticker = yf.Ticker(code)
        self._reference_price = None
        self._hist = None
        self._info = None
        self._financials = None
        self._quarterly_financials = None
        self._balance_sheet = None
        self._cashflow = None
        self._revenue_and_earning = None
        self._quarterly_balance_sheet = None
        self._n_shares = None
        self.is_last = (quot_date is None)
        self.quot_date = quot_date or datetime.now()

    @property
    def info(self):
        if self._info is None:
            self._info = self.ticker.info
        return self._info

    @property
    def financials(self):
        if self._financials is None:
            self._financials = self.ticker.financials.T.sort_index()
        return self._financials

    @property
    def quarterly_financials(self):
        if self._quarterly_financials is None:
            self._quarterly_financials = self.ticker.quarterly_financials.T.sort_index()
        return self._quarterly_financials

    @property
    def balance_sheet(self):
        if self._balance_sheet is None:
            self._balance_sheet = self.ticker.balance_sheet.T.sort_index()
        return self._balance_sheet

    @property
    def quarterly_balance_sheet(self):
        if self._quarterly_balance_sheet is None:
            self._quarterly_balance_sheet = (
                self.ticker.quarterly_balance_sheet.T.sort_index()
            )
        return self._quarterly_balance_sheet

    @property
    def cashflow(self):
        if self._cashflow is None:
            self._cashflow = self.ticker.cashflow.T.sort_index()
        return self._cashflow

    @property
    def revenue_and_earning(self):
        if self._revenue_and_earning is None:
            self._revenue_and_earning = self.ticker.earnings
        return self._revenue_and_earning

    @property
    def n_shares(self):
        if self._n_shares is None:
            try:
                if self.is_last:
                    try:
                        self._n_shares = float(self.get_info("sharesOutstanding"))
                    except:
                        shares = self.ticker.shares
                        self._n_shares = shares.loc[shares.index == (self.quot_date.year - 1)]['BasicShares'].item()
                else:
                    try:
                        shares = self.ticker.shares
                        self._n_shares = shares.loc[shares.index == (self.quot_date.year - 1)]['BasicShares'].item()
                        
                    except:
                        self._n_shares = float(self.get_info("sharesOutstanding"))
            except:
                self._n_shares = np.nan
        return self._n_shares

    @property
    def hist(self):
        if self._hist is None:
            self._hist = self.ticker.history(period="max")
            self._hist.index = self._hist.index.map(lambda x : x.replace(tzinfo=None))
            self._hist = self._hist.loc[self._hist.index <= pd.to_datetime(self.quot_date)]
        return self._hist

    @property
    def dividends(self):
        return self.hist["Dividends"].replace({0: None}).dropna()

    @property
    def annual_dividends(self):
        dividends = self.dividends.reset_index()
        dividends["Year"] = dividends["Date"].dt.year
        return pd.pivot_table(
            dividends, index="Year", values="Dividends", aggfunc=sum
        ).reset_index()

    def get_info(self, label):
        try:
            return  self.info[label]
        except:
            return None
    
    @property
    def reference_price(self):
        if self._reference_price is None:
            if self.is_last and (self.get_info("previousClose") is not None):
                self._reference_price = self.get_info("previousClose")
            else:
                self._reference_price = self.last_before_quot_date(self.hist)['Close']
        return self._reference_price

    @property
    def PB(self):
        return self.reference_price/ self.book_value
    
    @property
    def market_cap(self):
        if self.is_last and (self.get_info("marketCap") is not None):
            return float(self.get_info("marketCap"))
        else:
            return self.reference_price * self.n_shares

    @property
    def price_to_tangible_book(self):
        return (self.total_assets - self.total_liabilities - self.intangible_assets)/self.market_cap
    
    @property
    def PTBV(self):
        return self.price_to_tangible_book
    
    
    @property
    def intangible_assets(self):
        try:
            return self.last_before_quot_date(self.balance_sheet.index)["Intangible Assets"]
        except:
            return 0
    
    @property
    def stockholder_equity(self):
        try:
            if self.is_last:
                return self.last_before_quot_date(self.quarterly_balance_sheet)["Total Stockholder Equity"]
            else:
                return self.last_before_quot_date(self.balance_sheet)["Total Stockholder Equity"]
        except:
            return self.total_assets - self.total_liabilities
            
    @property
    def total_assets(self):
        if self.is_last:
            return self.quarterly_balance_sheet["Total Assets"].values[-1]
        else:
            return self.last_before_quot_date(self.balance_sheet)["Total Assets"]
    
    @property
    def total_liabilities(self):
        if self.is_last:
            return self.quarterly_balance_sheet["Total Liab"].values[-1]
        else:
            return self.last_before_quot_date(self.balance_sheet)["Total Liab"]
 
    @property
    def earning_per_share(self):
        return self.net_income/self.market_cap

    @property
    def PE(self):
        if self.is_last and (self.get_info("trailingPE") is not None):
            pe_yahoo = float(self.get_info("trailingPE"))
            pe_raw = self.market_cap/self.net_income
            if (pe_yahoo > (pe_raw+100)):
                return pe_raw
            else:
                return pe_yahoo
        else:
            return self.market_cap/self.net_income

    @property
    def net_income(self):
        if self.is_last and (self.get_info("netIncomeToCommon") is not None):
            return self.get_info("netIncomeToCommon")
        else:
            return self.last_before_quot_date(self.financials)['Net Income']

    @property
    def graham_price(self):
        squared_graham = 22.5 * self.book_value * self.earning_per_share
        if squared_graham > 0:
            return (squared_graham) ** (1 / 2)
        else:
            return np.nan

    @property
    def ROA(self):
        if self.is_last and (self.get_info("returnOnAssets") is not None):
            return float(self.get_info("returnOnAssets"))
        else:
            return self.net_income/self.total_assets
    
    @property
    def quick_ratio(self):
        if self.is_last and (self.get_info("quickRatio") is not None):
            return float(self.get_info("quickRatio"))
        else:
            return (self.total_current_assets - self.inventory)/self.total_current_liabilities


    @property
    def book_value(self):
        if self.is_last:
            try:
                return float(self.get_info("bookValue"))
            except:
                return self.stockholder_equity/self.n_shares
        else:
            return self.stockholder_equity/self.n_shares

    @property
    def ROE(self):
        return self.return_on_equity

    @property
    def price_to_book(self):
        return self.PB

    @property
    def full_time_employees(self):
        if self.get_info('fullTimeEmployees') is not None:
            return float(self.get_info('fullTimeEmployees'))
        else:
            return np.nan

    @property
    def return_on_equity(self):
        if self.is_last:
            try:
                return float(self.get_info("returnOnEquity"))
            except Exception as e:
                logger.warn(f'{e} : {e.__doc__}')
                return self.net_income/self.stockholder_equity
        else:
            return self.net_income/self.stockholder_equity
    
    @property
    def total_current_assets(self):
        return self.last_before_quot_date(self.balance_sheet)["Total Current Assets"]
 
    @property
    def inventory(self):
        try:
            return self.last_before_quot_date(self.balance_sheet)["Inventory"]
        except:
            return 0 #Insurance and banks do not have inventory

    @property
    def working_capital_per_share(self):
        return (self.total_current_assets - self.total_current_liabilities) / self.n_shares

    @property
    def total_current_liabilities(self):
        if self.is_last:
            return self.last_before_quot_date(self.balance_sheet["Total Current Liabilities"])
        else:
            
            return self.last_before_quot_date(self.quarterly_balance_sheet)["Total Current Liabilities"]

    @property
    def net_current_assets_per_share(self):
        return (self.total_current_assets - self.total_liabilities) / self.n_shares

    @property
    def total_debt(self):
        if self.is_last and (self.get_info("totalDebt") is not None):
            return self.get_info("totalDebt")
        else:
            return self.last_before_quot_date(self.balance_sheet)[['Long Term Debt', 'Total Current Liabilities']].sum()

    @property
    def net_cash_per_share(self):
        return (self.cash - self.total_debt) / self.n_shares

    @property
    def cash(self):
        if self.is_last and (self.get_info("totalCash") is not None):
            return self.get_info("totalCash")
        else:
            return self.last_before_quot_date(self.balance_sheet)['Cash']


    @property
    def payout_ratio(self):
        try:
            return  self.last_dividend / self.EPS
        except:
            return np.nan

    @property
    def last_dividend(self):
        if self.is_last and (self.get_info("dividendRate") is not None):
            return  self.get_info("dividendRate")
        elif len(self.annual_dividends):
            return self.annual_dividends.tail(1)['Dividends'].item()
        else:
            return 0


    @property
    def dividend_yeld(self):
        return  self.last_dividend/self.reference_price

    @property
    def operating_cash_flow(self):
        if self.is_last and (self.get_info("operatingCashflow") is not None) :
            return np.float(self.get_info("operatingCashflow"))
        else:
            return np.float( self.last_before_quot_date(self.cashflow)["Total Cash From Operating Activities"])

    @property
    def price_to_cash_flow(self):
        try:
            return self.market_cap/ self.operating_cash_flow
        except:
            return np.nan
 
    @property
    def price_to_free_cash_flow(self):
        return self.market_cap / self.free_cash_flow

    @property
    def free_cash_flow(self):
        if self.is_last and (self.get_info("freeCashflow") is not None):
            return np.float(self.get_info("freeCashflow"))
        else:
            return self.operating_cash_flow - self.capital_expenditures

    @property
    def capital_expenditures(self):
        return self.last_before_quot_date(self.cashflow)["Capital Expenditures"]
 
    @property
    def revenue(self):
        if self.is_last and (self.get_info("totalRevenue") is not None):
            return self.get_info("totalRevenue")
        else:
            return self.last_before_quot_date(self.financials)["Total Revenue"]
 
    @property
    def net_income_per_employee(self):
        return self.net_income/self.full_time_employees

    @property
    def revenue_per_employee(self):
        return  self.revenue/self.full_time_employees
    @property
    def earning_per_share(self):
        return  self.net_income/self.n_shares     

    @property
    def EPS(self):
        return self.earning_per_share

    @property
    def ROCE(self):
        return self.EBIT/(self.total_assets - self.total_current_liabilities)

    @property
    def EBIT(self):
        return self.last_before_quot_date(self.financials)["Ebit"]

    @staticmethod
    def last_before(df, date):
        return df.loc[df.index < date].iloc[-1]

    def last_before_quot_date(self, df):
        return self.last_before(df, self.quot_date)