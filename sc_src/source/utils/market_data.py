import pandas as pd
import pandas_datareader.data as web
import yfinance as yf 
from . import tools    
from . import keys 
from datetime import date, datetime
from os import path 
# ...

def get_sp500_fred(start = None, end = None):
    start = tools.to_date(start)
    if end is None:
        end = date.today()
    else:
        end = tools.to_date(end)
    return web.DataReader(['sp500'], 'fred', start, end).rename('index_value')

def get_sp500_yfinance(start = None, end = None):
    sp = yf.download(tickers = '^GSPC', start = start, end = end, interval = '1d')
    return pd.DataFrame(sp['Close'].rename('index_value'))

def get_sp500(start = None, end = None, source = 'Fred'):
    return {'fred': get_sp500_fred, 
                'yahoo': get_sp500_yfinance}[source](start = start, end = end)

def get_spxew_yfinance(start = None, end = None):
    sp_ew = yf.download(tickers = '^SPXEW', start = start, end = end, interval = '1d')
    return pd.DataFrame(sp_ew['Close'].rename('index_value'))

# ########################################### #
# useful functions to pull sp500 data
# ########################################### #
def pull_sp500_tickers():
    companies = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
    return companies['Symbol'].tolist() 

# ### 		Data Frame Tools 		### #
# 	generate fundamentals from file		#
# ##################################### #
def generate_fundamentals_from_file(filename, sp = False):
    fund_df = pd.read_csv(path.join(keys.DATA_PATH, filename), sep = ',', header = 0)
    # market caps: individual stocks; will be used to compute sector market cap df for pie charts 
    market_cap_df = fund_df[~fund_df['Market Cap'].isnull().values][['Market Cap','Stock']]
    # pe_ratio: will be used to generate individual bar charts
    pe_df = fund_df[~fund_df['P/E'].isnull().values][['P/E','Stock']]
    # dividend %
    divid_df = fund_df[~fund_df['Dividend %'].isnull().values][['Dividend %','Stock']]
    prefix = {True:'sp500_', False:''}[sp]
    if sp:
	    market_cap_df, pe_df, divid_df = sp_sector(market_cap = market_cap_df, pe = pe_df, dividend = divid_df)
    
    pe_filename = prefix + "pe_ratios_on_" + datetime.now().strftime('%Y-%m-%d-%H-%M') + '.csv'
    pe_df.to_csv(path.join(keys.DATA_PATH, pe_filename), sep = ',', header = True, index = False)
    divid_filename = prefix + 'dividend_percent_on_' + datetime.now().strftime('%Y-%m-%d-%H-%M') + '.csv'
    divid_df.to_csv(path.join(keys.DATA_PATH, divid_filename), sep = ',', header = True, index = False)
    cap_filename = prefix + 'market_caps_on_' + datetime.now().strftime('%Y-%m-%d-%H-%M') + '.csv'
    market_cap_df.to_csv(path.join(keys.DATA_PATH, cap_filename), sep = ',', header = True, index = False)   

# sp500 specific methods 
def sp_sector(market_cap = None, pe = None, dividend = None):
    sectors,_ = pull_sp500_tickers()
    sector_cap = {}

    for sector in sectors.keys():
	    sector_cap[sector] = market_cap[market_cap['Stock'].isin(sectors[sector])]['Market Cap'].sum()	
    
    for sector,stocks in sectors.items():
        pe.loc[pe[pe['Stock'].isin(stocks)].index, 'Sector'] = sector 
        dividend.loc[dividend[dividend['Stock'].isin(stocks)].index, 'Sector'] = sector 
        market_cap.loc[market_cap[market_cap['Stock'].isin(stocks)].index, 'Sector'] = sector 
        pe.sort_values('Sector', inplace = True)
        dividend.sort_values('Sector', inplace = True)
        market_cap.sort_values('Sector', inplace = True)

    sector_cap_df = pd.DataFrame.from_dict(sector_cap, orient = 'index', columns = ['Market Cap']).reset_index().rename({'index':'Sector'}, axis = 'columns')
    file_name = 'sp500_sector_market_cap_on_' + datetime.now().strftime('%Y-%m-%d-%H-%M') + '.csv'
    sector_cap_df.to_csv(path.join(keys.DATA_PATH, file_name), sep = ',', header = True, index = False)
    return market_cap, pe, dividend 


