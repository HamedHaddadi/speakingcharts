
# ##################################### #
# common components used by all indices #
# ##################################### #

from typing import Iterable
import dash_bootstrap_components as dbc 
import pandas as pd 
import plotly.graph_objects as go 
import plotly.express as px
from dash import html, dcc, callback 
from dash.dependencies import Input, Output, State 
from dash.exceptions import PreventUpdate 
from datetime import date,timedelta 
from dateutil.relativedelta import relativedelta
from functools import wraps  
# package modules
from .. utils import styles, tools, keys 

# module vasriables 
SECTOR_COLORS = {'Real Estate': '#FF00FF', 'Energy': '#000000', 'Consumer Discretionary': '#9400D3', 
			'Consumer Staples': '#F08080', 'Financials': '#6495ED', 
				'Health Care': '#800000', 'Communication Services': '#808000', 
					'Information Technology': '#00008B', 'Industrials': '#9ACD32', 
						'Utilities': '#8B4513', 'Materials': '#FF0000'}
# ###### Layout Components that are useful for all indices ###### #
# display the current date to mention data currency 
class DateRangeDisplay:
	base_name = '_date_display'
	def __init__(self, index_name = 's&p500', index_start_date = None, index_end_date = None, 
				message = 'Data collected from'):
		index_start_date = index_start_date.strftime('%Y-%m-%d')
		index_end_date = index_end_date.strftime('%Y-%m-%d')
		self.layout = html.Div([
			html.H3(f'{message} {index_start_date} to {index_end_date} and updated weekly',
					style = styles.h3_style)
		], id = index_name + self.base_name + '_div')
		
# ### sector return history layout ### #
class SectorReturnHistory:
	"""
	layout and callback for sector return history
	"""
	base_name = '_sector_return_history_'
	def __init__(self, index_name = 's&p500', index_start_date = None, index_end_date = None, index_object = None):
		
		self.index_start_date = index_start_date 
		self.index_end_date = index_end_date 
		self.index_object = index_object
		self.sector_keys = self.index_object.sector_keys 

		# define names
		self.graph_id = index_name + self.base_name + 'graph'
		self.date_picker_id = index_name + self.base_name + 'date_picker'
		self.dropdown_id = index_name + self.base_name + 'dropdown'
		self.submit_button_id = index_name + self.base_name + 'submit'

		self.layout =html.Div([
			html.H2(f'return history for each sector in {index_name}', style = styles.h2_style),
			dbc.Row([
				html.Main("""This graph displays the average cumulative return of each sector in a time period.
						 Please choose a time period and sectors and push the crunch button.
					 Return calculations start from the beginning of each period. 
					 You may choose multiple sectors to compare.""", style = styles.main_style), 
				dbc.Col([
					dcc.DatePickerRange(id = self.date_picker_id, min_date_allowed = self.index_start_date, 
						max_date_allowed = self.index_end_date, start_date = self.index_start_date,
							initial_visible_month = self.index_start_date, end_date = self.index_end_date, style = styles.date_picker)
						]),
				dbc.Col([
					dcc.Dropdown(id =self.dropdown_id, multi = True,
						placeholder = 'choose sectors',
				 			options = self.sector_keys, searchable = True, style = styles.multi_dropdown)
						]),
					]),
				dbc.Button('crunch!', id = self.submit_button_id, n_clicks = 0, style = styles.submit),
					dcc.Loading([
						dcc.Graph(id = self.graph_id, figure = tools.blank_figure(), style = {'width': '95%', 'margin-left': '20px', 'mergin-right': '20px', 'margin-top': '20px'})
						], id = index_name + self.base_name + '_load' , type='cube')
					], id = index_name + self.base_name + '_div')
		
		self.callback = callback(Output(self.graph_id, 'figure'), 
				Input(self.submit_button_id, 'n_clicks'), 
				   State(self.date_picker_id, 'start_date'), 
				   	  State(self.date_picker_id, 'end_date'), 
						 State(self.dropdown_id, 'value'), prevent_initial_call = True)(self.plot_sector_return_history)

	def plot_sector_return_history(self, n_clicks, start_date, end_date, selected_sectors):
		start_date, end_date = tools.adjust_dates(start_date, end_date, default_start = self.index_start_date,
					default_end=self.index_end_date)
		
		if selected_sectors is None or len(selected_sectors) == 0:
			raise PreventUpdate

		sector_ret_hist = self.index_object.sector_cumulative_return_history(within_dates = (start_date, end_date),
				 sectors = selected_sectors)

	#	available_sectors =sector_ret_hist.columns 
		fig = go.Figure()
		for sector in selected_sectors:
			fig.add_scatter(x = sector_ret_hist.index, y = sector_ret_hist[sector]*100, 
								mode = 'lines', name = sector, line_color = SECTOR_COLORS[sector])
		
		fig.data[0].showlegend = True
		fig.layout.height = 600
		fig.layout.xaxis.gridcolor = 'black'
		fig.layout.yaxis.gridcolor = 'black'
		fig.layout.xaxis.title = 'date'
		fig.layout.yaxis.title = 'return, %'
		fig.layout.font.family = 'Gill Sans'
		fig.layout.font.size = 20
		return fig

# ###### Return of Individual Stocks ###### #
class StockReturns:
	base_name = '_stock_return_'
	def __init__(self, index_name = 's&p500', index_start_date = None,
		index_end_date = None, index_object = None):

		self.index_start_date = index_start_date 
		self.index_end_date = index_end_date  
		self.index_object = index_object 
		# note that the callback can display graphs in batches of 50 assets 
		self.dropdown_range_max = self.index_object.num_assets//50 + 1 

		self.date_picker_id = index_name + self.base_name + 'date_picker'
		self.dropdown_id = index_name + self.base_name + 'dropdow'
		self.graph_id = index_name + self.base_name + 'graph'
		self.submit_button_id = index_name + self.base_name + 'submit'
		# faster way to cache callbacks without using wraps
		self.callback_start_date = index_start_date  
		self.callback_end_date = index_end_date 
		# date_range investment return is calculated only once unless date range changes 
		self.date_range_return = None 

		self.layout = html.Div([
			html.H2(f'return of individual stocks in {index_name}', style = styles.h2_style),
			dbc.Row([
				html.Main('This graph displays cumulative returns of individual stocks for the time period. Please choose a date range and the number of stocks you wish to display, then push the crunch button.', style = styles.main_style),
				dbc.Col([
					dcc.DatePickerRange(id = self.date_picker_id, min_date_allowed = self.index_start_date, 
					max_date_allowed = self.index_end_date, start_date = self.index_start_date,
						initial_visible_month = self.index_start_date, end_date = self.index_end_date, style = styles.date_picker)
						]),
				dbc.Col([
					dcc.Dropdown(id = self.dropdown_id, 
						placeholder = 'choose number of stocks to display ',
				 			options = [{'label': 'display up to ' + str(50*count) + ' stocks', 
												'value': 50*count} for count in range(1,self.dropdown_range_max)], style = styles.single_dropdown)
						]),
					]),
				dbc.Button('crunch!', id = self.submit_button_id, n_clicks = 0, style = styles.submit),
					dcc.Loading([
						dcc.Graph(id = self.graph_id, figure = tools.blank_figure(),
				 		style = {'width': '100%', 'margin-left': '20px', 'margin-top': '20px'})
						], id = index_name + self.base_name + 'load_graph', type='cube')
				], id = index_name + self.base_name + 'div')
		
		self.callback = callback(Output(self.graph_id, 'figure'), 
			Input(self.submit_button_id, 'n_clicks'), 
				State(self.date_picker_id, 'start_date'),
					State(self.date_picker_id, 'end_date'), 
						State(self.dropdown_id, 'value'), prevent_initial_call = True)(self.plot_stock_return)
	
	@staticmethod 
	def sort_date_range_return(frame = None):
		frame['Return'] = frame['Return']*100 
		frame.sort_values(by = ['Return'], ascending = False, inplace = True)
		frame.reset_index(drop = True, inplace = True)
		frame = frame.iloc[::-1]
		return frame 

	def plot_stock_return(self, n_clicks, start_date, end_date, num_stocks):
		start_date, end_date = tools.adjust_dates(start_date, end_date,
				default_start = self.index_start_date, default_end=self.index_end_date)	
		if num_stocks is None:
			raise PreventUpdate 

		if n_clicks == 1:
			self.callback_start_date = start_date 
			self.callback_end_date = end_date 
			frame = self.index_object.compute_investment_returns(within_dates = (self.callback_start_date, self.callback_end_date))
			self.date_range_return = StockReturns.sort_date_range_return(frame = frame)
		
		elif n_clicks > 1 and (start_date != self.callback_start_date or end_date != self.callback_end_date):
			self.callback_start_date = start_date 
			self.callback_end_date = end_date 
			frame = self.index_object.compute_investment_returns(within_dates = (self.callback_start_date, self.callback_end_date))
			self.date_range_return = StockReturns.sort_date_range_return(frame = frame)

		investment_df = self.date_range_return[self.date_range_return.index <= num_stocks]
		fig = px.bar(investment_df, y = 'Ticker', 
			x = 'Return', orientation = 'h', 
				labels = {'Return': 'return, %', 'Ticker': 'stock ticker symbol'},
					color = 'Return', color_continuous_scale = 'Turbo',
						hover_name = 'Name', hover_data = ['Sector', 'Return'],
				height = 800*(num_stocks//50), template = 'seaborn')

		fig.layout.font.family = 'Gill Sans'
		fig.layout.font.size = 10
		fig.layout.xaxis.gridcolor = 'black'
		fig.layout.yaxis.gridcolor = 'black'
		fig.layout.xaxis.titlefont.family = 'Gill Sans'
		fig.layout.xaxis.titlefont.size = 30
		fig.layout.xaxis.tickfont.size = 20
		fig.layout.yaxis.titlefont.family = 'Gill Sans'
		fig.layout.yaxis.titlefont.size = 30
		fig.layout.coloraxis.colorbar.tickfont.size = 20				 
		return fig

# ###### Risk-Return-Sharpe Scatter plots ###### #
class StockRiskReturn:
	"""
	plots scatter plots of cumulative return-volatility colored by sharpe ratio
	"""
	base_name = '_risk_return_'
	def __init__(self, index_name = 's&p500', index_object = None, index_start_date = None, 
							index_end_date = None):
		self.index_start_date = index_start_date 
		self.index_end_date = index_end_date 
		self.index_object = index_object
		self.index_object.risk_free = 'DGS10'
		self.index_object.set_daily_risk_free()

		self.date_picker_id = index_name + self.base_name + 'date_picker'
		self.dropdown_id = index_name + self.base_name + 'dropdown'
		self.radio_id = index_name + self.base_name + 'radio'
		self.graph_id = index_name + self.base_name + 'graph'
		self.submit_button_id = index_name + self.base_name + 'submit'

		# ways to reduce calculation time 
		self.callback_start_date = index_start_date 
		self.callback_end_date = index_end_date 
		self.risk_return_df = None 

		self.layout = html.Div([
			html.H2(f'Return - Volatility - Sharpe ratio with 10 year treasury as the risk free asset', style = styles.h2_style),
			dbc.Row([
				html.Main("""This graph displays cumulative
				 			return-volatility and colors show the sharpe ratio 
							 		using 10 year treasury yield.
									  You can compare performance of a group of stocks
									   with respect to the entire universe by choosing 
									   them from the dropdown menu. Choose an item using the radio button 
									   	to change color of points""", style = styles.main_style),
				dbc.Col([
					dcc.DatePickerRange(id = self.date_picker_id, min_date_allowed = self.index_start_date, 
					max_date_allowed = self.index_end_date, start_date = self.index_start_date,
						initial_visible_month = self.index_start_date, end_date = self.index_end_date, style = styles.date_picker)
						]),
				dbc.Col([
					dcc.Dropdown(id = self.dropdown_id, multi = True, searchable = True,
						placeholder = 'choose stock(s) to compare',
				 			options = self.index_object.asset_names, style = styles.multi_dropdown)
						]),	
				dbc.Col([
					dcc.RadioItems(id = self.radio_id, options = ['Sharpe Ratio', 'Latest Price', 
						'Average Price Last Week', 'Average Price Last Month', 'Average Price Last Six Months', 
							'Average Price Last One Year'], value = 'Latest Price', style = styles.radio_item)
						]),		
					]), 
				dbc.Button('crunch!', id = self.submit_button_id, n_clicks = 0, style = styles.submit),
					dcc.Loading([
						dcc.Graph(id = self.graph_id, figure = tools.blank_figure(),
				 		style = {'width': '90%', 'margin-left': '20px', 'margin-top': '20px'})
						], id = index_name + self.base_name + 'load_graph', type='cube')
		], id = index_name + self.base_name + 'div')
		
		self.callback = callback(Output(self.graph_id, 'figure'), 
			Input(self.submit_button_id, 'n_clicks'), 
				State(self.date_picker_id, 'start_date'),
					State(self.date_picker_id, 'end_date'), 
						State(self.dropdown_id, 'value'),
							State(self.radio_id, 'value'),
							 prevent_initial_call = True)(self.plot_risk_return_sharpe)
	
	def plot_risk_return_sharpe(self, n_clicks, start_date, end_date, stock_names, color_by):
		
		if stock_names is None:
			raise PreventUpdate 
		
		start_date, end_date = tools.adjust_dates(start_date, end_date, default_start = self.index_start_date, 
						default_end = self.index_end_date)
		
		if n_clicks == 1:
			self.callback_start_date = start_date 
			self.callback_end_date = end_date 
			self.risk_return_df = self.index_object.compute_risk_return(within_dates = (self.callback_start_date,
								 self.callback_end_date), risk_free = None)
		
		elif n_clicks > 1 and (start_date != self.callback_start_date or end_date != self.callback_end_date):
			self.callback_start_date = start_date 
			self.callback_end_date = end_date 
			self.risk_return_df = self.index_object.compute_risk_return(within_dates = (self.callback_start_date,
								self.callback_end_date), risk_free = None)
		
		select_assets = self.risk_return_df[self.risk_return_df['Name'].isin(stock_names)]

		if color_by != 'Sharpe Ratio':
			color_min = self.risk_return_df[color_by].min()
			color_max = self.risk_return_df[color_by].quantile(0.8).mean()
			marker_face_color = 'Yellow'
			marker_line_color = 'Red'
		else:
			color_min = self.risk_return_df[color_by].min()
			color_max = self.risk_return_df[color_by].max()
			marker_face_color = 'Black'
			marker_line_color = 'Black'

		fig = go.Figure()
		fig = px.scatter(self.risk_return_df,  x='Volatility', y = 'Return',
				 color = color_by, hover_data = ['Name', 'Ticker','Return', 'Volatility', color_by],
				 	range_color = (color_min, color_max), 
				 	height = 600, template = 'seaborn', opacity = 0.8)
		fig.update_traces(marker = {'size': 15})
		select_asset_fig = px.scatter(select_assets, x = 'Volatility', y = 'Return', color = color_by, 
					range_color = (color_min, color_max),
			 hover_data = ['Name', 'Ticker','Return', 'Volatility', color_by])
		select_asset_fig.update_traces(marker  = {'size': 25, 'symbol': 'x', 'line': {'width': 4, 'color': marker_line_color}})
		fig.add_trace(select_asset_fig['data'][0])
		
		
		fig.layout.coloraxis.colorscale = 'Turbo'
		fig.layout.font.family = 'Gill Sans'
		fig.layout.font.size = 20
		fig.layout.xaxis.gridcolor = 'black'
		fig.layout.yaxis.gridcolor = 'black'
		fig.layout.xaxis.titlefont.family = 'Gill Sans'
		fig.layout.xaxis.titlefont.size = 30
		fig.layout.xaxis.tickfont.size = 20
		fig.layout.yaxis.titlefont.family = 'Gill Sans'
		fig.layout.yaxis.titlefont.size = 30
		fig.layout.coloraxis.colorbar.tickfont.size = 20

		return fig 	
		
# ###### Sector Market Cap ###### #
class SectorMarketCap:
	"""
	plots pie chart of sector market cap 
	index_end_date can be used to add a text box
	"""
	base_name = '_sector_market_cap_'
	def __init__(self, index_name = 's&p500', index_object = None, index_end_date = None):
		self.show_button_id = index_name + self.base_name + 'show'
		self.graph_id = index_name + self.base_name + 'graph'
		self.index_object = index_object 
		self.index_end_date = index_end_date 

		self.layout = html.Div([
				html.H2(f'market cap share of each sector in {index_name}', style = styles.h2_style),
					html.Main(""" this pie chart shows market cap of each sector """, style = styles.main_style),
					dbc.Button('crunch!', id = self.show_button_id, n_clicks = 0, style = styles.submit), 
				dcc.Loading([
					dcc.Graph(id = self.graph_id, figure = tools.blank_figure(), 
						style = {'width': '90%', 'margin-left': '10px', 'margin-top': '20px'})
						], id = index_name + self.base_name + 'load', type = 'cube')
			], id = index_name + self.base_name + '_div')
		
		self.callback = callback(Output(self.graph_id, 'figure'),
 							Input(self.show_button_id, 'n_clicks'),
				prevent_initial_call = True)(self.plot_sector_market_cap)

	def plot_sector_market_cap(self, n_clicks):
		fig = px.pie(self.index_object.sector_fundamentals, values = 'Market Cap', names = 'Sector')
		fig.layout.font.family = 'Gill Sans'
		fig.layout.font.size = 20
		fig.layout.height = 600
		return fig

# ###### Index Fundamentals ###### #
class IndexFundamentals:
	base_name = '_index_fundamentals_'
	def __init__(self, index_name = 's&p500', index_object = None):
		self.index_object = index_object 
		self.sector_keys = self.index_object.sector_keys 
		self.checklist_id = index_name + self.base_name + 'checklist'
		self.radio_item_id = index_name + self.base_name + 'radio_item'
		self.submit_button_id = index_name + self.base_name + 'show' 
		self.graph_id = index_name + self.base_name + 'graph'

		self.layout = html.Div([
				html.H2(f'fundamentals of {index_name} stocks', style = styles.h2_style),
					dbc.Row([
						html.Main(""" In this graph, you see fundamentals of each stock.
						 	Please choose a sector and the fundamental you wish to see.
						 	 Then push the crunch button. Fundamentals are sorted in ascending order. Hover on each bar to see more info.  """, style = styles.main_style),
						dbc.Col([
							dcc.Checklist(id = self.checklist_id,
				 					options = self.sector_keys, inline = True, value = ['Information Technology'],
				 	 				labelStyle = styles.checklist_label, style = styles.checklist)
								]),
						dbc.Col([
							dcc.RadioItems(id = self.radio_item_id, 
							options = self.index_object.fundamentals_keys, value = 'Market Cap', style = styles.radio_item)
								]),
							]),
						dbc.Button('crunch!', id = self.submit_button_id, n_clicks = 0, style = styles.submit),
						dcc.Loading([
							dcc.Graph(id = self.graph_id, figure = tools.blank_figure(), 
							style = {'width': '90%', 'margin-left': '10px', 'margin-top': '20px'})
									], id = index_name + self.graph_id + '_load', type = 'cube')
						], id = index_name + self.base_name + '_div')
		
		self.callback = callback(Output(self.graph_id, 'figure'), 
				Input(self.submit_button_id, 'n_clicks'),
					State(self.checklist_id, 'value'), 
						State(self.radio_item_id, 'value'),
							prevent_initial_call = True)(self.plot_stock_fundamentals)

	def plot_stock_fundamentals(self, n_clicks, sectors, fundamental):
		"""
		callback to plot fundamentals of stocks screened by 'Sector'
		a radioitem chooses the fundamental to be plotted from 'Market Cap', 'P/E(TTM)' and 'Dividend %'
		"""
		if len(sectors) == 0:
			raise PreventUpdate

		sector_funds = self.index_object.fundamentals[self.index_object.fundamentals['Sector'].isin(sectors)].dropna().sort_values(fundamental)
		len_df = len(sector_funds.index)
		fig = px.bar(sector_funds, y = 'Stock', x = fundamental, 
				labels = {'Stock': 'ticker symbol'},
					hover_name = 'Name', hover_data = [fundamental, 'Sector', 'Stock', 'Latest Price,$'],
					color_continuous_scale = 'Turbo',
			 		color = fundamental, height = int(800*(len_df/40)), template = 'seaborn', orientation = 'h')
	
		fig.layout.font.family = 'Gill Sans'
		fig.layout.font.size = 10
		fig.layout.xaxis.gridcolor = 'black'
		fig.layout.yaxis.gridcolor = 'black'
		fig.layout.xaxis.titlefont.family = 'Gill Sans'
		fig.layout.xaxis.titlefont.size = 30
		fig.layout.xaxis.tickfont.size = 20
		fig.layout.yaxis.titlefont.family = 'Gill Sans'
		fig.layout.yaxis.titlefont.size = 30
		fig.layout.coloraxis.colorbar.tickfont.size = 20
		return fig

# ####################################### #
# SP500 Specific components and callbacks #
# ####################################### #
class XEWDisplay:
	"""
	displays index and equal weight index in a time period 
	this class is formatted using bootstrap components  
	"""
	base_name = '_index_equal_weight_display'
	def __init__(self, index_name = 's&p500', index_start_date = None,
				 index_end_date = None, index_object = None):
		
		self.index_start_date = index_start_date 
		self.index_end_date = index_end_date 
		self.index_object = index_object 
		self.index_name = index_name 

		self.graph_id = index_name + self.base_name + 'graph'
		self.date_picker_id = index_name + self.base_name + 'date_picker'
		self.submit_button_id = index_name + self.base_name + 'submit'

		self.layout = html.Div([
				dbc.Row(
					dbc.Col(
							html.H2(f'market cap & equal weighted {index_name}', style = styles.h2_style_dbc)
					)
				),
				dbc.Row(
					dbc.Col(
						html.Main(f""" This graph displays performance of market cap weighted 
							and equal weighted {index_name} in a time period. Please choose a 
								time period and push the crunch button """, style = styles.main_style_dbc)
					)
				),
				dbc.Row(
					dbc.Col(
						dcc.DatePickerRange(id = self.date_picker_id, min_date_allowed = self.index_start_date, 
							max_date_allowed = self.index_end_date, start_date = self.index_start_date,
								initial_visible_month = self.index_start_date, end_date = self.index_end_date, style = styles.date_picker)
					)
				),
				dbc.Row(
					dbc.Col(
					dbc.Button('crunch!', id = self.submit_button_id, n_clicks = 0, style = styles.submit)
					)
				),
				dbc.Row(
					dbc.Col(
					dcc.Loading([
						dcc.Graph(id = self.graph_id, figure = tools.blank_figure(), 
								style = {'size':10, 'offset': 0, 'lg': 10})
					 ], id = index_name + self.base_name + '_load', type = 'cube')
					),
				)
				], id = index_name + self.base_name + '_div')
		
		self.callback = callback(Output(self.graph_id, 'figure'),
		 							Input(self.submit_button_id, 'n_clicks'),
									 	State(self.date_picker_id, 'start_date'), 
											State(self.date_picker_id, 'end_date'), 
												prevent_initial_call = True)(self.display_index_and_equal_weight)
	
	def display_index_and_equal_weight(self, n_clicks, start_date, end_date):
		start_date, end_date = tools.adjust_dates(start_date, end_date, default_start= self.index_start_date, default_end=self.index_end_date)
		within_dates = (start_date, end_date)
		x_data = tools.choose_dates_lite(self.index_object.x_index, within_dates = within_dates)
		ew_data = tools.choose_dates_lite(self.index_object.ew_index, within_dates = within_dates)
		
		fig = go.Figure()
		fig.add_scatter(x = x_data.index, y = x_data['index_value'],
		 			mode = 'lines', name = self.index_name + ' index', line_color = '#FF00FF')
		fig.add_scatter(x = ew_data.index, y = ew_data['index_value'],
		 			mode = 'lines', name = self.index_name + ' equal weight', line_color = '#800000')
		fig.data[0].showlegend = True 
		fig.layout.height = 600
		fig.layout.xaxis.gridcolor = 'black'
		fig.layout.yaxis.gridcolor = 'black'
		fig.layout.xaxis.title = 'date'
		fig.layout.yaxis.title = 'index'
		fig.layout.font.family = 'Gill Sans'
		fig.layout.font.size = 20
		return fig

# ############################################# #
#  Display Analytics and Performance Components #
# ############################################# #
class PerformanceHist:
	"""
	generates distributions of all returns and display chosen assets using a vertical
		line in the graphs 
	Components: a Bar chart 
	Dropdown menu: for choosing the stock 
	RadioItem: for choosing the date range 
	""" 
	_dates = {'Last Week': 'LAST_WEEK',
				'Last Month': 'LAST_MONTH', 
					'Last Three Months': 'LAST_THREE_MONTHS', 
						'Last Six Months': 'LAST_SIX_MONTHS', 
							'Last Year': 'LAST_YEAR'}
	def __init__(self, hists = None):
		self.fields = hists._fields 
		univ_idx = [idx for idx,field in enumerate(self.fields) if 'UNIVERSE' in field][0]
		self.histograms = hists
		self.hist_id = self.fields[0].split('_')[0] 
		self.base_name = self.hist_id + '_perform_hist'
		self.dropdown_id = self.base_name + '_dropdown'
		self.stock_list = list(getattr(self.histograms, self.histograms._fields[univ_idx]).Name)
		self.radio_id = self.base_name + '_radio'
		self.graph_id = self.base_name + '_graph'
		self.submit_button_id = self.base_name + '_submit'

		self.layout = html.Div([
			html.H2('Performance of stocks compared to all stocks', style = styles.h2_style),
			dbc.Row([
				html.Main(f""" This graph shows a histogram of {self.hist_id}. You can compare 
					different stocks with the entire population. The population comprises all stocks 
						in S & P 500, Russell and Nasdaq indices. Choose you stocks using the dropdown menu.
							Graphs can be generated for different time ranges. Choose the time range using the
								radio item. """, style = styles.main_style), 
				dbc.Col([
					dcc.Dropdown(id = self.dropdown_id, multi = True, searchable=True,
						placeholder='choose stock(s) to compare', options = self.stock_list,
								style = styles.multi_dropdown)
					]),
				dbc.Col([
					dcc.RadioItems(id = self.radio_id, options = list(self._dates.keys()), 
							value = 'Last Week', style = styles.radio_item)
					]),
				]),
				dbc.Button('crunch!', id = self.submit_button_id, n_clicks = 0, style = styles.submit), 
					dcc.Loading([
						dcc.Graph(id = self.graph_id, figure = tools.blank_figure(),
							style = {'width': '90%', 'margin-left': '20px', 'margin-top': '20px'})
								], id = self.base_name + 'load_graph', type = 'cube')
				], id = self.base_name + '_div')
		
		self.callback = callback(Output(self.graph_id, 'figure'), 
			Input(self.submit_button_id, 'n_clicks'), 
				State(self.radio_id, 'value'), 
					State(self.dropdown_id, 'value'), prevet_initial_call = True)(self.plot_performance)

	
	@staticmethod 
	def _close_value_is(df = None, column = None, value = None):
		close_df = df.iloc[(df[column] - value).abs().argsort()[0]]
		return close_df 
	
	@staticmethod
	def generate_arrow_list(annotate_assets = None, hist_assets = None):
		arrow_list = []
		for _,asset in annotate_assets.iterrows():
			close_values = PerformanceHist._close_value_is(df = hist_assets, column = 'Returns',
					value = asset['Return'])
			arrow = {'x': close_values['Returns'], 'y': close_values['Number of Stocks'], 
				'text': asset['Name'], 'showarrow': True, 'arrowhead': 1,'arrowsize': 2, 'arrowwidth': 1,
					'bordercolor':'#D35400', 'borderwidth':3, 'bgcolor':'#FBFCFC',
						'font':{'size':15, 'color':'black'}}
			arrow_list.append(arrow)
		return arrow_list 

	def plot_performance(self, n_clicks, date_key, stocks):
		univ_key = self.hist_id + '_' + self._dates[date_key] + '_UNIVERSE'
		hist_key = self.hist_id + '_' + self._dates[date_key] + '_HIST'
		hist_df = getattr(self.histograms, hist_key)
		univ_df = getattr(self.histograms, univ_key)

		fig = px.bar(hist_df, x = 'Returns', y = 'Number of Stocks', labels = {'Returns': 'return, %', 
					'Number of Stocks': 'number of stocks'}, color = 'Returns', color_continuous_scale='Turbo', 
							hover_data = ['Returns'], template = 'seaborn')
		fig.layout.font.family = 'Gill Sans'
		fig.layout.font.size = 20
		fig.layout.xaxis.gridcolor = 'black'
		fig.layout.yaxis.gridcolor = 'black'
		fig.layout.xaxis.titlefont.family = 'Gill Sans'
		fig.layout.xaxis.titlefont.size = 30
		fig.layout.xaxis.tickfont.size = 20
		fig.layout.yaxis.titlefont.family = 'Gill Sans'
		fig.layout.yaxis.titlefont.size = 30
		fig.layout.coloraxis.colorbar.tickfont.size = 20
		fig.layout.height = 700		
		if stocks is not None and isinstance(stocks, Iterable):
			annotate_assets = univ_df[univ_df['Name'].isin(list(stocks))]
			arrow_list = PerformanceHist.generate_arrow_list(annotate_assets=annotate_assets, hist_assets = hist_df)
			fig.update_layout(annotations = arrow_list)

		return fig
		





		 




	





























	
