
# ############################ #
# Graph components of Nasdaq   #
# ############################ #
from re import S
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
from .. instruments.indices import Nasdaq 
from .. utils import tools, keys
from . import components 

# load assets 
# load all datasets
nq = Nasdaq.load_assets(sub_dir = keys.NASDAQ_SUBDIR)
nq.load_sector_mean_returns_long(sub_dir = keys.NASDAQ_SUBDIR)
nq.load_fundamentals(sub_dir = keys.NASDAQ_SUBDIR)

# define dates and date differences 
nq_start_date, nq_end_date = nq.date_range[0], nq.date_range[1]
one_day_ago, one_week_ago, one_month_ago, six_months_ago, last_year_final_date, one_year_ago = tools.compute_time_deltas(end_date = nq_end_date)

# ############# Graphs and callbacks ############## #
index_name = 'Nasdaq'
# display date range first 
sector_date_range_display = components.DateRangeDisplay(index_name = index_name, 
					index_start_date = nq_start_date, index_end_date = nq_end_date).layout  
# ##########   sector return history  ############ #
sector_return_history = components.SectorReturnHistory(index_name = index_name,
	 index_start_date=nq_start_date, index_end_date = nq_end_date, index_object = nq).layout 
# ##########   Individual stock returns  ############ #
stock_returns = components.StockReturns(index_name = index_name, index_start_date=nq_start_date, 
		index_end_date = nq_end_date, index_object=nq).layout 
# ##########   Sector market cap pie chart ############ #
sector_market_cap = components.SectorMarketCap(index_name = index_name, index_object=nq).layout 
# ######### Methods for generating index fundamentals ######### #
# available keys: Market Cap, P/E, Dividend %
index_fundamentals = components.IndexFundamentals(index_name = index_name, index_object = nq).layout 

# #############  	   Tabs     	############## #
nasdaq_tab = dbc.Tab([
	sector_date_range_display,
		sector_return_history, 
			stock_returns, 
				sector_market_cap, 
					index_fundamentals,
], label = ['NASDAQ'])