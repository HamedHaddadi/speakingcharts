# ######################################## #
# Tools to compare performance of an asset #
# ######################################## #
import pickle 
import numpy as np 
import pandas as pd 
from os import path 
from datetime import datetime 
from .. utils import keys, tools 
from .. instruments.indices import SP500, Russell3000, Nasdaq


class Performance:
	"""
	generates probability distribution of return, volatility, fundamentals and other metrics
	attributes:
		self.assets = sum of Index objcets: SP500 + Russell3000 + Nasdaq 
	
	Following data can be produced for more graph pbjects 
		return and its histogram 
		volatility and histogram 
		return-volatility
		performance with respect to market
		performance with respect to risk free 
	
	Date ranges are limited:
		past 90 days 
		past 180 days 
		past year 
		last two years 
	"""
	current_time = datetime.now().strftime('%Y-%m-%d-%H-%M')
	def __init__(self, assets = None, main_save_path = None):
		self.assets = assets 
		self.main_save_path = tools.make_dir(main_save_path)
	
	@property 
	def sample_size(self):
		return len(self.assets_object.assets)
	
	def generate_investment_return(self):
		pass  

	def generate_investment_return_distribution(self, within_dates = None,
				 sampling = 'D', bins = 100):
		"""
		generates return distribution for the entire universe
		"""
		if within_dates is None:
			within_dates = self.assets.date_range 
		investment_return_df = self.assets.compute_investment_returns(within_dates = within_dates, 
					sampling = sampling)
		return_hist, returns = np.histogram(investment_return_df['Return'].values, bins = bins)
		returns = [0.5*(ret[0] + ret[1]) for ret in zip(returns[:-1], returns[1:])]
		return_hist_df = pd.DataFrame(np.c_[returns[:,np.newaxis], return_hist[:,np.newaxis]], columns = ['Returns', 'Population Density'])
		return_hist_df = return_hist_df[return_hist_df['Population Density'] != 0]
		return investment_return_df, return_hist_df 
		

	@classmethod
	def load_assets_from_indices(cls, sub_dir = ''):
		sp_object = SP500.load_assets()
		ru_object = Russell3000.load_assets()
		nasdaq_object = Nasdaq.load_assets()

		grand_assets_object = sp_object + ru_object + nasdaq_object 
		main_save_path = path.join(keys.DATA_PATH, sub_dir)
		return cls(assets = grand_assets_object, main_save_path = main_save_path)


	@classmethod 
	def load_distributions(cls):
		pass 



