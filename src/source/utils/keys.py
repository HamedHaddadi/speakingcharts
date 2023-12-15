
from os import path 


DATA_PATH = '/Users/hamedhaddadi/Documents/FinanceProject/market_glance_project/data'
FRED_API='0fd93aa0a7b8cd16651fcb6801a13708'
RUSSELL3000_PDF = '/Users/hamedhaddadi/Documents/FinanceProject/Documents/ru3000_membershiplist_20220624_0.pdf'
RUSSELL3000_CSV = 'Russell3000_Companies.csv'

# SP500
SP500_SUBDIR = 'SP500_12_13'
SP500_ASSETS= 'SP500_for_5y_intervals_1d_pulled_on_2023-12-13-10-58.pkl'
SP500_SECTORS= 'SP500_sectors_pulled_on_2023-12-13-10-58.dat'
SP500_INFO='SP500_info_pulled_on_2023-12-13-10-58.csv'
SP500_INDEX_FILE='SP500_index_2023-12-13-11-03.pkl'

SP500_SECTOR_RETURN_LM='SP500_sector_return_long_M_sampling_2023-12-13.parquet'
SP500_SECTOR_RETURN_LQ='SP500_sector_return_long_Q_sampling_2023-12-13.parquet'
SP500_SECTOR_FUNDAMENTALS='SP500_sector_fundamentals_pulled_on_2023-12-13-10-58.parquet'
SP500_FUNDAMENTALS='SP500_fundamentals_pulled_on_2023-12-13-10-58.parquet'

#RUSSELL3000
RUSSELL3000_SUBDIR='RUSSELL3000_12_13'
RUSSELL3000_ASSETS= 'Russell3000_for_5y_intervals_1d_pulled_on_2023-12-13-13-02.pkl'
RUSSELL3000_SECTORS= 'Russell3000_sectors_pulled_on_2023-12-13-13-02.dat'
RUSSELL3000_INFO='Russell3000_info_pulled_on_2023-12-13-13-02.csv'
RUSSELL3000_INDEX_FILE='Russell3000_index_2023-12-13-13-39.pkl'

RUSSELL3000_SECTOR_RETURN_LM='Russell3000_sector_return_long_M_sampling_2023-12-13.parquet'
RUSSELL3000_SECTOR_RETURN_LQ='Russell3000_sector_return_long_M_sampling_2023-12-13.parquet'
RUSSELL3000_SECTOR_FUNDAMENTALS='Russell3000_sector_fundamentals_pulled_on_2023-12-13-13-02.parquet'
RUSSELL3000_FUNDAMENTALS='Russell3000_fundamentals_pulled_on_2023-12-13-13-02.parquet'

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
