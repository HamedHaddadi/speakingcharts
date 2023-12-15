
import argparse
from source.instruments.indices import SP500
from source.utils.market_data import pull_fundamentals, generate_fundamentals_from_file, generate_russell3000_companies 


def update_sp500():
	sp = SP500.get_history(period = '5y', interval = '1d', sector = None, 
                        start_date = None, end_date = None, save_data = True, 
                            benchmark = None)
	print('updating sector return long ...')
	sp.generate_sector_mean_return_long(freq = 'M', save_data = True)
	sp.generate_sector_mean_return_long(freq = 'Q', save_data = True)

def update_fundamentals(source = None, stocks = None):
	{'sp500': pull_fundamentals}[stocks](source = 'finviz', stock_list = 'sp500')

def generate_fundamental_from_file(fileinfo, sp = False):
	"""
	using the file name is enough; the path is the default path to the 
		fundamental file
	will compute market cap, pe ratio and dividend percet 
	"""
	generate_fundamentals_from_file(fileinfo, sp = sp)
	 

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description = 'input reader for data generation')
	parser.add_argument('--update_sp500', action = 'store_true')
	parser.add_argument('--update_fundamentals_sp500', action = 'store_true')
	parser.add_argument('--from_yahoo', action = 'store_true', help = 'uses yfinance for data source')
	parser.add_argument('--fundamental_from_file', type = str, action = 'store', nargs = '?', help = 'enter the file information of the latest fundamental file')
	# the following input must be added if fundamental_from_file is active
	parser.add_argument('--sp_fundamentals', action = 'store_true', help = 'if entered, it will compute sp500 sector fundamentals')
	parser.add_argument('--ru3000_list', action = 'store_true', help = 'generates russell3000 company list')

	args = parser.parse_args()

	if args.update_sp500:
		update_sp500()
	
	if args.update_fundamentals_sp500:
		stocks = 'sp500'
		source = 'finviz'
		if args.from_yahoo:
			source = 'yahoo'		
		update_fundamentals(source = source, stocks = 'sp500')
	
	if args.fundamental_from_file is not None:
		generate_fundamental_from_file(args.fundamental_from_file, sp = args.sp_fundamentals)
	
	if args.ru3000_list:
		generate_russell3000_companies()
	


