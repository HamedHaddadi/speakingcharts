
import pandas as pd
import numpy as np
import pickle 
from os import path 
from datetime import datetime
import yfinance as yf 
from . securities import Stock
from .. utils.market_data import pull_sp500_tickers 
from .. utils import keys,tools 

# ####################### #
# Base class              #
# ####################### #
class Index:
    """
    class to analyze SP500 & RUSSELL3000 stocks
    assets is a dictionary of Stock objects
    sectors: a dictionary of tickers with sectors as keys 
    all calculations are performed on all stocks in the index
    """
    list_of_assets = None
    # list of keys for loading files 
    assets_filename = None
    sector_filename = None 
    assets_info_filename = None 
    sector_long_filename_m = None 
    sector_long_filename_q = None 
    sector_fundamentals_filename = None 
    index_fundamentals_filename = None 

    fundamentals_keys = ['Market Cap', 'P/E(TTM)', 'Dividend %'] 
    current_time = datetime.now().strftime('%Y-%m-%d-%H-%M')  

    def __init__(self, assets = {}, sectors = None, date_range = None, assets_info = None):
        """
        assets in a dictionary of {ticker symbol: Stock object}
        sectors is a dictionary of {sector:[ticker]}
        date_range is the minimum and maximum datetime.date in the entire list of assets
        assets_info: is a dataframe of ['company name','ticker','sector'] columns 
        """
        self.assets = assets
        self.assets_info = assets_info
        self.num_assets = len(self.assets.keys())
        self.sectors = sectors
        self.period_cumulative_returns = None 
        # dictionary of values
        self.capital_gains = {}
        # best performing assets based on cumulative returns 
        self.best_performing = {key:[] for key in self.sectors.keys()}
        self.date_range = self._set_date_range(date_range = date_range) 
        # long format dataframes
        # monthly sampling 
        self.sector_mean_return_long_m = None
        # quarterly sampling 
        self.sector_mean_return_long_q = None 
        self.sector_fundamentals = None 
        self.fundamentals = None 
    
    # helper methods
    @staticmethod 
    def _sort_dict(this_dict, high_to_low = True):
        this_dict = {key:this_dict[key] for key in sorted(this_dict, 
                            key = this_dict.get, reverse = high_to_low)}  
        return this_dict  

    @staticmethod 
    def _date_range_to_str(frame):
        start = frame.index.date.min().strftime('%Y-%m-%d')
        end = frame.index.date.max().strftime('%Y-%m-%d')
        return start, end

    @staticmethod 
    def _compute_date_range(date_min = None, date_max = None,
                    asset_date_min = None, asset_date_max = None):
        if asset_date_min <= date_min:
            date_min = asset_date_min 
        if asset_date_max >= date_max:
            date_max = asset_date_max 
        return date_min, date_max 

    def save(self):
        file_name = self.__class__.__name__ + '_index_' + self.current_time + '.pkl'
        file_name = path.join(keys.DATA_PATH, file_name)
        with open(file_name, 'wb') as f:
            pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)

    def _set_date_range(self, date_range = None):
        if date_range is not None:
            return date_range 
        else:
            dates_list = np.array([asset.date_range for asset in self.assets.values()])
            dates_min = dates_list[:,0].min()
            dates_max = dates_list[:,1].max()
            return dates_min, dates_max  
    
    def compute_cumulative_returns_history(self, within_dates = None, end_point = 'Close',
                     sampling = 'D', fully_within_date_range = False):
        """
        computes historical values of cumulative returns
            it is useful for plotting these values for a group of stocks
            for example: a plot of cumulative returns for tickers in a sector
        """
        if within_dates is None:
            within_dates = self.date_range 

        cumulative_returns_history = {}
        for tickr, stock in self.assets.items():
            cm_returns = stock.cumulative_return(within_dates = within_dates, 
                                    end_point = end_point, fully_within_date_range = fully_within_date_range,
                                                sampling = sampling, in_percent = False)
            if cm_returns is not None: 
                cumulative_returns_history[tickr] = cm_returns 
        
        return cumulative_returns_history 
                    
    def compute_investment_returns(self, within_dates = None,
                                 end_point = 'Close', sampling = 'D', fully_within_date_range = False):
        """
        computes cumulative_return[-1] of individual stocks only if requested within_dates
            is fully within date_range of the stock object 
            else: ticker will not be added to period_cumulative_return dictionary  
        period cumulative returns = investment return 
        NOTE: investment return is equivalent to (price[-1] - price[0])/price[0] and is cimulative_return[-1]
        Example: invest 100$: if investment return is 1.2 it means 120 return will be gained (after removing 100$ initial)
        Returns a dataframe of ['ticker','company name', 'investment return', 'sector'] sorted by investment return
        """
        if within_dates is None:
            within_dates = self.date_range 

        investment_returns_dict = {'Ticker':[], 'Sector':[], 'Return':[], 'Name':[]}
        for stock in self.assets.values():
            investment_return = stock.investment_return(within_dates = within_dates, 
                    fully_within_date_range = fully_within_date_range,
                                end_point = end_point, sampling = sampling, initial_investment = 0)
            if investment_return is not None:
                investment_returns_dict['Return'].append(list(investment_return.values())[0])
                investment_returns_dict['Ticker'].append(stock.symbol)
                investment_returns_dict['Sector'].append(stock.sector)
                investment_returns_dict['Name'].append(stock.name)
        
        investment_returns_df = pd.DataFrame.from_dict(investment_returns_dict, orient = 'columns')
        return investment_returns_df 
    
    def compute_mean_volume(self, within_dates = None, fully_within_date_range = True):
        if within_dates is None:
            within_dates = self.date_range 
        mean_trade_volume = {}
        for ticker, stock in self.assets.items():
            trade_volume = stock.mean_trade_volume(within_dates = within_dates,
                 fully_within_date_range = fully_within_date_range)
            if trade_volume is not None:
                mean_trade_volume[ticker] = trade_volume  
        mean_trade_volume = Index._sort_dict(mean_trade_volume, high_to_low = True)
        return mean_trade_volume
    

    # ########### Sector Related Calculations ################## #
    # These methods do not report values for individual stocks   #

    def sector_cumulative_return_history(self, within_dates = None, end_point = 'Close',
                             sampling = 'D', fully_within_date_range = False):
        
        cumulative_return_history = self.compute_cumulative_returns_history(within_dates = within_dates, 
                end_point = end_point, sampling = sampling, fully_within_date_range= fully_within_date_range)
        sector_return_history = {key:None for key in self.sectors.keys()}
        for sector, tickers in self.sectors.items():
            sector_df = []
            for ticker in tickers:
                if ticker in cumulative_return_history.keys():
                    sector_df.append(cumulative_return_history[ticker])
            sector_df = pd.concat(sector_df, axis = 1)
            sector_return_history[sector] = sector_df.mean(axis = 1)
        return pd.DataFrame(sector_return_history) 

    def sector_mean_returns(self, within_dates = None,  
                                end_point = 'Close', sampling = 'D',
                                    fully_within_date_range = False):
        """
        receives a dataframe from compute_investment_returns method 
            and returns a dictionary 
        """
        period_cumulative_returns = self.compute_investment_returns(within_dates = within_dates, 
                            fully_within_date_range = fully_within_date_range, end_point = end_point, sampling = sampling)
        
        sectors = self.sectors.keys()
        sector_mean_returns = {key:[] for key in sectors}      
        
        for sector in sectors:
            sector_mean_returns[sector] = period_cumulative_returns[period_cumulative_returns['Sector'] == sector]['Return'].mean()
        # sort the dict here 
        sector_mean_returns = Index._sort_dict(sector_mean_returns, high_to_low = True)
        return sector_mean_returns
    
    # ### useful methods for longformat data generation ### #    
    def generate_sector_mean_return_long(self, freq = 'M', start_date = None,
                             end_date = None, save_data = False, fully_within_date_range = True):
        if start_date is None:
            start_date = self.date_range[0]
        if end_date is None:
            end_date = self.date_range[1]
        _dates = pd.date_range(start = start_date, end = end_date, freq = freq).date 
        mean_values = []
        for p_start, p_end in zip(_dates[:-1], _dates[1:]):
            sector_mean_return = self.sector_mean_returns(within_dates = (p_start, p_end), 
                         fully_within_date_range = fully_within_date_range)
            return_df = pd.DataFrame([sector_mean_return])
            mean_values.append(return_df)
        sector_mean_return_df = pd.concat(mean_values)
        value_vars = list(sector_mean_return_df.columns)
        sector_mean_return_df['Date'] = _dates[:-1]
        sector_mean_return_long = sector_mean_return_df.melt(id_vars = ['Date'], 
                        value_vars = value_vars, ignore_index = True, var_name = 'Sector', 
                                    value_name = 'Return')
        if save_data:
            file_name = self.__class__.__name__ + '_sector_return_long_' + freq + '_sampling_' +  self.current_time + '.parquet'
            save_name = path.join(keys.DATA_PATH, file_name)
            sector_mean_return_long.to_parquet(save_name, engine = 'auto', index = False, compression = 'snappy')
        
        return sector_mean_return_long 
    # ##################################################################### #
    # ####       Methods for generating index fundamentals             #### #
    # #### These methods are often used for updating index information #### #
    # ##################################################################### #
    def _compute_sector_fundamentals(self):
        """
        Market Cap: sum of the market cap of all assets in a sector
        P/E ratio and Dividend % are average values
        """
        sector_fundamentals = {'Sector':[], 'Market Cap':[], 'P/E(TTM)':[], 'Dividend %':[]}
        for sector in self.sectors.keys():
            sector_fundamentals['Sector'].append(sector)
            sector_df = self.fundamentals[self.fundamentals['Sector'] == sector]
            sector_fundamentals['Market Cap'].append(sector_df['Market Cap'].dropna().sum())
            sector_fundamentals['P/E(TTM)'].append(pd.to_numeric(sector_df['P/E(TTM)'].dropna(), downcast='float').mean())
            sector_fundamentals['Dividend %'].append(pd.to_numeric(sector_df['Dividend %'].dropna(), downcast = 'float').mean())
        self.sector_fundamentals = pd.DataFrame(sector_fundamentals) 

    def generate_index_fundamentals(self):
        """
        generates four dataframes and saves them in parquet files 
            they can also be loaded 
        """
        fundamentals = {'Stock':[], 'Sector':[], 'Market Cap':[], 'P/E(TTM)': [], 'Dividend %':[], 'Name':[]}
        for ticker, stock in self.assets.items():
            fundamentals['Stock'].append(ticker)
            fundamentals['Sector'].append(stock.sector)
            fundamentals['Name'].append(stock.name)
            fundamentals['Market Cap'].append(stock.fundamentals['marketCap'])
            fundamentals['P/E(TTM)'].append(stock.fundamentals['trailingPE'])
            fundamentals['Dividend %'].append(stock.fundamentals['dividendRate'])
        
        self.fundamentals = pd.DataFrame(fundamentals)
        self.fundamentals.dropna(inplace = True)
        self._compute_sector_fundamentals()

        fund_filename = path.join(keys.DATA_PATH, self.__class__.__name__ + '_fundamentals_pulled_on_' + Index.current_time + '.parquet')
        sect_filename = path.join(keys.DATA_PATH, self.__class__.__name__ + '_sector_fundamentals_pulled_on_' + Index.current_time + '.parquet')
        self.fundamentals.to_parquet(fund_filename, engine = 'auto', index = False, compression = 'snappy')
        self.sector_fundamentals.to_parquet(sect_filename, engine = 'auto', index = False, compression = 'snappy')    
    # ########################################################### #

    # #### Load sector long dataframes and fundamental data  #### #   
    def load_sector_mean_returns_long(self, sub_dir = ''):
        
        self.sector_mean_return_long_m = pd.read_parquet(path.join(keys.DATA_PATH, sub_dir,
                     self.sector_long_filename_m))
        self.sector_mean_return_long_q = pd.read_parquet(path.join(keys.DATA_PATH, sub_dir,
                     self.sector_long_filename_q))
    
    def load_fundamentals(self, sub_dir = ''):
        _sector_fundamentals = pd.read_parquet(path.join(keys.DATA_PATH, sub_dir, self.sector_fundamentals_filename))
        self.sector_fundamentals = _sector_fundamentals[_sector_fundamentals['Sector'].isin(keys.SECTORS)]
        self.fundamentals = pd.read_parquet(path.join(keys.DATA_PATH, sub_dir, self.index_fundamentals_filename))
	# ############################################################## #

    @classmethod 
    def pull_assets(cls, period = 'max', interval = '1d',
                     start_date = None, end_date = None, save_data = True):
        """
        cap = 0; it will download all stocks
        """
        # a dictionary of {sector:[ticker]}
        sector_tickers = {}
        # a dictionary of {symbol: Stock object}
        assets = {}
        assets_info = {'Names':[], 'Symbols':[], 'Sectors':[]}
        date_min = datetime.strptime('2030-01-01', '%Y-%m-%d').date()
        date_max = datetime.strptime('1930-01-01', '%Y-%m-%d').date()
        for symbol in cls.list_of_assets:
            print(f'pulling {symbol} ... from {cls.__name__} index ...')
            asset = Stock.get_history(symbol, period = period, interval=interval, 
                                    start_date = start_date, end_date = end_date, 
                                                fundamentals=True)
            if asset is not None and not asset.data.isnull().all().all():
                assets[symbol] = asset
                asset_date_min, asset_date_max = asset.date_range 
                date_min, date_max = Index._compute_date_range(date_min = date_min, date_max = date_max, 
                        asset_date_min = asset_date_min, asset_date_max = asset_date_max)
                sector = asset.sector
                if sector not in sector_tickers.keys():
                    sector_tickers[sector] = []
                sector_tickers[sector].append(symbol)
                assets_info['Names'].append(asset.name)
                assets_info['Symbols'].append(asset.symbol)
                assets_info['Sectors'].append(asset.sector)
        
        assets_info = pd.DataFrame(assets_info)
        if save_data is True:
            if start_date is not None and end_date is not None:
                file_name = cls.__name__ + '_for_' + start_date + '_and_' + end_date  + '_pulled_on_'
            else:
                file_name = cls.__name__ + '_for_' + period + '_intervals_' + interval + '_pulled_on_'
            file_name = file_name + cls.current_time 

            asset_name = path.join(keys.DATA_PATH, file_name + '.pkl')
            with open(asset_name, 'wb') as f:
                for asset in assets.values():
                    pickle.dump(asset, f, pickle.HIGHEST_PROTOCOL)
            
            sector_filename = path.join(keys.DATA_PATH,
                         cls.__name__ + '_sectors_pulled_on_' + cls.current_time + '.dat')
            with open(sector_filename, 'w') as s:
                for sector, tickers in sector_tickers.items():
                    tickers = ','.join(tickers)
                    s.write(sector + '>>>' + tickers + '\n')

            assets_info_filename = cls.__name__ + '_info_pulled_on_' + cls.current_time + '.csv'
            assets_info.to_csv(path.join(keys.DATA_PATH, assets_info_filename), sep = ',', header = True, index = False)           

        return cls(assets = assets, sectors = sector_tickers, date_range = (date_min, date_max), assets_info = assets_info) 

    @classmethod
    def load_assets(cls, assets_file = None, sector_file = None, assets_info = None, sub_dir = ''):
        """
        loads all stocks in sp500 from the pickle file of Stock objects
        """
        assets_file = path.join(keys.DATA_PATH, sub_dir, cls.assets_filename)
        sector_file = path.join(keys.DATA_PATH, sub_dir, cls.sector_filename)
        assets_info = path.join(keys.DATA_PATH, sub_dir, cls.assets_info_filename)

        assets = {}
        with open(assets_file, 'rb') as f:
            while True:
                try:
                    asset = pickle.load(f)
                    assets[asset.symbol] = asset 
                except EOFError:
                    break 
                
        sector_dict = {}
        sector_lines = open(sector_file).read().splitlines()
        for _line in sector_lines:
            line_info = _line.split('>>>')
            sector = line_info[0]
            tickers = line_info[1].split(',')
            sector_dict[sector] = tickers 
        
        assets_info_df = pd.read_csv(assets_info, sep = ',', header = 0)
        return cls(assets = assets, sectors = sector_dict, assets_info = assets_info_df)

    @classmethod 
    def load_index(cls, sub_dir = ''):
        """
        loads the index from the serialized index file and returns an object
        """
        index_file = path.join(keys.DATA_PATH, sub_dir, cls.index_filename)
        with open(index_file, 'rb') as f:
            index = pickle.load(f)
            return index  
	
# ################################# #
# ### 		SP500 Index			### #
# ################################# #  
class SP500(Index):

    list_of_assets = pull_sp500_tickers()
    assets_filename = keys.SP500_ASSETS
    sector_filename = keys.SP500_SECTORS 
    assets_info_filename = keys.SP500_INFO 
    index_filename = keys.SP500_INDEX_FILE 

    sector_long_filename_m = keys.SP500_SECTOR_RETURN_LM 
    sector_long_filename_q = keys.SP500_SECTOR_RETURN_LQ
    sector_fundamentals_filename = keys.SP500_SECTOR_FUNDAMENTALS 
    index_fundamentals_filename = keys.SP500_FUNDAMENTALS

    def __init__(self, assets = {}, sectors = None, date_range = None, assets_info = None):
        super(SP500, self).__init__(assets = assets, sectors=sectors,
            date_range = date_range, assets_info = assets_info)
    
# ###################################### #
# Russel 3000 index                      #
# to avoid downloading fundamentals      #
# using separate functions, we use       #
# Ticker object of yahoo finance         #
# ###################################### #
class Russell3000(Index):

    list_of_assets = pd.read_csv(path.join(keys.DATA_PATH, keys.RUSSELL3000_CSV),
             sep = ',', header = 0)['tickers']
    
    assets_filename = keys.RUSSELL3000_ASSETS
    sector_filename = keys.RUSSELL3000_SECTORS 
    assets_info_filename = keys.RUSSELL3000_INFO 
    index_filename = keys.RUSSELL3000_INDEX_FILE

    sector_long_filename_m = keys.RUSSELL3000_SECTOR_RETURN_LM 
    sector_long_filename_q = keys.RUSSELL3000_SECTOR_RETURN_LQ
    sector_fundamentals_filename = keys.RUSSELL3000_SECTOR_FUNDAMENTALS
    index_fundamentals_filename = keys.RUSSELL3000_FUNDAMENTALS

    def __init__(self, assets = {}, sectors = None, date_range = None, assets_info = None):
         super(Russell3000, self).__init__(assets = assets, sectors = sectors,
            date_range = date_range, assets_info = assets_info)
