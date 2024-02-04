
from abc import ABCMeta, abstractclassmethod 
from typing import Iterable 
import pandas as pd 
import numpy as np 
import pandas_datareader.data as web
import yfinance as yf 
import datetime 
from .. utils import market_data, tools, keys  

# ################### #
#  Asset Base Class   #
# ################### #
class Asset(metaclass =ABCMeta):
    """
    Abstract Base Class for all asset classes
    fundmantals: a dictionary with keys: ['trailingPE', 'forwardPE', 'marketCap', 
                    'sector', 'dividendRate', 'dividendYield']
    """
    _annualize = {'M': 12, 'D': 252, 'W': 52}
    fundamentals_numeric_keys = ['trailingPE','forwardPE', 'marketCap', 'dividendRate', 'dividendYield']
    fundamentals_id_keys = ['sector', 'shortName']

    def __init__(self, symbol = None, data = None, fundamentals = None,
            name = None, sector = None):
        
        self.symbol = symbol
        self.data = data 
        self.fundamentals = fundamentals
        self.name = name 
        self.sector = sector 
        # final date ranfge used by the model 
        self.last_date_range = None 
        self.latest_date = self.data.index.date.max()
        self._risk_free = None 

    # #### Different prices #### #
    @property 
    def price_latest(self):
        return self.data['Close'][-1]
    
    @property 
    def price_avg_last_week(self):
        last_week = tools.get_one_week_ago(self.latest_date)
        return self.data[(self.data.index.date >= last_week) & 
            (self.data.index.date <= self.latest_date)]['Close'].mean()
    
    @property
    def price_avg_last_month(self):
        last_month = tools.get_one_month_ago(self.latest_date)
        return self.data[(self.data.index.date >= last_month) &
                 (self.data.index.date <= self.latest_date)]['Close'].mean()

    @property 
    def price_avg_last_six_months(self): 
        last_six = tools.get_six_months_ago(self.latest_date)
        return self.data[(self.data.index.date >= last_six) &
             (self.data.index.date <= self.latest_date)]['Close'].mean()
    
    @property 
    def price_avg_last_year(self):
        last_year = tools.get_one_year_ago(self.latest_date)
        return self.data[(self.data.index.date >= last_year) &
            (self.data.index.date <= self.latest_date)]['Close'].mean()
    
    @property
    def risk_free(self):
        return self._risk_free 

    @risk_free.setter 
    def risk_free(self, new_risk_free):
        """
        Note that risk_free should be converted according to:
            risk_free.resample(D).last().div(periods_per_year = 262).dropna(inplace = False)
        """
        if isinstance(new_risk_free, pd.Series) or isinstance(new_risk_free, pd.DataFrame):
            self._risk_free = new_risk_free 
    
    @property 
    def date_range(self):
        return self.data.index.date.min(), self.data.index.date.max()
                  
    # => Carpets the dataframe for missing dates
    @staticmethod 
    def fill_frame_daily(data, column = None):
        min_date, max_date = data.index.min(), data.index.max()
        min_date = min_date.to_pydatetime()
        max_date = max_date.to_pydatetime()
        date_range = pd.date_range(start = min_date, end = max_date, freq = 'D')
        key = {True: 'values', 
                False: column}[column is None]
        data = pd.DataFrame({key:data.iloc[:,0]}, index = date_range)
        data.ffill(inplace = True)
        data.dropna(inplace = True)
        return data 
    
    @staticmethod
    def dates(frame):
        return frame.index.min(), frame.index.max()

     
    @staticmethod
    def compute_cumulative_return(returns = None, in_percent = False):
        if in_percent:
            return ((1 + returns).cumprod() - 1).dropna()*100
        else:
            return ((1 + returns).cumprod() - 1).dropna()

    def is_within_dates(self, within_dates = None):
        """
        accepts a tuple of (start, end) and compares with date_range of the asset
        returns: boolean True or False
                True if either start or end falls within date range
                False if start..end is outside date_range[0]..date_range[1]
        """
        start, end = within_dates 
        if not (start and end):
            raise TypeError('start and end are None in is_within_dates')
        else:
            start = tools.to_date(start)
            end = tools.to_date(end)
            if start > end:
                raise ValueError('start date is ahead of end date')
            elif start >= self.date_range[0] and start <= self.date_range[1] and end >= self.date_range[1]:
                return True 
            elif start <= self.date_range[0] and end >= self.date_range[0] and end <= self.date_range[1]:
                return True 
            elif start >= self.date_range[0] and end <= self.date_range[1]:
                return True
            else:
                return False  
    
    def is_fully_within_date_range(self, within_dates = None):
        """
        a method useful for working with indices or multi asset objects such as SP500
        """
        start, end = within_dates 
        if not (start and end):
            raise TypeError('start and end are None in is_within_dates')
        else:
            start = tools.to_date(start)
            end = tools.to_date(end)
            if start > end:
                raise ValueError('start date is ahead of end date')
            elif start >= self.date_range[0] and end <= self.date_range[1]:
                return True 
            else:
                return False 

    def adjust_within_dates(self, within_dates):
        start, end = within_dates 
        if start:
            start = tools.to_date(start)
            if start.date() <= self.date_range[0]:
                start = self.date_range[0].strftime('%Y-%m-%d')
        if end:
            end = tools.to_date(end)
            if end.date() >= self.date_range[1]:
                end = self.date_range[1].strftime('%Y-%m-%d')  
        self.last_date_range = [start, end]
        return start, end   

    @staticmethod
    def to_datetime(frame):
        if not isinstance(frame.index, datetime.date):
            frame.index.to_pydatetime()
        return frame

    # ############################################################### #
    # #### cumulative return & capital gains  #### #
    def cumulative_return(self, within_dates =  None, 
                 end_point = ' Close', sampling = 'D', in_percent = False):
        """
        computes cumulative returns within a period
        using (1 + pct_change).cumprod() - 1
        pct_change depends on sampling
        returns a dictionary of asset cumulative return 
            if requested
        cumulative returns are dataframes 
        """
        cm_returns = None
        if within_dates is None:
            within_dates = self.date_range 
         
        data = tools.choose_dates(self.data, within_dates)
        if data is not None:
            asset_return = data[end_point].resample(sampling).last().pct_change().dropna()
            cm_returns = Asset.compute_cumulative_return(returns = asset_return, in_percent=in_percent)
        return cm_returns 
    
    def investment_return(self, within_dates =  None, 
                 end_point = 'Close', sampling = 'D', 
                            initial_investment = 0):
        """
        computes return from an investment using cumulative return 
        Returns: a dictionary of return which may contain capital gain as well in initial_investment is not 0
        """
        cm_returns = self.cumulative_return(within_dates = within_dates, 
                            end_point= end_point, sampling = sampling, in_percent = False)
        investment_return = None
        if cm_returns is not None and len(cm_returns.index) > 0:
            investment_return = {self.name + '_investment_return': cm_returns.values[-1]}
            if initial_investment != 0:
                investment_return['gain_of_' + str(initial_investment) + '_dollars'] = initial_investment*investment_return[self.name + '_investment_return']
        return investment_return   
    
    def volatility(self, within_dates = None, end_point = 'Close', 
                    sampling = 'D'):
        """
        computes annualized volatility within a time period 
        """
        num_trading_periods = keys.NUM_PERIODS[sampling]
                
        if within_dates is None:
            within_dates = self.date_range 
        
        volatility = None 
        data = tools.choose_dates(self.data, within_dates) 
        if data is not None:
            data = data.resample(sampling).last()
            returns = np.log(data[end_point]/data[end_point].shift(1))
            returns.fillna(0, inplace = True)
            volatility = returns.std()*np.sqrt(num_trading_periods)
        return volatility 
    
    def sharpe(self, within_dates = None, end_point = 'Close', sampling = 'D'):
        """
        sharpe ratio is calculated using:
            sqrt(num periods)*(aritmetic_mean_period_return - risk_free_rate)/(std of period_returns)
        It is reported on annual basis;  
        Note that risk free is divided by 100 to report as percent; then divided by number of periods
            example: mean 0.018 return annually is 0.018/255 daily 
        """
        num_trading_periods = keys.NUM_PERIODS[sampling]

        if within_dates is None:
            within_dates = self.date_range

        data = tools.choose_dates(self.data, within_dates)
        risk_free = tools.choose_dates(self.risk_free, within_dates)
        sharpe = None 
   
        if data is not None and risk_free is not None:
            sampling_return = data[end_point].resample(sampling).last().pct_change().dropna(inplace = False)
            mean_returns = (sampling_return.mean() + 1)**(num_trading_periods) - 1
            std = sampling_return.std()*np.sqrt(num_trading_periods)
        
            risk_free = risk_free.resample(sampling).last()
            mean_risk_free = risk_free.mean().values[0]
            sharpe = (mean_returns - mean_risk_free)/std 
        return sharpe
    
    # trading volume
    def mean_trade_volume(self, within_dates = None, fully_within_date_range = False):
        if within_dates is None:
            within_dates = self.date_range
        elif self.is_within_dates(within_dates=within_dates) is not True:
            return None 
        if fully_within_date_range is True and self.is_fully_within_date_range(within_dates=within_dates) is False:
            return None
        data = tools.choose_dates(self.data, within_dates)  
        return data['Volume'].mean()      
    
    # class instantiation factories
    @abstractclassmethod 
    def get_history(cls, *args, **kwargs):
        ...
    
    @staticmethod 
    def _numeric_value_is(value):
        try:
            return float(value)
        except:
            return None 

    @staticmethod 
    def pull_history_and_fundamentals(symbol = None, period = None, 
                    interval = None, start_date = None, end_date = None):
        """
        pulls history and generates fundamentals as well 
        """
        fundamentals = {key:None for key in Asset.fundamentals_numeric_keys + Asset.fundamentals_id_keys}

        try:
            symbol_data = yf.Ticker(symbol)
            if start_date is None and end_date is None:
                data = symbol_data.history(period = period, interval = interval)
            else:
                data = symbol_data.history(start = start_date, end = end_date)
            for key,value in symbol_data.info.items():
                if key in Asset.fundamentals_numeric_keys:
                    fundamentals[key] = Asset._numeric_value_is(value)
                elif key in Asset.fundamentals_id_keys:
                    fundamentals[key] = value
            fundamentals['sector'] = keys.SECTOR_KEYS[fundamentals['sector']]
            old_name = fundamentals['shortName']
            new_name = old_name.replace('"', '')
            fundamentals['shortName'] = new_name    
            return data, fundamentals 
        except:
            return None, None 

# ################### #
#       Stocks        #
# ################### #
class Stock(Asset):
    def __init__(self, *args, **kwargs):
        super(Stock, self).__init__(*args, **kwargs)
    
    @classmethod 
    def get_history(cls, symbol, period = 'max', interval = '1d', start_date = None, end_date = None, fundamentals = False):
        """
        period: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        interval: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
        start and end_date: year-month-day 
        """
        try:
            data, fundamentals = Stock.pull_history_and_fundamentals(symbol = symbol,
                                            period = period, interval = interval, start_date = start_date, end_date = end_date)
        
            if data is not None and fundamentals is not None:
                return cls(symbol = symbol, data = data, sector = fundamentals['sector'],
                        fundamentals = fundamentals, name = fundamentals['shortName'])
        except:
            return None 

# ################################# #
#  Cryptos                          #
# SEC definition for cryptos        #
# ################################# #
class Crypto(Stock):
    """
    Note that ticker symbols are often combined with USD:
            BTC-USD
            ETH-USD
            PEPE-USD
    """
    def __init__(self, *args, **kwargs):
        super(Crypto, self).__init__(*args, **kwargs)

    

    



    

