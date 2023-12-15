
# ############################ #
# Graph components of SP500	   #
# ############################ #
import dash_bootstrap_components as dbc 
from dash import html, dcc, callback 
from dash.dependencies import Input, Output, State 
from dash.exceptions import PreventUpdate 

import pandas as pd 
from datetime import date,timedelta 
from dateutil.relativedelta import relativedelta 
import plotly.graph_objects as go 
import plotly.express as px 

# package components 
from .. instruments.indices import SP500 
from .. utils import styles, tools, keys
from . import components   

# load assets 
# load all datasets
sp = SP500.load_assets(sub_dir = keys.SP500_SUBDIR)
sp.load_sector_mean_returns_long(sub_dir = keys.SP500_SUBDIR)
sp.load_fundamentals(sub_dir = keys.SP500_SUBDIR)

# define dates and date differences 
sp_start_date, sp_end_date = sp.date_range[0], sp.date_range[1]
one_day_ago, one_week_ago, one_month_ago, six_months_ago, last_year_final_date, one_year_ago = tools.compute_time_deltas(end_date = sp_end_date)


# ############# Graphs and callbacks ############## #
index_name = 's&p500'
# ##########   sector return history  ############ #
sector_return_history = components.SectorReturnHistory(index_name = index_name,
	 index_start_date=sp_start_date, index_end_date = sp_end_date, index_object = sp).layout 
# ##########   Individual stock returns  ############ #
stock_returns = components.StockReturns(index_name = index_name, index_start_date=sp_start_date, 
		index_end_date = sp_end_date, index_object=sp).layout 
# ##########   Sector market cap pie chart ############ #
sector_market_cap = components.SectorMarketCap(index_name = index_name, index_object=sp).layout 
# ######### Methods for generating index fundamentals ######### #
# available keys: Market Cap, P/E, Dividend %
index_fundamentals = components.IndexFundamentals(index_name = index_name, index_object = sp).layout 

# #############  	   Tabs     	############## #
sp500_tab = dbc.Tab([
	sector_return_history, 
		stock_returns, 
			sector_market_cap, 
				index_fundamentals,
], label = ['SP500'])

