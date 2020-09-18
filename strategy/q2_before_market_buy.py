# -*- coding: utf-8 -*-
"""
Created on Thu May  7 22:16:26 2020

@author: ksme0
"""

import Kiwoom
import datetime

# you can choose stock and qty
code = '032190'
qty = 2141


app = Kiwoom.QApplication(Kiwoom.sys.argv)
kiwoom = Kiwoom.Kiwoom()
kiwoom.comm_connect()

acc_no = kiwoom.GetLoginInfo("ACCLIST").split(';')[0]
order_type = 'SELL'
deal_type = 'BEFORE_MARKET'

base_1 = datetime.datetime.now().replace(minute=30,second=59,microsecond=900000)
base_2 = datetime.datetime.now().replace(minute=29,second=59,microsecond=850000)
while True:
    now = datetime.datetime.now()
    if now >= base_1:
        kiwoom.send_order(acc_no, order_type, code, qty, deal_type)
        break
    elif now >= base_2:
        kiwoom.send_order(acc_no, order_type, code, qty, deal_type)
    