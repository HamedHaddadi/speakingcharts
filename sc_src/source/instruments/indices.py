
from copy import deepcopy 
import pandas as pd
import numpy as np
import pandas_datareader.data as web 
import pickle 
import re 
from os import path, makedirs  
from datetime import datetime
import yfinance as yf 
from . securities import Stock
from .. utils import market_data 
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

    assets_filename = keys.INDEX_ASSETS
    sector_filename = keys.INDEX_SECTORS 
    sector_long_filename_m = keys.INDEX_SECTOR_RETURN_LM 
    sector_long_filename_q = keys.INDEX_SECTOR_RETURN_LQ 
    sector_fundamentals_filename = keys.INDEX_SECTOR_FUNDAMENTALS 
    index_fundamentals_filename = keys.INDEX_FUNDAMENTALS  

    fundamentals_keys = ['Market Cap', 'P/E(TTM)', 'Dividend %'] 
    current_time = datetime.now().strftime('%Y-%m-%d-%H-%M')  

    def __init__(self, assets = {}, sectors = None, date_range = None, main_save_path = None):
        """
        assets in a dictionary of {ticker symbol: Stock object}
        sectors is a dictionary of {sector:[ticker]}
        date_range is the minimum and maximum datetime.date in the entire list of assets
        assets_info: is a dataframe of ['company name','ticker','sector'] columns 
        """
        self.assets = assets
        self.num_assets = len(self.assets.keys())
        self.asset_names = [stock.name for stock in self.assets.values()]
        self.sectors = sectors
        self.sector_keys = list(self.sectors.keys())
        self.period_cumulative_returns = None 
        # dictionary of values
        self.capital_gains = {}
        # best performing assets based on cumulative returns 
        self.date_range = self._set_date_range(date_range = date_range) 
        # long format dataframes
        # monthly sampling 
        self.sector_mean_return_long_m = None
        # quarterly sampling 
        self.sector_mean_return_long_q = None 
        self.sector_fundamentals = None 
        self.fundamentals = None
        self._main_save_path = tools.make_dir(main_save_path) 
        self._risk_free = None 
        self.daily_risk_free = None 

    @property 
    def main_save_path(self):
        return self._main_save_path  
    
    @main_save_path.setter 
    def main_save_path(self, new_path):
        if self._main_save_path == None and new_path != '':
            self._main_save_path = new_path
    
    @property 
    def risk_free(self):
        return self._risk_free
    
    # ### different prices ### #
    # last price 
    # average price last week 
    # average price last month
    # average price last 6 month
    # average price last year
        
    @risk_free.setter 
    def risk_free(self, new_rf):
        if self._risk_free is None and new_rf in ['DGS10']:
            self._risk_free = web.DataReader(new_rf, 'fred', self.date_range[0], self.date_range[1])
    
    def set_daily_risk_free(self):
        if self.risk_free is not None and self.daily_risk_free is None:
            periods_per_year = round(self.risk_free.resample('A').size().max())
            self.daily_risk_free = self.risk_free.resample('D').last().div(periods_per_year).div(100).dropna(inplace = False)

    def sort_assets(self, sort_key = 'marketCap'):
        """
        sorts the assets dictionary based on a fundamental key
            this fundamental key can be any of the marketCap, trailingPW or dividendYield
        """
        self.assets = {key:asset for key,asset in sorted(self.assets.items(), key = lambda kv: kv[1].fundamentals[sort_key])}

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
        """
        saves the index object as a separate pkl file
        """
        file_name = path.join(self.main_save_path, 'index.pkl')
        with open(file_name, 'wb') as f:
            pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)

    def save_assets(self):
        """
        saves assets dictionary and sector_ticker dictionary if
            class is instantiated from these dictionaries
        appliable to Russell2000 index
        """
        asset_name = path.join(self.main_save_path,  'all_assets.pkl')
        with open(asset_name, 'wb') as f:
            for asset in self.assets.values():
                pickle.dump(asset, f, protocol = pickle.HIGHEST_PROTOCOL)
        
        sector_filename = path.join(self.main_save_path, 'sectors.dat')
        
        with open(sector_filename, 'w') as s:
            for sector,tickers in self.sectors.items():
                tickers = ','.join(tickers)
                s.write(sector + '>>>' + tickers + '\n')

    def _set_date_range(self, date_range = None):
        if date_range is not None:
            return date_range 
        else:
            dates_list = np.array([asset.date_range for asset in self.assets.values()])
            dates_min = dates_list[:,0].min()
            dates_max = dates_list[:,1].max()
            return dates_min, dates_max  
    
    def compute_cumulative_returns_history(self, within_dates = None, end_point = 'Close', sampling = 'D', tickers = None):
        """
        computes historical values of cumulative returns
            it is useful for plotting these values for a group of stocks
            for example: a plot of cumulative returns for tickers in a sector
        """
        if within_dates is None:
            within_dates = self.date_range 
        cumulative_returns_history = {}
        for tickr in tickers:
            cm_returns = self.assets[tickr].cumulative_return(within_dates = within_dates, 
                                    end_point = end_point, sampling = sampling, in_percent = False)
            if cm_returns is not None: 
                cumulative_returns_history[tickr] = cm_returns 
        return cumulative_returns_history

    # ### return, volatility, sharpe ### #                
    def compute_investment_returns(self, within_dates = None,
                                 end_point = 'Close', sampling = 'D'):
        """
        computes cumulative_return[-1] of individual stocks 
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
                                end_point = end_point, sampling = sampling, initial_investment = 0)
            if investment_return is not None:
                investment_returns_dict['Return'].append(list(investment_return.values())[0])
                investment_returns_dict['Ticker'].append(stock.symbol)
                investment_returns_dict['Sector'].append(stock.sector)
                investment_returns_dict['Name'].append(stock.name)
        
        investment_returns_df = pd.DataFrame.from_dict(investment_returns_dict, orient = 'columns')
        return investment_returns_df 
    
    # ### compute risk_return dataframe: return, sharpe, volatility ### #
    def compute_risk_return(self, within_dates = None, end_point = 'Close',
            sampling = 'D', risk_free = 'DGS10'):
        """
        computes a dataframe contaning cumulative return, volatility, sharpe ratio
        this method is similar to compute_investment_returns above except that
            it computes two more metrics: volatility and sharpe
        dataframe contains different prices (latest, average last week, etc) for coloring in graphs
        """
        if within_dates is None:
            within_dates = self.date_range 
        
        if risk_free is not None:
            self.risk_free = risk_free 
            self.set_daily_risk_free()
        
        risk_return_dict = {'Ticker':[], 'Sector':[], 'Name':[],
                                 'Return':[], 'Volatility': [], 'Sharpe Ratio': [], 'Latest Price': [], 
                                    'Average Price Last Week':[], 'Average Price Last Month':[], 
                                        'Average Price Last Six Months':[],
                                             'Average Price Last One Year':[]}

        for stock in self.assets.values():
            risk_return_dict['Ticker'].append(stock.symbol)
            risk_return_dict['Name'].append(stock.name)
            risk_return_dict['Sector'].append(stock.sector)
            stock.risk_free = self.daily_risk_free
            investment_return = stock.investment_return(within_dates = within_dates, 
                                end_point = end_point, sampling = sampling, initial_investment = 0)
            volatility = stock.volatility(within_dates = within_dates, end_point = end_point, 
                                        sampling = sampling)
            sharpe = stock.sharpe(within_dates = within_dates, end_point = end_point, 
                                        sampling = sampling)
            risk_return_dict['Return'].append(list(investment_return.values())[0])
            risk_return_dict['Volatility'].append(volatility)
            risk_return_dict['Sharpe Ratio'].append(sharpe)
            risk_return_dict['Latest Price'].append(stock.price_latest)
            risk_return_dict['Average Price Last Week'].append(stock.price_avg_last_week)
            risk_return_dict['Average Price Last Month'].append(stock.price_avg_last_month)
            risk_return_dict['Average Price Last Six Months'].append(stock.price_avg_last_six_months)
            risk_return_dict['Average Price Last One Year'].append(stock.price_avg_last_year)
        
        risk_return_df = pd.DataFrame.from_dict(risk_return_dict, orient = 'columns')
        return risk_return_df 


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
    def sector_cumulative_return_history(self, within_dates = None, end_point = 'Close', sampling = 'D', sectors = None):
        
        tickers = []
        for sector in sectors:
            tickers.extend(self.sectors[sector])

        cumulative_return_history = self.compute_cumulative_returns_history(within_dates = within_dates, 
                end_point = end_point, sampling = sampling, tickers = tickers)
        
        sector_return_history = {key:None for key in sectors}
        for sector in sectors:
            sector_df = []
            for ticker in self.sectors[sector]:
                if ticker in cumulative_return_history.keys():
                    sector_df.append(cumulative_return_history[ticker])
            sector_df = pd.concat(sector_df, axis = 1)
            sector_return_history[sector] = sector_df.mean(axis = 1)
        return pd.DataFrame(sector_return_history) 

    def sector_mean_returns(self, within_dates = None,  
                                end_point = 'Close', sampling = 'D'):
        """
        receives a dataframe from compute_investment_returns method 
            and returns a dictionary 
        """
        period_cumulative_returns = self.compute_investment_returns(within_dates = within_dates, 
                            end_point = end_point, sampling = sampling)
        
        sectors = self.sectors.keys()
        sector_mean_returns = {key:[] for key in sectors}      
        
        for sector in sectors:
            sector_mean_returns[sector] = period_cumulative_returns[period_cumulative_returns['Sector'] == sector]['Return'].mean()
        # sort the dict here 
        sector_mean_returns = Index._sort_dict(sector_mean_returns, high_to_low = True)
        return sector_mean_returns
    
    # ### useful methods for longformat data generation ### #    
    def generate_sector_mean_return_long(self, freq = 'M', start_date = None,
                             end_date = None, save_data = False):
        if start_date is None:
            start_date = self.date_range[0]
        if end_date is None:
            end_date = self.date_range[1]
        _dates = pd.date_range(start = start_date, end = end_date, freq = freq).date 
        mean_values = []
        for p_start, p_end in zip(_dates[:-1], _dates[1:]):
            sector_mean_return = self.sector_mean_returns(within_dates = (p_start, p_end))
            return_df = pd.DataFrame([sector_mean_return])
            mean_values.append(return_df)
        sector_mean_return_df = pd.concat(mean_values)
        value_vars = list(sector_mean_return_df.columns)
        sector_mean_return_df['Date'] = _dates[:-1]
        sector_mean_return_long = sector_mean_return_df.melt(id_vars = ['Date'], 
                        value_vars = value_vars, ignore_index = True, var_name = 'Sector', 
                                    value_name = 'Return')
        if save_data:
            file_name = 'sector_return_long_' + freq + '_sampling.parquet'
            save_name = path.join(self.main_save_path, file_name)
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
        Note that in the final plot 0 must be dropped, otherwise None will be dropped 
        """
        fundamentals = {'Stock':[], 'Sector':[], 'Market Cap':[], 'P/E(TTM)': [], 'Dividend %':[], 'Name':[]}
        for ticker, stock in self.assets.items():
            fundamentals['Stock'].append(ticker)
            fundamentals['Sector'].append(stock.sector)
            fundamentals['Name'].append(stock.name)
            fundamentals['Market Cap'].append(stock.fundamentals['marketCap'])
            fundamentals['P/E(TTM)'].append(stock.fundamentals['trailingPE'])
            fundamentals['Dividend %'].append(stock.fundamentals['dividendYield'])
        
        self.fundamentals = pd.DataFrame(fundamentals)
        #self.fundamentals.dropna(inplace = True)
        self._compute_sector_fundamentals()

        # Note:self.main_save_path aleardy includes the index name 
        fund_filename = path.join(self.main_save_path, 'fundamentals.parquet')
        sect_filename = path.join(self.main_save_path, 'sector_fundamentals.parquet')
        self.fundamentals.to_parquet(fund_filename, engine = 'auto', index = False, compression = 'snappy')
        self.sector_fundamentals.to_parquet(sect_filename, engine = 'auto', index = False, compression = 'snappy')    
    # ########################################################### #

    # #### Load sector long dataframes and fundamental data  #### #   
    def load_sector_mean_returns_long(self):
        
        self.sector_mean_return_long_m = pd.read_parquet(path.join(keys.LOAD_PATH, self.__class__.__name__,
                     self.sector_long_filename_m))
        self.sector_mean_return_long_q = pd.read_parquet(path.join(keys.LOAD_PATH, self.__class__.__name__,
                     self.sector_long_filename_q))
    
    def load_fundamentals(self):
        _sector_fundamentals = pd.read_parquet(path.join(keys.LOAD_PATH, self.__class__.__name__, self.sector_fundamentals_filename))
        self.sector_fundamentals = _sector_fundamentals[_sector_fundamentals['Sector'].isin(keys.SECTORS)]
        self.fundamentals = pd.read_parquet(path.join(keys.LOAD_PATH, self.__class__.__name__, self.index_fundamentals_filename))
	# ############################################################## #

    @classmethod 
    def pull_assets(cls, period = 'max', interval = '1d',
                     start_date = None, end_date = None, save_data = True, cap = 0):
        """
        add_index is currently used for sp500 only; but it can be activated for other indices only
            __init__ method of Russell and Nasdaq accept **kwargs to accomodate for 
                variable length keyworded arguments
        note that class name will be added to subdir 
        """
        # a dictionary of {sector:[ticker]}
        sector_tickers = {}
        # a dictionary of {symbol: Stock object}
        assets = {}
        date_min = datetime.strptime('2030-01-01', '%Y-%m-%d').date()
        date_max = datetime.strptime('1930-01-01', '%Y-%m-%d').date()
        count = 0 
        for symbol in cls.list_of_assets:
            print(f'pulling {symbol} ... from {cls.__name__} index ...')
            if cap > 0 and count >= cap:
                break
            count += 1
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
        
        main_save_path = tools.make_dir(path.join(keys.DATA_PATH, cls.__name__.upper()))    
        if save_data is True:
            with open(path.join(main_save_path, 'all_assets.pkl'), 'wb') as f:
                for asset in assets.values():
                    pickle.dump(asset, f, pickle.HIGHEST_PROTOCOL)
            sector_filename = path.join(main_save_path, 'sectors.dat')
            with open(sector_filename, 'w') as s:
                for sector, tickers in sector_tickers.items():
                    tickers = ','.join(tickers)
                    s.write(sector + '>>>' + tickers + '\n')
        return cls(assets = assets, sectors = sector_tickers,
            date_range = (date_min, date_max), main_save_path = main_save_path) 

    @classmethod
    def load_assets(cls):
        """
        loads all stocks in sp500 from the pickle file of Stock objects
        """
        assets_file = path.join(keys.LOAD_PATH, cls.__name__.upper(), cls.assets_filename)
        sector_file = path.join(keys.LOAD_PATH, cls.__name__.upper(), cls.sector_filename)

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
        return cls(assets = assets, sectors = sector_dict)

    @classmethod 
    def load_index(cls):
        """
        loads the index from the serialized index file and returns an object
        """
        index_file = path.join(keys.LOAD_PATH, cls.__name__.upper(), cls.index_class_filename)
        with open(index_file, 'rb') as f:
            index = pickle.load(f)
            return index  
    # ######################################## #
    # operations for operation between indices #
    # ######################################## #

    def __iadd__(self, other):
        """
        adds assets and sectors of two indices
        """
        self.assets.update(other.assets)
        new_sectors = {}
        for sector in keys.SECTORS:
            new_sectors[sector] = list(set(self.sectors.get(sector, [])).union(set(other.sectors.get(sector, []))))
        self.sectors = new_sectors 
        return self 


    def __add__(self, other):
        assets = deepcopy(self.assets)
        assets.update(other.assets)
        new_sectors = {}
        for sector in keys.SECTORS:
            new_sectors[sector] = list(set(self.sectors.get(sector, [])).union(set(other.sectors.get(sector, []))))                

        date_range = self.date_range 
        added_names = self.__class__.__name__ + '_added_to_' + other.__class__.__name__
        
        main_save_path = None 
        if self.main_save_path is not None:
            main_save_path = re.sub(self.__class__.__name__, added_names, self.main_save_path) 
        
        return Index(assets = assets, sectors = new_sectors, date_range = date_range,
                     main_save_path = main_save_path)
        
        
# ################################# #
# ### 		SP500 Index			### #
# ################################# #  
class SP500(Index):
    """
    SP500 has an additional input for __init__
    add_index(), load_index() are methods to generate sp500 and spxew indices 
    currently, only SP500 supports x_index and ew_index attributes
        x_index: SP500 index market cap weighted 
        ew_index: SP500 index equal weighted
    """

    list_of_assets = market_data.pull_sp500_tickers()
    # index filenmes 
    x_index_filename = keys.SP500_INDEX_FILENAME 
    ew_index_filename = keys.SPXEW_INDEX_FILENAME

    def __init__(self, assets = {}, sectors = None, date_range = None, main_save_path = None):
        super(SP500, self).__init__(assets = assets, sectors=sectors,
                    date_range = date_range, main_save_path=main_save_path)
        self.x_index = None
        self.ew_index = None 
    
    # adds and writes index values to files
    # indices: self.sp_index ==> SP500 total index 
    #          self.spxew_index ==> SP500 Equal weighted     
    def add_index(self):
        """
        creates indices and saves dataframes to files 
        """
        start_date, end_date = self.date_range 
        self.x_index = market_data.get_sp500_yfinance(start = start_date, end = end_date)
        self.ew_index = market_data.get_spxew_yfinance(start = start_date, end = end_date)
        self.x_index.dropna(inplace = True)
        self.ew_index.dropna(inplace = True)
        
        sp_filename = path.join(self._main_save_path , 'sp_index.csv')
        spxew_filename = path.join(self._main_save_path, 'spxew_index.csv')

        self.x_index.to_csv(sp_filename, sep = ',', header = True, index = True)
        self.ew_index.to_csv(spxew_filename, sep = ',', header = True, index = True)

    def load_index(self):
        self.x_index = pd.read_csv(path.join(keys.LOAD_PATH, 'SP500', self.x_index_filename), header = 0, sep = ',', index_col='Date')
        self.ew_index = pd.read_csv(path.join(keys.LOAD_PATH, 'SP500', self.ew_index_filename), header = 0, sep = ',', index_col = 'Date') 
        self.x_index.index = pd.to_datetime(self.x_index.index)
        self.ew_index.index = pd.to_datetime(self.ew_index.index)

    def compute_index_cumulative_returns(self, sampling = 'D', in_percent = True, within_dates = None):
        """
        computes cumulative returns of sp_index and spxew_index in a time period 
            it generates dataframes of return vs time 
        """
        if within_dates is None:
            within_dates = self.date_range 
        
        x_data = tools.choose_dates(self.x_index, within_dates)
        ew_data = tools.choose_dates(self.ew_index, within_dates)
        
        x_change = x_data['index_value'].resample(sampling).last().pct_change().dropna()
        ew_change = ew_data['index_value'].resample(sampling).last().pct_change().dropna()

        x_return = tools.compute_cumulative_return(returns = x_change, in_percent= in_percent)
        ew_return = tools.compute_cumulative_return(returns = ew_change, in_percent=in_percent)

        return x_return, ew_return


# ###################################### #
# Russel 3000 index                      #
# to avoid downloading fundamentals      #
# using separate functions, we use       #
# Ticker object of yahoo finance         #
# ###################################### #
class Russell3000(Index):

    list_of_assets = pd.read_csv(path.join(keys.MAIN_DATA_PATH, keys.RUSSELL3000_CSV),
             sep = ',', header = 0)['tickers']

    def __init__(self, assets = {}, sectors = None, date_range = None, main_save_path = None):
         super(Russell3000, self).__init__(assets = assets, sectors = sectors,
            date_range = date_range, main_save_path = main_save_path)
        
    def generate_russell2000_assets(self):
        """
        after generating russell3000, this method sorts assets based on
            market cap and generates information needed for russell2000 class
        generates three files needed for load_asset
        """ 
        self.sort_assets(sort_key='marketCap')
        _sector_tickers = {}
        _assets = {}
        _tickers = list(self.assets.keys())[:2000]
        
        for tickr in _tickers:
            _assets[tickr] = self.assets[tickr]
            sector = self.assets[tickr].sector
            if sector not in _sector_tickers.keys():
                _sector_tickers[sector] = [] 
            _sector_tickers[sector].append(tickr)
        return _assets, _sector_tickers 

# ###################################### #
# Russel 2000 index                      #
# ###################################### #
class Russell2000(Index):    
    def __init__(self, assets = {}, sectors = None, date_range = None, main_save_path = None):
        super(Russell2000, self).__init__(assets = assets, sectors = sectors, 
                        date_range = date_range, main_save_path = main_save_path)
    
# ###################################### #
# NASDAQ                                 #
# to avoid downloading fundamentals      #
# using separate functions, we use       #
# Ticker object of yahoo finance         #
# ###################################### #
class Nasdaq(Index):

    list_of_assets = pd.read_csv(path.join(keys.MAIN_DATA_PATH, keys.NASDAQ_CSV),
             sep = ',', header = 0)['Symbol']

    def __init__(self, assets = {}, sectors = None, date_range = None, main_save_path = None):
        super(Nasdaq, self).__init__(assets = assets, sectors = sectors,
                    date_range = date_range,
                            main_save_path = main_save_path)
        