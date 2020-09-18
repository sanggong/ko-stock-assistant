# -*- coding: utf-8 -*-
"""
config.py
configuration value for this package

"""

# defualt configuration
class config():
    DB = {'USER_ID': 'your_id',
          'NORM_PWD': 'your_pwd',
          'DB_NAME': 'your_db'}
    # In Kiwoom pwd, you must use {%}, {^}, {*} in type special simbol %, ^, *.
    # Because pywinauto(package used in kiwoom login) use %,^,* as special function.
    KIWOOM = {'USER_ID': 'your_id',
              'NORM_PWD': 'your_pwd',
              'CERT_PWD': 'your_pwd'}
    LOG_PATH = 'your_log_path'


# backetest configuration
class configBacktest(config):
    DB = {'USER_ID': 'your_id',
          'NORM_PWD': 'your_pwd',
          'STOCK_DB': 'your_db_where_stock_is_stored',
          'BT_DB': 'your_db_used_in_saving_backtest_result'
          }


# update configuration
class configUpdate(config):
    START_DATE = 'update_start_date'  #'2000-01-02'
    UPDATE_DATE = 'update_last_date'  #'2020-08-08'/None:today
    MANUAL_CHART_TRANSFER = True  # True:yes/False:no
    NUMBER_OF_PROCESS = 1  # Number of process to be used(MAX 2).

    CLOSED_DAYS_EXCEL_PATH = 'closed_day_excel_path'
    PROCESS_PICKLE_PATH = 'file_path_that_update_data_is_saved'
    LOG_PATH = 'update_log_path'

    BLACK_LIST = ['015540']  # stock code with weird data.
    WICS_LC = {10:'에너지',
               15:'소재', 
               20:'산업재', 
               25:'경기관련소비재', 
               30:'필수소비재', 
               35:'건강관리',
               40:'금융', 
               45:'IT', 
               50:'커뮤니케이션서비스', 
               55:'유틸리티'}
    
    WICS_MC = {1010:'에너지',
               1510:'소재',
               2010:'자본재',
               2020:'상업서비스와공급품',
               2030:'운송',
               2510:'자동차와부품',
               2520:'내구소비재와의류',
               2530:'호텔,레스토랑,레저 등',
               2550:'소매(유통)',
               2560:'교육서비스',
               3010:'식품과기본식료품소매',
               3020:'식품,음료,담배',
               3030:'가정용품과개인용품',
               3510:'건강관리장비와서비스',
               3520:'제약과생물공학',
               4010:'은행',
               4020:'증권',
               4030:'다각화된금융',
               4040:'보험',
               4050:'부동산',
               4510:'소프트웨어와서비스',
               4520:'기술하드웨어와장비',
               4530:'반도체와반도체장비',
               4535:'전자와 전기제품',
               4540:'디스플레이',
               5010:'전기통신서비스',
               5020:'미디어와엔터테인먼트',
               5510:'유틸리티'}