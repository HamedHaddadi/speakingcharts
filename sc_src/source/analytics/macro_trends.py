# ############################################### #
# includes various tools for macro trend analyses #
# ############################################### #
from typing import Dict, Optional, Any 
from datetime import datetime, date 
from os import path, listdir 
import pandas as pd
import numpy as np  
from .. utils import market_data, tools, keys   


class IndexReturnVSFedAsset:
	"""
	class responsible for calculating return of indices 
		overlain on a fed asset such as fed fund rate 
	"""
	INDICES = ['SP500', 'DowJones', 'Nasdaq', 'Russell2000', 'Russell3000']
	FED = ['fed_funds_rate']
	
	def __init__(self, fed_assets: Optional[Dict] = None, indices: Optional[Dict] = None):
		self.common_date_range = None 
		self.available_date_range = None 
		self.fed_assets = fed_assets 
		self.indices = indices 
		self._set_date_ranges()
	
	def _set_date_ranges(self):
		"""
		min and maximum date range of all assets
		"""
		for df in list(self.fed_assets.values()) + list(self.indices.values()):
			df.index = pd.to_datetime(df.index)
	
		dates = np.array([[df.index.date.min(), df.index.date.max()] 
					for df in list(self.fed_assets.values()) + list(self.indices.values())])
		self.common_date_range = (dates[:,0].max(), dates[:,1].min()) 
		self.available_date_range = (dates[:,0].min(), dates[:,1].max())
	
	def cumulative_return(self, indices = None, within_dates = None, in_percent = True) -> Dict:
		if within_dates is None:
			within_dates = self.date_range 
		
		cm_returns = {}
		for asset in indices:
			asset_df = self.indices[asset]
			asset_data = tools.choose_dates(asset_df, within_dates)
			if asset_data is not None:
				asset_return = asset_data[asset].resample('M').last().pct_change().dropna()
				cm_returns[asset] = tools.compute_cumulative_return(returns = asset_return,
							 in_percent = in_percent)
		return cm_returns 
	
	@classmethod
	def load_assets(cls):
		main_path = path.join(keys.LOAD_PATH, cls.__name__.upper())
		files = listdir(main_path)
		fed_assets = {}
		indices = {}
		for _file in files:
			file_name = _file.split('.')[0]
			if 'FED' in file_name:
				fed_assets[file_name] = pd.read_csv(path.join(main_path, _file), sep = ',', header = 0).set_index('DATE', drop = True)
			else:
				indices[file_name] = pd.read_csv(path.join(main_path, _file), sep = ',', header = 0).set_index('Date', drop = True)
		return cls(fed_assets = fed_assets, indices = indices)

	@classmethod
	def pull_assets(cls, start_date = '1977-01-01' , end_date = None, save_data = True):
		fed_assets = {}
		indices = {}

		if start_date is None:
			start_date = '1977-01-01'
		
		if end_date is None:
			end_date = date.today().strftime('%Y-%m-%d')
		
		for index in cls.INDICES:
			index_data = market_data.get_yfinance_index(index, start = start_date, end = end_date)
			index_df = index_data['Close'].to_frame(index)
			indices[index] = index_df 
					
		for asset in cls.FED:
			fed_df = market_data.get_fed_asset(asset, start = start_date, end = end_date)
			fed_assets['FED_' + asset] = fed_df 
		
		if save_data is True:
			save_path = tools.make_dir(path.join(keys.DATA_PATH, cls.__name__.upper()))
			for fed_asset, fed_asset_df in fed_assets.items():
				fed_asset_df.to_csv(path.join(save_path, fed_asset + '.csv'), sep = ',', header = True, index = True,
						float_format = '%.5f')
			
			for index, index_df in indices.items():
				index_df.to_csv(path.join(save_path, index + '.csv'), sep = ',', header = True, index = True, 
							float_format = '%.5f')
		
		return cls(fed_assets = fed_assets, indices = indices)


	






	





