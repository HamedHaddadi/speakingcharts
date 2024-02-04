
# ################################################## #
# Updates datasets by reading from an input yml file #
# ################################################## #

from source.instruments.indices import SP500, Russell3000, Russell2000, Nasdaq 
from timeit import default_timer 
import yaml 
import argparse 
import re 

def parse_inputs(yml_file):
	try:
		stream = open(yml_file)
		inputs = yaml.safe_load(stream)
	except FileExistsError:
		print('Error reading input file')
	return inputs 

def update_sp500_index(period = '5y', interval = '1d',
		start_date = None, end_date = None, **kwargs):
	
	print('start updating SP500 index ...')
	sp = SP500.pull_assets(period = period, interval = interval, start_date = start_date,
					end_date = end_date, save_data = True)

	sp.generate_sector_mean_return_long(freq = 'M', save_data = True)
	sp.generate_sector_mean_return_long(freq = 'Q', save_data = True)	
	sp.generate_index_fundamentals()
	sp.add_index()
	sp.save()

def update_russell_index(period = '5y', interval = '1d',
		start_date = None, end_date = None, **kwargs):

	print('start updating Russell2000 and 3000 index ...')
	ru = Russell3000.pull_assets(period = period, interval = interval, start_date = start_date,
					end_date = end_date, save_data = True, cap = kwargs.get('cap', 0))
	ru.generate_sector_mean_return_long(freq = 'M', save_data = True)
	ru.generate_sector_mean_return_long(freq = 'Q', save_data = True)	
	ru.generate_index_fundamentals()
	ru.save()

	ru2000_assets, ru2000_sectors = ru.generate_russell2000_assets()
	ru2000_main_save_path = re.sub('3000', '2000', ru.main_save_path)
	ru2000 = Russell2000(assets = ru2000_assets, sectors = ru2000_sectors, main_save_path = ru2000_main_save_path)
	
	ru2000.save_assets()
	ru2000.generate_sector_mean_return_long(freq='M', save_data = True)
	ru2000.generate_sector_mean_return_long(freq = 'Q', save_data = True)
	ru2000.generate_index_fundamentals()
	ru2000.save()

def update_nasdaq(period = '5y', interval = '1d',
		start_date = None, end_date = None, **kwargs):
	
	print('start updating Nasdaq ...')
	nasdaq = Nasdaq.pull_assets(period = period, interval = interval, start_date = start_date,
					end_date = end_date, save_data = True)
	nasdaq.generate_sector_mean_return_long(freq = 'M', save_data = True)
	nasdaq.generate_sector_mean_return_long(freq = 'Q', save_data = True)	
	nasdaq.generate_index_fundamentals()
	nasdaq.save()	

def update_all(**kwargs):
	update_sp500_index(**kwargs)
	update_russell_index(**kwargs)
	update_nasdaq(**kwargs)

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description = 'input file')
	parser.add_argument('-filenames', nargs = '*', type = str, help = 'input files')
	args = parser.parse_args()
	for _file in args.filenames:
		inputs = parse_inputs(_file)
		start = default_timer()
		{'sp500': update_sp500_index, 
				'russell': update_russell_index, 
					'nasdaq': update_nasdaq,
						'all': update_all}[inputs['asset']](**inputs)
		end = default_timer()
		print(f'finished upading process within {end - start} seconds')

