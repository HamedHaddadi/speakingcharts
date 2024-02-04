# ##################################### #
# Graph components of asset performance #
# ##################################### #
import dash_bootstrap_components as dbc 
from ..analytics import performance 
from . import components 

histograms = performance.load_distributions()

asset_performance_population = components.PerformanceHist(histograms).layout 


performance_tab = dbc.Tab([asset_performance_population], label = ['PERFORMANCE'])






