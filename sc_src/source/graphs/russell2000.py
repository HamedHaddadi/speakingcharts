
# ############################### #
# Graph components of Russell2000 #
# ############################### #

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
from .. instruments.indices import Russell2000 
from .. utils import styles, tools, keys
from . import components   

# load assets 
ru2 = Russell2000.load_assets()
ru2.load_sector_mean_returns_long()
ru2.load_fundamentals()

# define dates and date differences 
ru2_start_date, ru2_end_date = ru2.date_range[0], ru2.date_range[1]
one_day_ago, one_week_ago, one_month_ago, six_months_ago, last_year_final_date, one_year_ago = tools.compute_time_deltas(end_date = ru2_end_date)

# ############# Graphs and callbacks ############## #
index_name = 'russell2000'
# display date range first 
sector_date_range_display = components.DateRangeDisplay(index_name = index_name, 
					index_start_date = ru2_start_date, index_end_date = ru2_end_date).layout
# ##########   sector return history  ############ #
sector_return_history = components.SectorReturnHistory(index_name = index_name,
	 index_start_date= ru2_start_date, index_end_date = ru2_end_date, index_object = ru2).layout
# ##########   Individual stock returns  ############ #
stock_returns = components.StockReturns(index_name = index_name, index_start_date=ru2_start_date, 
		index_end_date = ru2_end_date, index_object=ru2).layout
# ##########   Sector market cap pie chart ############ #
sector_market_cap = components.SectorMarketCap(index_name = index_name, index_object=ru2).layout
# ######### Methods for generating index fundamentals ######### #
# available keys: Market Cap, P/E, Dividend %
index_fundamentals = components.IndexFundamentals(index_name = index_name, index_object = ru2).layout

# #############  	   Tabs     	############## #
russell2000_tab = dbc.Tab([
	sector_date_range_display,
		sector_return_history,
			stock_returns, 
				sector_market_cap, 
					index_fundamentals 
], label = ['RUSSELL2000'])



