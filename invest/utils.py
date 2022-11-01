import os
from functools import reduce
from sklearn.metrics import mean_squared_error
import numpy as np

import pandas as pd
import yaml


def file_folder_exists(path: str):
    """
    Return True if a file or folder exists.
    :param path: the full path to be checked
    :type path: str
    """
    try:
        os.stat(path)
        return True
    except:
        return False


def select_or_create(path: str):
    """
    Check if a folder exists. If it doesn't, it create the folder.
    :param path: path to be selected
    :type path: str
    """
    if not file_folder_exists(path):
        os.makedirs(path)
    return path


def merge_dataframe(data_frames):
    return reduce(lambda left, right: pd.merge(left, right, how="outer"), data_frames)

def fundamental_indicator(stock):
    score = pd.DataFrame()
    score["code"] = [stock.code]
    score["Date"] = [stock.quot_date]
    
    score["Reference Price"] = [stock.reference_price]
    score["Graham Price"] = [stock.graham_price]

    score["Last Closing Price"] = [stock.hist['Close'].values[-1]]
    score["price_over_graham_number"] = [stock.reference_price/stock.graham_price]
    score["Net current asset per share over price"] = [stock.net_current_assets_per_share/stock.reference_price]

    score["PE ratio"] = [stock.PE]
    score["Return On Equity"] = [stock.ROE]
    score["PB ratio"] = [stock.PB]
    score["Tangible PB ratio"] = [stock.price_to_tangible_book]
    score["Return on Assets"] = [stock.ROA]
    score["Dividend yeld"] = [stock.dividend_yeld]
    score["Payout Ratio"] = [stock.payout_ratio]
    score["Quick Ratio"] = [stock.quick_ratio]
    score["Price to cash flow"] = [stock.price_to_cash_flow]
    score["Price to free cash flow"] = [stock.price_to_free_cash_flow]
    score['Working capital over market cap'] = [stock.working_capital_per_share/stock.reference_price]
    score['Net cash over market cap'] = [stock.net_cash_per_share/stock.reference_price]
    score['EPS over price'] = [stock.EPS/stock.reference_price]
    score['ROCE'] = [stock.ROCE]
    score['Net income per employee'] = [stock.net_income_per_employee]
    score['Revenue per employee'] = [stock.revenue_per_employee]
    return score



def rmse(y_true, y_pred):
    return np.sqrt(mean_squared_error(y_true, y_pred))