
# ####### General Purpose Tools ####### #
from datetime import datetime, date
from itertools import islice 
from os import path, makedirs  
import plotly.graph_objects as go  
import pandas as pd 
from datetime import date,timedelta 
from dateutil.relativedelta import relativedelta


def make_dir(dirname):
	if dirname is not None and not path.exists(dirname):
		makedirs(dirname)
	return dirname 

def blank_figure():
	fig = go.Figure(go.Scatter(x = [], y = []))
	fig.update_layout(template = None)
	fig.update_xaxes(showgrid = False, showticklabels = False, zeroline = False)
	fig.update_yaxes(showgrid = False, showticklabels = False, zeroline = False)
	return fig 


def batched(iterable, number):
	if number < 1:
		raise ValueError('n must be at least one')
	it = iter(iterable)
	while batch := tuple(islice(it, number)):
		yield batch

def to_date(input_date):
	if isinstance(input_date, str):
		return datetime.strptime(input_date, '%Y-%m-%d').date()
	elif isinstance(input_date, date):
		return input_date

def adjust_dates(start_date, end_date, default_start = None, default_end = None):
	if start_date is None:
		start_date = default_start
	if end_date is None:
		end_date = default_end 
	
	if isinstance(start_date, str):
		start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
	if isinstance(end_date, str):
		end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
	
	if start_date >= end_date:
		start_date = default_start 
		end_date = default_end  
	
	return start_date, end_date

def choose_dates(frame, within_dates = None):
	start, end = within_dates
	if start:
		start = to_date(start)
		frame = frame[frame.index.date >= start]
	if end:
		end = to_date(end)
		frame = frame[frame.index.date <= end]
	return {True: None,
			False: frame}[frame.empty] 

# lite version of choose_dates: within_dates is a tuple of [datetime.date, datetime.date]
choose_dates_lite = lambda frame, within_dates: frame[(frame.index.date >= within_dates[0]) & (frame.index.date <= within_dates[1])]


def find_assets_common_times(asset_1 = None, asset_2 = None):
    min_1 = asset_1.index.date.min()
    max_1 = asset_1.index.date.max()
    min_2 = asset_2.index.date.min()
    max_2 = asset_2.index.date.max()
    min_date = max(min_1, min_2)
    max_date = min(max_1, max_2)
    asset_1 = choose_dates(asset_1, (min_date, max_date))
    asset_2 = choose_dates(asset_2, (min_date, max_date))
    return asset_1, asset_2 

# #### time difference operations #### #
def compute_time_deltas(end_date = None):
	one_day_ago = end_date - timedelta(days = 1)
	one_week_ago = end_date - timedelta(days = 7)
	one_month_ago = end_date - timedelta(weeks = 4)
	six_months_ago = end_date - relativedelta(months = 6)
	last_year_final_date = date(end_date.year - 1, 12, 31)  
	one_year_ago =  end_date - relativedelta(years = 1)
	return one_day_ago, one_week_ago, one_month_ago, six_months_ago, last_year_final_date, one_year_ago


# ### cumulative return calculation 			############### #
# A similar staticmethod exists in the Asset class  			#
# The function here can be used by other classes such as index  #
# ############################################################# #
def compute_cumulative_return(returns = None, in_percent = False):
	if in_percent:
		return ((1 + returns).cumprod() - 1).dropna()*100 
	else:
		return ((1 + returns).cumprod() - 1).dropna()
