# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 15:02:01 2020

@author: ksme0
"""
import datetime

from kostock import backtester
from kostock.stockdb import StockDB
from kostock.configurer import Configurer

list_data = []
temp_codes = []
date = None
bt = backtester.BackTester()

with open('logs/q1_suprise_com.txt', 'r') as file:
    for line in file:
        line = line.split('/')
        name = line[0].strip()
        if name == 'None':
            continue
        code = db.conv_name_to_code(name)
        if code is None:
            continue
        prev_date = date
        date = datetime.datetime.strptime(line[1].strip(), '%Y-%m-%d %H:%M:%S')
        if prev_date == date and code in temp_codes:
            continue
        elif prev_date == date and code not in temp_codes:
            temp_codes.append(code)
        else:  # prev_date != date
            temp_codes = []
            temp_codes.append(code)
        
        bt.insert([code, date, '1'])

result = bt.back_test()
result.show_summary()
result.show_graph()
