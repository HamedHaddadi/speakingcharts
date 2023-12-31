
# ###################################### #
# Contains text parsers and functions	 #
# that are not often used in the online  #
# codebase								 #
# ###################################### #
import fitz 
import re 
import requests 
import pandas as pd 
from . import keys, tools 
from bs4 import BeautifulSoup
#from pandas_datareader.nasdaq_trader import get_nasdaq_symbols 
from datetime import date, datetime  
from os import path 

# ############## Nasdaq List of Companies ################# #
def generate_nasdaq_companies():
    """
    generates a dataframe of Nasdaq Companies; column names are:
        Company, Symbol, GIGS Sector GICS Sub-Industry 
    """
    url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
    headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0',
                    'Accept': 'application/json',
                        'Accept-Language': 'en-US,en;q=0.5'}
    try:
        response = requests.get(url, headers = headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        tables = soup.find_all('table')
        nasdaq_df = pd.read_html(str(tables))[4]
        nasdaq_df.rename(columns = {'Ticker':'Symbol'}, inplace = True)
        nasdaq_df.to_csv(path.join(keys.DATA_PATH, 'Nasdaq_Companies.csv'), sep = ',', header = True, index = False)
    except Exception as ex:
        print(f'Did not pull Nasdaq company information {type(ex).__name__}')   

def generate_russell3000_companies():
    """
    generates a dataframe of company name - ticker symbol for Russell3000
    """
    ru3000 = fitz.open(keys.RUSSELL3000_PDF)
    text = []
    for num in range(ru3000.page_count):
        text.extend(ru3000.load_page(num).get_text('text').splitlines())
    not_include = ['Russell US Indexes', 'Russell 3000® Index ', 'Membership list', 'Ticker', 'Company', 'June 24, 2022']
    companies = {'companies': [], 'tickers': []}
    for count, elem in enumerate(text):
        if 'ftserussell.com' in elem:
            break
        if (len(elem.split(' ')) > 1 or bool(re.search(r'\d', elem)) or len(elem) > 4) and (elem.strip() not in not_include):
            companies['companies'].append(elem)
            companies['tickers'].append(text[count + 1])
    comp_df = pd.DataFrame.from_dict(companies)
    comp_filename = 'Russell3000_Companies.csv'
    comp_df.to_csv(path.join(keys.DATA_PATH, comp_filename), sep = ',', header = True, index = False)

# ####### finviz fundamental reader ######### #
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
        
def pull_fundamentals_finviz(stock_list = None):
     
     total_length = len(stock_list)
     BATCH_SIZE = 4
     stock_batch = tools.batched(stock_list, BATCH_SIZE)
     url_base = 'https://finviz.com/quote.ashx?t='
     request_headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:76.0) Gecko/20100101 Firefox/76.0'}

     list_df = []
     downloaded = 0 
     for tickers in stock_batch:
         time.sleep(20)
         print(f'start downloading {tickers} after the pause; {downloaded} out of {total_length} so far')
         for ticker in tickers:
             asset_url = url_base + ticker  
             html_soup = BeautifulSoup(requests.get(asset_url, headers = request_headers).content, 'html.parser')
             asset_fund = {'P/E': None, 'EPS-ttm': None, 'Shares Outstanding': None, 
                 'Market Cap': None, 'Floating Shares': None, 
                         'PEG': None, 'P/S': None, 'Book/Share Ratio': None, 
                             'ROA': None, 'Dividend $': None, 'Dividend %': None, 
                                 'D/E': None, 'Stock': ticker}
        
             for row in html_soup.select('.snapshot-table2 tr'):
                 asset_fund = parse_row(row, asset_fund=asset_fund)
        
             asset_df = pd.DataFrame([asset_fund])
             if list(asset_df.columns) == list(asset_fund.keys()):
                 list_df.append(asset_df)
         downloaded += len(list_df)*BATCH_SIZE
     list_df = pd.concat(list_df)
     save_name = 'list_of_stocks_fundamentals_from_finviz_on_' + datetime.now().strftime('%Y-%m-%d-%H-%M') + '.csv'
     list_df.to_csv(path.join(keys.DATA_PATH, save_name), sep = ',', header = True, index = False, float_format = '%.4f')

def pull_fundamentals(source = 'finviz', stock_list = None):
    {'finviz': pull_fundamentals_finviz}[source](stock_list = stock_list)
