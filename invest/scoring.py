import pandas as pd
from invest.fundamental_analysis import main_fundamental_indicators
from invest.technical_analysis import detect_trend


def compute_score(indicatori : pd.DataFrame):
    indicatori['score_NIPE'] = score_NIPE(indicatori['Net income per employee'])
    indicatori['score_PE'] = score_PE(indicatori['PE'])
    indicatori['score_QR'] = score_QR(indicatori['Quick Ratio'])
    indicatori['score_TREND'] = score_TREND(indicatori['trend_magnitude'])
    indicatori['score_PB'] = score_PB(indicatori['PB'])
    indicatori['score_DIVIDEND'] = score_dividend(indicatori['Dividend yeld'], 
                                                  indicatori['#div_past20y'],
                                                  indicatori['Payout Ratio'])
    indicatori['score_GRAHAM'] = score_graham(indicatori['price_over_graham'])
    indicatori['score_ROA'] = score_ROA(indicatori['Return on Assets'])
    indicatori['score_ROE'] = score_ROE(indicatori['ROE'])
    indicatori['score_NCAPSOP'] = score_NCAPSOP(indicatori['Net current asset per share over price'])
    
    n_scores = len(indicatori.filter(like='score').columns)

    indicatori['OVERALL_SCORE'] = indicatori.filter(like='score').sum(axis=1)/n_scores

    return indicatori.sort_values(by='OVERALL_SCORE', ascending=False)


def get_indicators(stock):
    trend_magnitude, last_value_trendline = detect_trend(stock, verbose=0)
    tmp = main_fundamental_indicators(stock)
    tmp['trendline'] = last_value_trendline

    tmp['trend_magnitude'] = trend_magnitude
    tmp['price_over_trend'] = (tmp['Reference Price'])/last_value_trendline
    tmp['sector'] = stock.get_info('sector')
    tmp['description'] = stock.get_info('longBusinessSummary')
    tmp['#div_past20y'] = years_of_dividend_payments(stock)
    return tmp

def years_of_dividend_payments(mystock):
    tmp_div_df = pd.DataFrame()
    mydate = mystock.quot_date
    tmp_div_df['Year'] = list(range(mydate.year-20, mydate.year))
    dividends_df = mystock.annual_dividends.copy().merge(tmp_div_df)
    return len(dividends_df)

def score_PE(PE):
    tmp_df = pd.DataFrame()
    tmp_df['PE'] = PE
    tmp_df['score_PE'] = 1
    tmp_df.loc[tmp_df['PE'].isna(), 'score_PE'] = 0
    tmp_df.loc[tmp_df['PE'] < 17.5, 'score_PE'] = 2 
    tmp_df.loc[tmp_df['PE'] < 15, 'score_PE'] = 3
    tmp_df.loc[tmp_df['PE'] < 12, 'score_PE'] = 4
    tmp_df.loc[tmp_df['PE'] < 10, 'score_PE'] = 5
    return tmp_df['score_PE']

def score_QR(qr):
    tmp_df = pd.DataFrame()
    tmp_df['QR'] = qr
    tmp_df['score_QR'] = 0
    tmp_df.loc[tmp_df['QR'].isna(), 'score_QR'] = 0
    tmp_df.loc[tmp_df['QR'] < 0.8, 'score_QR'] = 1
    tmp_df.loc[(tmp_df['QR'] < 1) & 
               (tmp_df['QR'] > 0.8) , 'score_QR'] = 2
    tmp_df.loc[(tmp_df['QR'] > 1) & 
               (tmp_df['QR'] < 1.2) , 'score_QR'] = 3
    tmp_df.loc[(tmp_df['QR'] > 1.2) & 
               (tmp_df['QR'] < 2) , 'score_QR'] = 3
    
    tmp_df.loc[tmp_df['QR'] > 2, 'score_QR'] = 5
    return tmp_df['score_QR']

def score_PB(PB):
    tmp_df = pd.DataFrame()
    tmp_df['PB'] = PB
    tmp_df['score_PB'] = 0
    tmp_df.loc[tmp_df['PB'].isna() | (tmp_df['PB'] < 0), 'score_PB'] = 0
    tmp_df.loc[(tmp_df['PB'] > 3), 'score_PB'] = 1 
    tmp_df.loc[((tmp_df['PB'] < 3) & (tmp_df['PB'] > 2)), 'score_PB'] = 2
    tmp_df.loc[(tmp_df['PB'] < 2) & (tmp_df['PB'] > 1), 'score_PB'] = 4
    tmp_df.loc[(tmp_df['PB'] < 1)& (tmp_df['PB'] > 0), 'score_PB'] = 5
    return tmp_df['score_PB']

def score_TREND(trend):
    tmp_df = pd.DataFrame()
    tmp_df['TREND'] = trend
    tmp_df['score_TREND'] = 0
    tmp_df.loc[(tmp_df['TREND'] > 0), 'score_TREND'] = 1
    tmp_df.loc[(tmp_df['TREND'] > 0.5), 'score_TREND'] = 3
    tmp_df.loc[(tmp_df['TREND'] > 1), 'score_TREND'] = 5
    
    return tmp_df['score_TREND']


def score_NIPE(IPE):
    tmp_df = pd.DataFrame()
    tmp_df['IPE'] = IPE
    
    best_decile = tmp_df['IPE'].quantile(0.90)
    
    tmp_df['score_NIPE'] = None
    tmp_df.loc[tmp_df['IPE'].isna() | (tmp_df['IPE'] < 0), 'score_NIPE'] = 0

    tmp_df.loc[(tmp_df['IPE'] > 0) & 
               (tmp_df['IPE'] < best_decile), 'score_NIPE'] = 5*tmp_df['IPE']/best_decile

    tmp_df.loc[(tmp_df['IPE'] >= best_decile), 'score_NIPE'] = 5
    
    return tmp_df['score_NIPE'] 

  
def score_dividend(div, years, payout):
    tmp_df = pd.DataFrame()
    tmp_df['dividend'] = div
    tmp_df['years'] = years
    tmp_df['payout'] = payout
    tmp_df['score_DIVIDEND'] = 0
    tmp_df.loc[(tmp_df['dividend'] > 0), 'score_DIVIDEND'] = 1
    tmp_df.loc[(tmp_df['dividend'] > 0) & 
               (tmp_df['payout'] > 0), 'score_DIVIDEND'] = 2
    tmp_df.loc[(tmp_df['dividend'] > 0) & 
               (tmp_df['payout'] < 0.7), 'score_DIVIDEND'] = 3 + tmp_df['years']/10
    return tmp_df['score_DIVIDEND']  

def score_graham(price_over_graham):
    tmp_df = pd.DataFrame()
    tmp_df['graham'] = price_over_graham
    tmp_df['score_GRAHAM'] = None
    tmp_df.loc[tmp_df['graham'].isna(), 'score_GRAHAM'] = 0
    tmp_df.loc[(tmp_df['graham'] > 2) , 'score_GRAHAM'] = 1
    tmp_df.loc[((tmp_df['graham'] > 1.5) & 
                (tmp_df['graham'] < 2)) , 'score_GRAHAM'] = 2
    tmp_df.loc[((tmp_df['graham'] > 1.1) & 
                (tmp_df['graham'] < 1.5)) , 'score_GRAHAM'] = 3
    tmp_df.loc[((tmp_df['graham'] > 1) & 
                (tmp_df['graham'] < 1.1)) , 'score_GRAHAM'] = 4
    tmp_df.loc[tmp_df['graham'] < 1, 'score_GRAHAM'] = 5
    return tmp_df['score_GRAHAM']  

def score_ROA(ROA):
    tmp_df = pd.DataFrame()
    tmp_df['ROA'] = ROA
    tmp_df['score_ROA'] = None
    tmp_df.loc[tmp_df['ROA'].isna() |
              (tmp_df['ROA'] < 0), 'score_ROA'] = 0
    tmp_df.loc[tmp_df['ROA'] > 0 |
              (tmp_df['ROA'] < 0.2), 'score_ROA'] = 5*tmp_df['ROA']/0.2
    tmp_df.loc[((tmp_df['ROA'] >= 0.2)), 'score_ROA'] = 5
    return tmp_df['score_ROA']  


def score_ROE(ROE):
    tmp_df = pd.DataFrame()
    tmp_df['ROE'] = ROE
    tmp_df['score_ROE'] = None
    tmp_df.loc[tmp_df['ROE'].isna() |
              (tmp_df['ROE'] < 0), 'score_ROE'] = 0
    tmp_df.loc[tmp_df['ROE'] > 0 |
              (tmp_df['ROE'] < 0.2), 'score_ROE'] = 5*tmp_df['ROE']/0.2
    tmp_df.loc[((tmp_df['ROE'] >= 0.2)), 'score_ROE'] = 5
    return tmp_df['score_ROE'] 



def score_NCAPSOP(NCAPSOP):
    tmp_df = pd.DataFrame()
    tmp_df['NCAPSOP'] = NCAPSOP
    tmp_df['score_NCAPSOP'] = None
    tmp_df.loc[tmp_df['NCAPSOP'].isna(), 'score_NCAPSOP'] = 0
    tmp_df.loc[tmp_df['NCAPSOP'] < -10, 'score_NCAPSOP'] = 1
    tmp_df.loc[((tmp_df['NCAPSOP'] > -10) & 
                (tmp_df['NCAPSOP'] < -5)), 'score_NCAPSOP'] = 2
    tmp_df.loc[((tmp_df['NCAPSOP'] > -5) & 
                (tmp_df['NCAPSOP'] < -1)), 'score_NCAPSOP'] = 3
    tmp_df.loc[((tmp_df['NCAPSOP'] > -1) & 
                (tmp_df['NCAPSOP'] < 0)), 'score_NCAPSOP'] = 4
    tmp_df.loc[((tmp_df['NCAPSOP'] > 0)), 'score_NCAPSOP'] = 5
    return tmp_df['score_NCAPSOP'] 