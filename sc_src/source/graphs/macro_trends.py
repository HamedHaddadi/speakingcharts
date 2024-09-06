# ##################################### #
# Graph components of macro_trends #
# ##################################### #
import dash_bootstrap_components as dbc 
from ..analytics import macro_trends
from . import components 

index_fed_object = macro_trends.IndexReturnVSFedAsset.load_assets()

index_vs_fed_graph = components.IndexReturnFedAsset(index_fed_object=index_fed_object).layout 

macro_trend_tab = dbc.Tab([index_vs_fed_graph], label = ['MACRO TRENDS'])






