
# ##################################### #
# common components used by all indices #
# ##################################### #

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
				 			options = keys.SECTORS, searchable = True, style = styles.multi_dropdown)
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
		start_date, end_date = tools.adjust_dates(start_date, end_date, default_start = self.index_start_date, default_end=self.index_end_date)
		sector_ret_hist = self.index_object.sector_cumulative_return_history(within_dates = (start_date, end_date))

		if selected_sectors is None:
			raise PreventUpdate 

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

		self.date_picker_id = index_name + self.base_name + 'date_picker'
		self.dropdown_id = index_name + self.base_name + 'dropdow'
		self.graph_id = index_name + self.base_name + 'graph'
		self.submit_button_id = index_name + self.base_name + 'submit'

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
				 			options = [{'label': 'display ' + str(50*count) + ' stocks', 
												'value': 50*count} for count in range(1,11)], style = styles.single_dropdown)
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
	
	def plot_stock_return(self, n_clicks, start_date, end_date, num_stocks):
		start_date, end_date = tools.adjust_dates(start_date, end_date,
				default_start = self.index_start_date, default_end=self.index_end_date)	
		if num_stocks is None:
			raise PreventUpdate 
		investment_df = self.index_object.compute_investment_returns(within_dates = (start_date, end_date), 
						fully_within_date_range= True)
		investment_df['Return'] = investment_df['Return']*100 
		investment_df.sort_values(by = ['Return'], ascending=False, inplace = True)
		investment_df.reset_index(drop = True, inplace = True)
		investment_df = investment_df.iloc[::-1]
		investment_df = investment_df[investment_df.index <= num_stocks]

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
				 					options = keys.SECTORS, inline = True, value = ['Information Technology'],
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
		sector_funds = self.index_object.fundamentals[self.index_object.fundamentals['Sector'].isin(sectors)].dropna().sort_values(fundamental)
		len_df = len(sector_funds.index)
		fig = px.bar(sector_funds, y = 'Stock', x = fundamental, 
				labels = {'Stock': 'ticker symbol'},
					hover_name = 'Name', hover_data = [fundamental, 'Sector', 'Stock'],
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
































	
