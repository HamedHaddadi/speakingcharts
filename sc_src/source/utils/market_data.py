import pandas as pd
import pandas_datareader.data as web
import yfinance as yf 
from . import tools    
from . import keys 
from datetime import date, datetime
from os import path 
# ...

YFINANCE_ASSETS = {
      'SP500':'^GSPC',
      'SP500 Equal Weight': '^SPXEW',
      'DowJones':'^DJI',
      'Nasdaq':'^IXIC',
      'NYSE COMPOSITE (DJ)':'^NYA',
      'NYSE AMEX COMPOSITE INDEX':'^XAX',
      'Cboe UK 100':'^BUK100P',
      'Russell2000':'^RUT',
      'Russell3000': '^RUA',
      'CBOE Volatility Index':'^VIX',
      'FTSE 100':'^FTSE',
      'DAX PERFORMANCE-INDEX':'^GDAXI',
      'CAC 40':'^FCHI',
      'ESTX 50 PR.EUR':'^STOXX50E',
      'Euronext 100 Index':'^N100',
      'BEL 20':'^BFX',
      'Nikkei 225':'^N225',
      'SSE Composite Index':'000001.SS',
      'STI Index':'^STI',
      'SP ASX 200':'^AXJO',
      'SP BSE SENSEX':'^BSESN',
}

def get_yfinance_index(index: str, start: str = '1960-01-01',
                     end: str = date.today().strftime('%Y-%m-%d')) -> pd.DataFrame:
    start = tools.to_date(start)
    end = tools.to_date(end)
    if index in YFINANCE_ASSETS.keys():
        return yf.download(YFINANCE_ASSETS[index], start = start, end = end)
    else:
        raise KeyError(f'index {index} not found in YFinance asset list')

# ###### #
FRED_ASSETS = {
    'median_house_price':'MSPUS',
    'used_cars':'CUSR0000SETA02',
    'global_all_commodities':'PALLFNFINDEXQ',
    'global_copper':'PCOPPUSDM',
    'spot_crude':'WTISPLC',
    'global_brent_crude':'POILBREUSDM',
    'global_raw_materials':'PRAWMINDEXM',
    'global_energy':'PNRGINDEXM',
    'global_iron_ore':'PIORECRUSDM',
    'eggs':'APU0000708111',
    'corn':'PMAIZMTUSDM',
    'global_aluminum':'PALUMUSDM',
    'global_uranium':'PURANUSDM',
    'global_cotton':'PCOTTINDUSDM',
    'us_diesel':'GASDESW',
    'milk':'APU0000709112',
    'global_rice':'PRICENPQUSDM',
    'global_beef':'PBEEFUSDQ',
    'jet_fuel':'DJFUELUSGULF',
    'global_sugar':'PSUGAISAUSDM',
    'coffee':'PCOFFOTMUSDM',
    'global_nickel':'PNICKUSDM',
    'us_gasoline':'APU000074714',
    'global_poultry':'PPOULTUSDM',
    'global_industrial_metals':'PINDUINDEXM',
    'us_flour':'APU0000701111',
    'global_food':'PFOODINDEXM',
    'global_swine':'PPORKUSDM',
    'us_tomatoes':'APU0000712311',
    'lumber':'WPU081',
    'real_median_personal_income':'MEPAINUSA672N',
    '30_year_fixed_mortgage_rates':'MORTGAGE30US',
    'gdp':'GDP',
    'fed_funds_rate':'FEDFUNDS',
    'case_shiller_us_home_index':'CSUSHPINSA',
    'median_household_income':'MEHOINUSA672N',
    'us_house_sales_price':'ASPUS',
    'corporate_bond_yield':'AAA',
    'personal_consumption_expenditures':'PCE',
    'us_industrial_production':'INDPRO',
    'ppi_all_commodities':'PPIACO',
    'us_average_hourly_earnings':'CES0500000003',
    'commercial_industrial_loans':'BUSLOANS',
    'real_disposable_income':'DSPIC96',
    'deposits_all_commercial_banks':'DPSACBW027SBOG',
    'us_home_ownership_rate':'RHORUSQ156N',
    'housing_units_authorized':'PERMIT',
    'loans_leases_bank_credit':'TOTLLNSA',
    'credit_card_delinquency_rate':'DRCCLACBS',
    'disposable_income_per_capita':'A229RX0',
    'personal_income':'PI',
    'poplulation':'POPTHM',
    'global_copper':'PCOPPUSDM',
    'personal_consumption_expenditures_durable_goods':'PCEDG',
    'gross_national_product':'GNP',
    'total_net_worth_top_one_precent':'WFRBST01134',
    'us_new_single_family_houses':'HSN1F',
    'us_trade_balance':'BOPGSTB',
    'vix':'VIXCLS',
    'yield_10_year_treasury':'DGS10',
    'nonfarm_payroll':'PAYEMS',
    'unemployment_rate':'UNRATE',
    # monaey supplies
    'm2':'M2SL',
    'm3':'MABMM301USM189S',
    'total_public_debt':'GFDEBTN',
    'monetary_base':'BOGMBASE',
    'currency_in_circulation':'CURRCIR',
    'm1':'M1SL',
    'real_m2_money_stock':'M2REAL',
    'fed_mbs':'WSHOMCB',
    'fed_total_assets':'WALCL',
    }


def get_fed_asset(asset: str, start = None, end = date.today()):
    if asset not in FRED_ASSETS.keys():
        raise KeyError(f'asset {asset} does not exist in FRED assets')
    start = tools.to_date(start)
    end = tools.to_date(end)
    return web.DataReader([FRED_ASSETS[asset]], 'fred', start, end).rename(columns = {FRED_ASSETS[asset]: asset}).dropna()


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


