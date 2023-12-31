
from os import path 


DATA_PATH = '/Users/hamedhaddadi/Documents/FinanceProject/speaking_charts_datasets'
FRED_API='0fd93aa0a7b8cd16651fcb6801a13708'
RUSSELL3000_PDF = '/Users/hamedhaddadi/Documents/FinanceProject/Documents/ru3000_membershiplist_20220624_0.pdf'
RUSSELL3000_CSV = 'Russell3000_Companies.csv'
NASDAQ_CSV= 'Nasdaq_Companies.csv'

# SP500
SP500_SUBDIR = 'SP500-12-31'
SP500_ASSETS= 'SP500_for_5y_intervals_1d_pulled_on_2023-12-31-09-31.pkl'
SP500_SECTORS= 'SP500_sectors_pulled_on_2023-12-31-09-31.dat'
SP500_INDEX_CLASS_FILE='SP500_index_2023-12-31-09-31.pkl'

SP500_SECTOR_RETURN_LM='SP500_sector_return_long_M_sampling_2023-12-31-09-31.parquet'
SP500_SECTOR_RETURN_LQ='SP500_sector_return_long_Q_sampling_2023-12-31-09-31.parquet'
SP500_SECTOR_FUNDAMENTALS='SP500_sector_fundamentals_pulled_on_2023-12-31-09-31.parquet'
SP500_FUNDAMENTALS='SP500_fundamentals_pulled_on_2023-12-31-09-31.parquet'

SP500_INDEX_FILENAME='sp_index_pulled_on_2023-12-31-09-31.csv'
SPXEW_INDEX_FILENAME='spxew_index_pulled_on_2023-12-31-09-31.csv'

#RUSSELL3000
RUSSELL3000_SUBDIR='RUSSELL3000-12-31'
RUSSELL3000_ASSETS= 'Russell3000_for_5y_intervals_1d_pulled_on_2023-12-31-09-31.pkl'
RUSSELL3000_SECTORS= 'Russell3000_sectors_pulled_on_2023-12-31-09-31.dat'
RUSSELL3000_INDEX_CLASS_FILE='Russell3000_index_2023-12-31-09-31.pkl'

RUSSELL3000_SECTOR_RETURN_LM='Russell3000_sector_return_long_M_sampling_2023-12-31-09-31.parquet'
RUSSELL3000_SECTOR_RETURN_LQ='Russell3000_sector_return_long_Q_sampling_2023-12-31-09-31.parquet'
RUSSELL3000_SECTOR_FUNDAMENTALS='Russell3000_sector_fundamentals_pulled_on_2023-12-31-09-31.parquet'
RUSSELL3000_FUNDAMENTALS='Russell3000_fundamentals_pulled_on_2023-12-31-09-31.parquet'

#RUSSELL2000 
RUSSELL2000_SUBDIR='RUSSELL2000-12-31'
RUSSELL2000_ASSETS= 'Russell2000_for_5y_intervals_1d_pulled_on_2023-12-31-09-31.pkl'
RUSSELL2000_SECTORS= 'Russell2000_sectors_pulled_on_2023-12-31-09-31.dat'
RUSSELL2000_INDEX_CLASS_FILE='Russell2000_index_2023-12-31-09-31.pkl'

RUSSELL2000_SECTOR_RETURN_LM='Russell2000_sector_return_long_M_sampling_2023-12-31-09-31.parquet'
RUSSELL2000_SECTOR_RETURN_LQ='Russell2000_sector_return_long_Q_sampling_2023-12-31-09-31.parquet'
RUSSELL2000_SECTOR_FUNDAMENTALS='Russell2000_sector_fundamentals_pulled_on_2023-12-31-09-31.parquet'
RUSSELL2000_FUNDAMENTALS='Russell2000_fundamentals_pulled_on_2023-12-31-09-31.parquet'

#NASDAQ
NASDAQ_SUBDIR='NASDAQ-12-31'
NASDAQ_ASSETS= 'Nasdaq_for_5y_intervals_1d_pulled_on_2023-12-31-09-31.pkl'
NASDAQ_SECTORS= 'Nasdaq_sectors_pulled_on_2023-12-31-09-31.dat'
NASDAQ_INDEX_CLASS_FILE='Nasdaq_index_2023-12-31-09-31.pkl'

NASDAQ_SECTOR_RETURN_LM='Nasdaq_sector_return_long_M_sampling_2023-12-31-09-31.parquet'
NASDAQ_SECTOR_RETURN_LQ='Nasdaq_sector_return_long_Q_sampling_2023-12-31-09-31.parquet'
NASDAQ_SECTOR_FUNDAMENTALS='Nasdaq_sector_fundamentals_pulled_on_2023-12-31-09-31.parquet'
NASDAQ_FUNDAMENTALS='Nasdaq_fundamentals_pulled_on_2023-12-31-09-31.parquet'


TIME_PERIODS = {'yesterday': '1d', 
					'last week': '1w', 
						'last month': '1m', 
							'last 6 months': '6m', 
								'year to date': 'ytd', 
									'1 year': '1y'}
RESHAPES = {50: (5,10), 
				100: (10,10), 
					200: (20,10), 
						300: (15,20), 
							400: (20,20), 
								500: (20, 25)}

SECTOR_KEYS = {'Healthcare': 'Health Care', 
                    'Consumer Cyclical': 'Consumer Discretionary',
                        'Technology': 'Information Technology', 
                            'Consumer Defensive': 'Consumer Staples',
                                'Communication Services': 'Communication Services', 
                                    'Basic Materials': 'Materials', 
                                        'Industrials': 'Industrials', 
                                            'Financial Services': 'Financials', 
                                                'Energy':'Energy',
                                                    'Utilities':'Utilities', 
                                                        'Real Estate': 'Real Estate', None: 'No Sector'}

SECTORS = [key for key in SECTOR_KEYS.values() if 'No Sector' not in key]
