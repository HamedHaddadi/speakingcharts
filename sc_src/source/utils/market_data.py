import pandas as pd
import pandas_datareader.data as web
from pandas_datareader.nasdaq_trader import get_nasdaq_symbols 
import yfinance as yf 
import requests 
import re 
#from bs4 import BeautifulSoup
from . import tools    
from . import keys 
from datetime import date, datetime
import time 
import re 
#import fitz 
from os import path 
# ...

def get_sp500_fred(start = None, end = None):
    start = tools.to_date(start)
    if end is None:
        end = date.today()
    else:
        end = tools.to_date(end)
    return web.DataReader(['sp500'], 'fred', start, end)

def get_sp500_yfinance(start = None, end = None):
    sp = yf.download(tickers = '^GSPC', start = start, end = end, interval = '1d')
    return pd.DataFrame(sp['Close'].rename('sp500'))

def get_sp500(start = None, end = None, source = 'Fred'):
    return {'fred': get_sp500_fred, 
                'yahoo': get_sp500_yfinance}[source](start = start, end = end)

# ########################################### #
# useful functions to pull sp500 data
# ########################################### #
def pull_sp500_tickers():
    companies = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
    return companies['Symbol'].tolist() 

def parse_row(row, asset_fund = None):
    """
    asset_fund is a dictionary
    takes rows from BeautifulSoup and returns asset_fund(amentals) dictionary
    """
    row_list = [td.text for td in row.select('td')]
    len_list = len(row_list)
    for index in range(len_list//2):
        ent = row_list[2*index]
        key = None 
        if 'P/E' in ent:
            key = 'P/E'
        elif 'EPS (ttm)' in ent:
            key = 'EPS-ttm'
        elif 'Shs Outstand' in ent:
            key = 'Shares Outstanding'
        elif 'Market Cap' in ent:
            key = 'Market Cap'
        elif 'Shs Float' in ent:
            key = 'Floating Shares'
        elif 'PEG' in ent:
            key = 'PEG'
        elif 'P/S' in ent:
            key = 'P/S'
        elif 'Book/sh' in ent:
            key = 'Book/Share Ratio'
        elif 'ROA' in ent:
            key = 'ROA'
        elif 'Dividend' in ent and '%' not in ent:
            key = 'Dividend $'
        elif 'Dividend %' in ent:
            key = 'Dividend %'
        elif 'Debt/Eq' in ent:
            key = 'D/E'
        if key is not None:
            index_value = row_list[2*index + 1]
            if 'B' in index_value:
                factor = 10**9 
            elif 'M' in index_value:
                factor = 10**6
            else:
                factor = 1
            values = re.findall(r'[-+]?\d*\.?\d+|[-+]?\d+', index_value) 
            if len(values) > 0:
                asset_fund[key] = float(values[0])*factor 
    return asset_fund 
        
# def pull_fundamentals_finviz(stock_list = None):
#     if 'sp500' in stock_list:
#         _,stock_list = pull_sp500_tickers()
#     else:
#         raise Exception('stock list is None')

#     total_length = len(stock_list)
#     BATCH_SIZE = 4
#     stock_batch = tools.batched(stock_list, BATCH_SIZE)
#     url_base = 'https://finviz.com/quote.ashx?t='
#     request_headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:76.0) Gecko/20100101 Firefox/76.0'}

#     list_df = []
#     downloaded = 0 
#     for tickers in stock_batch:
#         time.sleep(20)
#         print(f'start downloading {tickers} after the pause; {downloaded} out of {total_length} so far')
#         for ticker in tickers:
#             asset_url = url_base + ticker  
#             html_soup = BeautifulSoup(requests.get(asset_url, headers = request_headers).content, 'html.parser')
#             asset_fund = {'P/E': None, 'EPS-ttm': None, 'Shares Outstanding': None, 
#                 'Market Cap': None, 'Floating Shares': None, 
#                         'PEG': None, 'P/S': None, 'Book/Share Ratio': None, 
#                             'ROA': None, 'Dividend $': None, 'Dividend %': None, 
#                                 'D/E': None, 'Stock': ticker}
        
#             for row in html_soup.select('.snapshot-table2 tr'):
#                 asset_fund = parse_row(row, asset_fund=asset_fund)
        
#             asset_df = pd.DataFrame([asset_fund])
#             if list(asset_df.columns) == list(asset_fund.keys()):
#                 list_df.append(asset_df)
#         downloaded += len(list_df)*BATCH_SIZE
#     list_df = pd.concat(list_df)
#     save_name = 'list_of_stocks_fundamentals_from_finviz_on_' + datetime.now().strftime('%Y-%m-%d-%H-%M') + '.csv'
#     list_df.to_csv(path.join(keys.DATA_PATH, save_name), sep = ',', header = True, index = False, float_format = '%.4f')

# def pull_fundamentals(source = 'finviz', stock_list = None):
#     {'finviz': pull_fundamentals_finviz}[source](stock_list = stock_list)


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


# ######### Useful methods for the list of Russel3000 ########### #
# def generate_russell3000_companies():
#     """
#     generates a dataframe of company name - ticker symbol for Russell3000
#     """
#     ru3000 = fitz.open(keys.RUSSELL3000_PDF)
#     text = []
#     for num in range(ru3000.page_count):
#         text.extend(ru3000.load_page(num).get_text('text').splitlines())
#     not_include = ['Russell US Indexes', 'Russell 3000® Index ', 'Membership list', 'Ticker', 'Company', 'June 24, 2022']
#     companies = {'companies': [], 'tickers': []}
#     for count, elem in enumerate(text):
#         if 'ftserussell.com' in elem:
#             break
#         if (len(elem.split(' ')) > 1 or bool(re.search(r'\d', elem)) or len(elem) > 4) and (elem.strip() not in not_include):
#             companies['companies'].append(elem)
#             companies['tickers'].append(text[count + 1])
#     comp_df = pd.DataFrame.from_dict(companies)
#     comp_filename = 'Russell3000_Companies.csv'
#     comp_df.to_csv(path.join(keys.DATA_PATH, comp_filename), sep = ',', header = True, index = False)
        

    



    





