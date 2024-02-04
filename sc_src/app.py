
import dash 
import dash_bootstrap_components as dbc 
from dash import html 
from source.graphs.sp500 import sp500_tab
from source.graphs.russell3000 import russell3000_tab
from source.graphs.russell2000 import russell2000_tab  
from source.graphs.nasdaq import nasdaq_tab
from source.graphs.performance import performance_tab

app = dash.Dash(__name__, external_stylesheets = [dbc.themes.LUX])
server = app.server 

app.layout = html.Div([
	html.H1('Markets at a Glance using interactive charts'), 
		html.Br(),
			dbc.Tabs([
				sp500_tab, 
					russell3000_tab,
						russell2000_tab,  
							nasdaq_tab,
								performance_tab], id = 'all all tabs')
	], id = 'app layout')

if __name__ == '__main__':
	app.run_server(debug = True, use_reloader = True)
