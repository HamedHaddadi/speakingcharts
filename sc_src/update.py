
# ################################################## #
# Updates datasets by reading from an input yml file #
# ################################################## #

from source.instruments.indices import SP500, Russell3000
from timeit import default_timer 
import yaml 
import argparse 


def parse_inputs(yml_file):
	try:
		stream = open(yml_file)
		inputs = yaml.safe_load(stream)
	except FileExistsError:
		print('Error reading input file')
	return inputs 

def update_sp500_index(period = '5y', interval = '1d',
		start_date = None, end_date = None, longs_fully_within_date_range = True, **kwargs):
	sp = SP500.pull_assets(period = period, interval = interval, start_date = start_date,
					end_date = end_date, save_data = True)
	sp.generate_sector_mean_return_long(freq = 'M', save_data = True, fully_within_date_range=longs_fully_within_date_range)
	sp.generate_sector_mean_return_long(freq = 'Q', save_data = True, fully_within_date_range=longs_fully_within_date_range)	
	sp.generate_index_fundamentals()
	sp.save()

def update_russell3000_index(period = '5y', interval = '1d',
		start_date = None, end_date = None, longs_fully_within_date_range = True, **kwargs):
	
	ru = Russell3000.pull_assets(period = period, interval = interval, start_date = start_date,
					end_date = end_date, save_data = True)
	ru.generate_sector_mean_return_long(freq = 'M', save_data = True, fully_within_date_range=longs_fully_within_date_range)
	ru.generate_sector_mean_return_long(freq = 'Q', save_data = True, fully_within_date_range=longs_fully_within_date_range)	
	ru.generate_index_fundamentals()
	ru.save()

def update_all(**kwargs):
	update_sp500_index(**kwargs)
	update_russell3000_index(**kwargs)


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description = 'input file')
	parser.add_argument('-filenames', nargs = '*', type = str, help = 'input files')
	args = parser.parse_args()
	for _file in args.filenames:
		inputs = parse_inputs(_file)
		start = default_timer()
		{'sp500': update_sp500_index, 
			'russell3000': update_russell3000_index, 
				'all': update_all}[inputs['asset']](**inputs)
		end = default_timer()
		print(f'finished upading process within {end - start} seconds')

