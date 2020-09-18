# -*- coding: utf-8 -*-
"""
##################### Kiwoom.py ########################

- This is Class file for using Kiwoom Investment Open API.
- Some method operate transmitting Kiwwom server and receiving event.
  (setting value function -> transmit signal -> waiting event -> get data) 
- This class has functions of order, lookup data, etc.
 
########################################################
"""

import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import time
import datetime
from pandas import DataFrame as df
import pandas as pd
import numpy as np
from multiprocessing.pool import ThreadPool
from threading import Thread

TR_REQ_INTERVAL_1_SEC = 1       # TR5 per 1sec / unit : [s]
TR_REQ_INTERVAL_70_SEC = 50     # TR100 per 70sec / unit : [s]
TR_REQ_INTERVAL_600_SEC = 110   # TR700 per 600sec / unit : [s]

LIMIT_TR_COUNT = 99

EVENT_RESPONSE_TIME_LIMIT = 6000  # ms
LOGIN_RESPONSE_TIME_LIMIT = 15000 # ms

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        self._set_signal_slots()
        self._tr_count = int(0)
        self._scr_no = '0'
        self._cur_order_list = {}
        
        self._current_timer = None
        self.login_event_loop = QEventLoop()
        self.tr_event_loop = QEventLoop()
        self.condi_load_event_loop = QEventLoop()
        self.condition_event_loop = QEventLoop()

    ########### EVENT RELATED METHOD START #################
    def _set_signal_slots(self):
        '''
        EVENT SLOT - usually used in receiveing data.
        '''
        self.OnEventConnect.connect(self._event_connect) # comm_connect -> WAITING EVENT FROM SERVER
        self.OnReceiveTrData.connect(self._receive_tr_data) # _set_input_value -> _comm_rq_data -> WAITING EVENT FROM SERVER
        self.OnReceiveConditionVer.connect(self._receive_condition_ver) # _get_condition_load -> WAITING EVENT FROM SERVER
        self.OnReceiveTrCondition.connect(self._receive_tr_condition) # _send_condition -> WAITING EVENT FROM SERVER
        self.OnReceiveChejanData.connect(self._receive_chejan_data) # send_order -> NO WAITING
    
    def _event_connect(self, err_code):
        '''
        # Event Connect Method # 
        CALLED BY [comm_connect] 
        event method after you require login.
        exit login_event_loop
        * variable 
        err_code [int] : [0] success 
                         [-100] user info exchange fail
                         [-101] server connect fail
                         [-102] version process fail
        '''
        self.login_event_loop.exit()
    
    
    def _receive_tr_data(self, scr_no, rq_name, tr_code, record, continuous,
                         unused1, unused2, unused3, unused4):
        '''
        # Event Connect Method #
        CALLED BY [_comm_rq_data]
        event method after you require to look up tr data
        (1) check whether continuous data is remained or not 
        (2) get data on depending the rq_name
        (3) exit tr_event_loop

        * variable
        scr_no [str] : screen number
        rq_name [str] : user-defined instruction name (ex. opt10001_req)
        tr_code [str] : tr code name (ex. opt10001)
        record [str] : record name, but right now, it is not used
        continuous [str] : represent exsitence of remained data
                           ['0'] no remained data
                           ['2'] exist remained data
        unused1-4 : unused
        
        * output (not return)
        diffrent value depending on the rq_name method 
        '''
        self._disconnect_real_data(scr_no)

        if continuous == '2':
            self.remained_data = True
        else:
            self.remained_data = False

        if rq_name == 'opt10001_req':
            self._get_opt10001(rq_name, tr_code)
        elif rq_name == "opt10060_req":
            self._get_opt10060(rq_name, tr_code)
        elif rq_name == "opt10081_req":
            self._get_opt10081(rq_name, tr_code)
        elif rq_name == "opt10086_req":
            self._get_opt10086(rq_name, tr_code)

        self.tr_event_loop.exit()
        
        
    def _receive_condition_ver(self, ret_val, msg):
        '''
        # Event Connect Method #
        CALLED BY [_get_condition_load]
        event method after you require to look up your own condition name in Kiwoom
        exit condi_load_event_loop
        * variable
        ret_val [long] : [1] success
                         [rest] fail
        '''
        self.condi_load_event_loop.exit()
  
    
    def _receive_tr_condition(self, scr_no, code_list, condi_name, condi_idx, continuous):
        '''
        # Event Connect Method #
        CALLED BY [_send_condition]
        event method after you require to look up stocks code that meet the condition
        (1) make code list
        (2) exit condition_event_loop
        
        * variable
        scr_no [str] : screen number
        code_list [str] : stock codes in series str connected with ';'
                          (ex. code_one;code_two;...;)
        condi_name [str] : input condition name
        condi_idx [int] : input condition index
        continuous [int] : continuous lookup
                           [2] continuous lookup
                           [0] no continuous lookup
        * output (not return)
        self.condi_list [one-dim str]
        '''
        self.condi_list = []
        self.condi_list = code_list.split(';')
        self.condition_event_loop.exit()
        
    def _receive_chejan_data(self, gubun, item_cnt, fid_list):
        '''
        # Event Connect Method #
        CALLED BY [send_order]
        
        * variable
        gubun [str] - [0] 
                      [1]
        item_cnt [int] - number of item
        fid_list [str] - fid list (different value depending on gubun)
                         [gubun 0] 9201;9203;9205;9001;912;913;302;900;901;902;
                                   903;904;905;906;907;908;909;910;911;10;27;28;
                                   914;915;938;939;919;920;921;922;923;949;10010;
                                   969;819
                         [gubun 1] 9201;9001;917;916;302;10;930;931;932;933;945;
                                   946;950;951;27;28;307;8019;957;958;918;990;991;
                                   992;993;959;924;10010;25;11;12;306;305;970
        '''
        if gubun == 0:
            order_no = self.GetChejanData(9203)
            acc_no = self.GetChejanData(9201)
            stock_code = self.GetChejanData(9001)
            stock_name = self.GetChejanData(302)
            total_qty = self.GetChejanData(900)
            conc_qty = self.GetChejanData(911)
            remained_qty = self.GetChejanData(902)
            conc_price = format(self.GetChejanData(910), ',')
            org_price = format(self.GetChejanData(901), ',')
            conc_time = self.GetChejanData(908) #HHMMSSMS
            if len(conc_time) == 6: #HHMMSS
                conc_time = conc_time[0:2] + ':' + conc_time[2:4] + ':' + conc_time[4:6]
            elif len(conc_time) == 8: #HHMMSSMS
                conc_time = conc_time[0:2] + ':' + conc_time[2:4] + ':' + conc_time[4:6] + '.' + conc_time[6:8]
            
            #print()
            if order_no not in self._cur_order_list: # order acceptance
               # print(f"[INFO] {conc_time} Order({(order_no)}) is accepted")
               # print(f"       {stock_name}({stock_code}) {org_price}WON {total_qty}BLOCKS")
                self._cur_order_list[order_no] = [stock_code, org_price, total_qty]
            else: # order conclusion
               # print(f"[INFO] {conc_time} Order({(order_no)}) is concluded")
               # print(f"       {stock_name}({stock_code}) {conc_qty}BLOCKS for {conc_price}WON")
                if remained_qty == 0:
                    del(self._cur_order_list[order_no])
    ########### EVENT RELATED METHOD END #################      

    
    
    ########### INTERNAL METHOD START ##############
    def _set_input_value(self, sid, value):
        '''
        for looking up tr data, set input value
        
        * input
        sid [str] : input name described in tr
        value [str] : input value on depending the input name
        '''
        self.SetInputValue(sid, value)

    def _comm_rq_data(self, rq_name, tr_code, continuous, scr_no):
        '''
        CALL EVENT [_receive_tr_data]
        if set input value is completed, 
        you should use this method to receive data
        
        * input
        rq_name [str] : user-defined instruction name (ex. opt10001_req)
        tr_code [str] : tr code name (ex. opt10001)
        continuous [int] : [0] fist call 
                           [2] from the second call, if remained data exist,
        src_no [str] : screen number
        '''
        condition = self.CommRqData(rq_name, tr_code, continuous, scr_no)
        if condition == 0: # lookup success
            if self._current_timer:
                self._current_timer.stop()
                self._current_timer.deleteLater()
            self._current_timer = QTimer()
            self.tr_event_loop = QEventLoop()
            self._current_timer.singleShot(EVENT_RESPONSE_TIME_LIMIT,
                                           self.tr_event_loop.quit)
            self.tr_event_loop.exec_()

        self._tr_count += 1
        if self._tr_count % 5 == 0:
            #print("[INFO] Sleep 1(s) because of tr count")
            time.sleep(TR_REQ_INTERVAL_1_SEC)
        if (self._tr_count % 100) == 0:
            #print("[INFO] Sleep 50(s) because of tr count")
            time.sleep(TR_REQ_INTERVAL_70_SEC)
        if self._tr_count == 700:
            #print("[INFO] Sleep 110(s) because of tr count")
            time.sleep(TR_REQ_INTERVAL_600_SEC)

        return condition #0:lookup success, -200:lookup fail

    def _get_repeat_cnt(self, tr_code, rq_name):
        '''
        AFTER EVENT [_receive_tr_data]
        this method count and return number of receiving tr data.
        
        * input
        tr_code [str] : tr code name (ex. opt10001)
        rq_name [str] : user-defined instruction name (ex. opt10001_req)
        
        * output
        rcnt [int] : number of receiving tr data (repeat count)
        '''
        rcnt = self.GetRepeatCnt(tr_code, rq_name)
        return rcnt 
    
    def _get_comm_data(self, tr_code, rq_name, idx, item):
        '''
        AFTER EVENT [_receive_tr_data]
        this method get tr data correponding item(attribute of tr data).
        
        * input
        tr_code [str] : tr code name (ex. opt10001)
        rq_name [str] : user-defined instruction name (ex. opt10001_req)
        idx [int] : index of tr data repeat (output of _get_repeat_cnt)
        item [str] : attribute in tr data
        
        * output
        data.strip() [str] : attribute value corresponding item in tr data
        '''
        data = self.GetCommData(tr_code, rq_name, idx, item)
        return data.strip()
    
    def _get_comm_data_ex(self, tr_code, rq_name):
        data = self.GetCommDataEx(tr_code, rq_name)
        return data
    
    def _get_condition_load(self):
        '''
        CALL EVENT [_receive_condition_ver]
        for getting user conditions, this method is used.
        '''
        ret_val = self.GetConditionLoad()
        if ret_val == 1:  # condition lookup require success
            if self._current_timer:
                self._current_timer.stop()
                self._current_timer.deleteLater()
            self._current_timer = QTimer()
            self.condi_load_event_loop = QEventLoop()
            self._current_timer.singleShot(EVENT_RESPONSE_TIME_LIMIT, 
                                           self.condi_load_event_loop.quit)
            self.condi_load_event_loop.exec_()
        return ret_val # 1:condition lookup require success, {rest}:fail

    def _get_condition_name_list(self):
        '''
        AFTER EVENT [_receive_condition_ver]
        this method get user-defined condition name list.
        
        * output
        idx_name_list [two-dim str] : user defined condition list consisting of index, name
                                      (format : [[condition index, condition name], ...])
        '''
        condi_info_list_str = self.GetConditionNameList()
        # conditional expression : 0^condition_one;1^condition_two;...;
        idx_name_list = []
        condi_info_list = condi_info_list_str.split(';') 
        for condi_info in condi_info_list[:-1]:
            idx_name = condi_info.split('^')
            idx = idx_name[0]
            name = idx_name[1]
            idx_name_list.append([idx, name])
        return idx_name_list
     
    def _send_condition(self, scr_no, condi_name, condi_idx, search_opt):
        '''
        CALL EVENT [_receive_tr_condition]
        this method transmit signal to get stock code list 
        that meet input conditon name and index.
        
        * input 
        scr_no [str] : screen number
        condi_name [str] : condition name used to get stock code list
        condi_idx [int] : condition index used to get stock code list
        search_opt [int] : lookup division option
                           [0] condition search
                           [1] real-time condition search
        '''
        ret_val = self.SendCondition(scr_no, condi_name, condi_idx, search_opt)
        if ret_val == 1: # stock lookup that meets condition success
            if self._current_timer:
                self._current_timer.stop()
                self._current_timer.deleteLater()
            self._current_timer = QTimer()
            self.condition_event_loop = QEventLoop()
            self._current_timer.singleShot(EVENT_RESPONSE_TIME_LIMIT, 
                                           self.condition_event_loop.quit)            
            self.condition_event_loop.exec_()
        return ret_val # 1:stock conditon lookup success {rest}:fail

    def _get_opt10001(self, rq_name, tr_code):
        '''
        AFTER EVENT [_receive_tr_data].
        this method get tr 10,001 data (stock code, name, market cap).
        * input
        rq_name [str] : user-defined instruction name (ex. opt10001_req)
        tr_code [str] : tr code name (ex. opt10001)
        * output (not return)
        self.d10001[DataFrame] : index:stock code, columns:stock name, market cap.
        '''
        code = self._get_comm_data(tr_code, rq_name, 0, "종목코드")
        name = self._get_comm_data(tr_code, rq_name, 0, "종목명")
        cap = self._get_comm_data(tr_code, rq_name, 0, "시가총액")

        self.d10001.loc['code'] = (name, cap)
        #self.d10001['code'].append(code)
        #self.d10001['name'].append(name)
        #self.d10001['market_cap'].append(cap)
    
    def _get_opt10060(self, rq_name, tr_code):   
        '''
        AFTER EVENT [_receive_tr_data]
        this method get tr 10,060 data (daily investor chart data).
        :PARAM :rq_name[str] user-defined instruction name (ex. opt10001_req)
        :tr_code[str] tr code name (ex. opt10001)
        :OUTPUT(not return)
        :self.d10060[(, 17) list] 0-date('%Y%m%d') 4-indi 5-fore 6-inst
        '''
        data = self._get_comm_data_ex(tr_code, rq_name)
        if data:
            self.d10060.extend(data)
        '''
        data_cnt = self._get_repeat_cnt(tr_code, rq_name)
        for i in range(data_cnt):
            date = self._get_comm_data(tr_code, rq_name, i, "일자")
            fore = self._get_comm_data(tr_code, rq_name, i, "외국인투자자")
            inst = self._get_comm_data(tr_code, rq_name, i, "기관계")
            indi = self._get_comm_data(tr_code, rq_name, i, "개인투자자")
            data = [[date, '1', '2', '3', indi, fore, inst]]
            self.d10060.extend(data)
        '''
    def _get_opt10081(self, rq_name, tr_code):   
        '''
        AFTER EVENT [_receive_tr_data]
        this method get tr 10,081 data (daily ohlc chart data).
        :PARAM :rq_name[str] user-defined instruction name (ex. opt10001_req)
        :tr_code[str] tr code name (ex. opt10001)
        :OUTPUT(not return)
        :self.d10081[(, 15) list] 1-close 2-volume 3-volume_price 4-date('%Y%m%d')
        5-open 6-high 7-low 
        '''
        data = self._get_comm_data_ex(tr_code, rq_name)
        if data:
            self.d10081.extend(data)
        '''
        data_cnt = self._get_repeat_cnt(tr_code, rq_name)
        for i in range(data_cnt):
            date = self._get_comm_data(tr_code, rq_name, i, "일자")
            p_open = self._get_comm_data(tr_code, rq_name, i, "시가")
            p_close = self._get_comm_data(tr_code, rq_name, i, "현재가")
            p_high = self._get_comm_data(tr_code, rq_name, i, "고가")
            p_low = self._get_comm_data(tr_code, rq_name, i, "저가")
            volume_q = self._get_comm_data(tr_code, rq_name, i, "거래량")
            volume_p = self._get_comm_data(tr_code, rq_name, i, "거래대금")
            data = [['', p_close, volume_q, volume_p, date, p_open, p_high, p_low]]
            self.d10081.extend(data)
        
            date = datetime.datetime.strptime(date, '%Y%m%d').date()
            openv  = int( openv.replace('--', '-', 1))
            close  = int( close.replace('--', '-', 1))
            high   = int(  high.replace('--', '-', 1))
            low    = int(   low.replace('--', '-', 1))
            volume = int(volume.replace('--', '-', 1))

            self.d10081.append((date, openv, close, high, low, volume), ignore_index=True)
            #self.d10081.loc[date] = (openv, close, high, low, volume)
            #self.d10081['date'].append(date)
            #self.d10081['open'].append(openv)
            #self.d10081['close'].append(close)
            #self.d10081['high'].append(high)
            #self.d10081['low'].append(low)
            #self.d10081['volume'].append(volume)
        '''
        
    def _get_opt10086(self, rq_name, tr_code):
        '''
        AFTER EVENT [_receive_tr_data].
        this method get tr 10,086 data (trade trend by investor)
        * input
        rq_name [str] : user-defined instruction name (ex. opt10001_req)
        tr_code [str] : tr code name (ex. opt10001)
        * output (not return)
        self.d10086 [DataFrame] : index:date, columns:individual, institution, foreigner quantity,
        '''        
        data = self._get_comm_data_ex(tr_code, rq_name)
        self.d10086.extend(data)
        '''
        data_cnt = self._get_repeat_cnt(tr_code, rq_name)
        for i in range(data_cnt):
            date = self._get_comm_data(tr_code, rq_name, i, "날짜")
            fore = self._get_comm_data(tr_code, rq_name, i, "외인순매수")
            inst = self._get_comm_data(tr_code, rq_name, i, "기관순매수")
            indi = self._get_comm_data(tr_code, rq_name, i, "개인순매수")

            date = datetime.datetime.strptime(date, '%Y%m%d').date()
            fore = int(fore.replace('--', '-', 1))#.replace('+-', '+', 1))
            inst = int(inst.replace('--', '-', 1))#.replace('+-', '+', 1))
            indi = int(indi.replace('--', '-', 1))#.replace('+-', '+', 1))

            self.d10086.loc[date] = (fore, inst, indi)
            #self.d10086['date'].append(date)
            #self.d10086['fore'].append(fore)
            #self.d10086['inst'].append(inst)
            #self.d10086['indi'].append(indi)
        '''
    def _disconnect_real_data(self, scr_no):
        '''
        disconnect receiving real data by disconnecting screen
        :param scr_no:[str]connected screen number
        '''
        self.DisconnectRealData(scr_no)

    def _login_input(self, user_id, norm_pwd, cert_pwd, is_mock):
        '''
        Insert Login information into kiwoom gui login window.
        :param user_id:[str] kiwoom investor user id
        :param norm_pwd:[str] normal passward
        :param cert_pwd:[str] certification passward for real server
        :param is_mock:[bool] whether you login mock server(True) or not(False)
        '''
        import pywinauto
        # sys.coinit_flags=0
        while True:
            procs = pywinauto.findwindows.find_elements()
            for proc in procs:
                if proc.name == 'Open API Login':
                    break
            if proc.name == 'Open API Login':
                break
        login_app = pywinauto.Application().connect(process=proc.process_id)
        login_dig = login_app.OpenAPILogin
        login_dig.Edit1.send_keystrokes(user_id)
        login_dig.Edit2.send_keystrokes(norm_pwd)
        if is_mock:
            if login_dig.Edit3.is_enabled():
                login_dig.Button5.click()  # check mock invest server mode
            login_dig.Edit2.send_keystrokes('{ENTER}')
        else:
            if not login_dig.Edit3.is_enabled():
                login_dig.Button5.click()  # uncheck mock invest server mode
            login_dig.Button5.uncheck()
            login_dig.Edit3.send_keystrokes(cert_pwd)
            login_dig.Edit3.send_keystrokes('{ENTER}')
        return proc.process_id
    ########### INTERNAL METHOD END ##############        
    
    
    ########### USER-USED METHOD START ##############

    def manual_login(self, user_id, norm_pwd, cert_pwd=None, is_mock=True):
        '''
        Manual log-in kiwoom invest server function. if it takes LOGIN_RESPONSE_TIME_LIMIT to login
        for some reasons, login process will be terminated.
        :param user_id:[str] kiwoom investor user id
        :param norm_pwd:[str] normal passward
        :param cert_pwd:[str] certification passward for real server
        :param is_mock:[bool] whether you login mock server(True) or not(False)
        '''
        pool = ThreadPool(processes=1)
        login_th = pool.apply_async(self._login_input,
                                    kwds={'user_id': user_id, 'norm_pwd': norm_pwd,
                                          'cert_pwd': cert_pwd, 'is_mock': is_mock})
        '''
        login_th = Thread(target=self._login_input,
                          kwargs={'user_id': user_id, 'norm_pwd': norm_pwd, 'cert_pwd': cert_pwd,
                                  'is_mock': is_mock})
        login_th.daemon = True
        login_th.start()
        '''
        self.comm_connect()
        if not self.get_connect_state():
            login_pid = login_th.get()
            kill_cmd = 'taskkill /f /pid {0}'.format(login_pid)
            os.system(kill_cmd)

    def comm_connect(self):
        '''
        CALL EVENT [_event_connect]
        open kiwoom login window
        '''
        self.CommConnect()
        
        if self._current_timer:
            self._current_timer.stop()
            self._current_timer.deleteLater()
        self._current_timer = QTimer()
        self.login_event_loop = QEventLoop()   
        self._current_timer.singleShot(LOGIN_RESPONSE_TIME_LIMIT,
                                       self.login_event_loop.quit)
        self.login_event_loop.exec_()

    #####################################################
    def get_connect_state(self):
        '''
        :return:[bool]connect state
        '''
        ret = self.GetConnectState()
        if ret == 1:
            return True
        else:
            return False

    #####################################################
    def get_login_info(self, param):
        '''
        :PARAM :[str]info {"ACCOUNT_CNT" - number of account connected by id,
        "ACCLIST"or"ACCNO" - account list separated by ';',
        "USER_ID" - user id, "USER_NAME" - user name,
        "KEY_BSECGB" - whether to cancel keyboard security (0-normal, 1-canceled),
        "FIREW_SECGB" - whether to set up a firewall (0-not set, 1-turn on, 2-turn off),
        "GetServerGubun" - connection server classification (1-mock server, rest-real server)}
        :return:[str]info return value corresponding PARAM
        '''
        info = self.GetLoginInfo(param)
        return info

    ########################################################
    def get_code_list_by_market(self, market):
        '''
        this method get stock code list by market.
        
        * input
        market [str] : market code
                 ['0'] kospi
                 ['10'] kosdaq
                 ['8'] ETF
                 [NULL] all market code
        
        * output
        code_list [one-dim str] : stock code list
        '''
        code_list = self.GetCodeListByMarket(market)
        code_list = code_list.split(';')
        # format : code_one;code_two;code_three;...;
        return code_list[:-1]

    ########################################################
    def get_master_code_name(self, *str_code_list):
        '''
        this method get stock name corresponding stock code.
        
        * input
        *str_code_list [unpacking list str] : stock code list 
        
        * output
        name_list [one-dim str] : stock name list
        '''
        name_list = []
        for str_code in str_code_list:
            name = self.GetMasterCodeName(str_code)
            name_list.append(name)
        return name_list

    ########################################################
    def get_condition_search_result(self, condi_key):
        '''
        this method return stock code list that meet user-defined conditional expression.
        %screen number : '0150'
        * input
        condi_key [str(name) or int(idx)] : user-defined condition name or index
        * output
        return_value[:-1] : stock code list that meets the condition
        '''
        self._get_condition_load()
        condi_list = self._get_condition_name_list()
        for condi in condi_list:
            condi_idx = int(condi[0])
            condi_name = condi[1]
            if condi_idx==condi_key or condi_name==condi_key:
                self._send_condition("0150", condi_name, condi_idx, 0)
        return_value = self.condi_list
        self.condi_list=[]
        return return_value[:-1]

    ########################################################
    def req_opt10001(self, *com_code_list):
        '''
        this method require all tr 10,001 data
        (tr10,001 : stock default information)
        %screen number : '0001'
        * input 
        *com_code_list [unpacking list str] : stock code list
        * output (not return)
        self.d10001 [DataFrame] : index:stock code, columns:stock name, market cap.
        '''
        self.d10001 = df(columns=('name', 'market_cap'))
        #self.d10001 = {'code': [], 'name': [], 'market_cap': []}
        for com_code in com_code_list:
            if self._tr_count == LIMIT_TR_COUNT:
                return -1
            self._set_input_value("종목코드", com_code)
            self._comm_rq_data("opt10001_req", "opt10001", 0, "0001")
        return 0

    ########################################################
    def req_opt10060(self, com_code, end_date, form_opt='MONEY', trade_opt='TOTAL',
                     stock_opt=1000, start_date=datetime.datetime(1,1,1)):
        '''
        this method require all tr 10,060 data
        (tr10,060 : stock daily investors trend chart data)
        %screen number : '0060'
        :PARAM :com_code[str] stock code(6digit) :end_date[datetime] last day of chart
        :form_opt[str] data unit 'MONEY'-money unit, 'QUANTITY'-quantity unit
        :trade_opt[str] trade option 'TOTAL'-calculated selling and buying, 'SELL'-just selling,
        'BUY'-just buying :stock_opt[int] if form_opt is 'MONEY', this ignored. select quantitiy unit(1 or 1000)
        :start_date[datetime] first day of chart. if default, all past data
        :RETURN :status[int] 0-succes -1-some data because of limited tr count
        :df_data[DataFrame] index[datetime]=date, columns[int]=foreigner, institution, individual amount
        '''
        date = end_date.strftime('%Y%m%d')
        start_date = start_date.strftime('%Y%m%d')
        form_opt = '1' if form_opt == 'MONEY' else ('2' if form_opt == 'QUANTITY' else
                        (self._error('Argument', 'form_opt')))
        trade_opt = '0' if trade_opt == 'TOTAL' else ('1' if trade_opt == 'BUY' else
                        ('2' if trade_opt == 'SELL' else (self._error('Argument', 'trade_opt'))))
        stock_opt = '1' if stock_opt == 1 else ('1000' if stock_opt == 1000 else
                        (self._error('Argument', 'stock_opt')))
            
        self.d10060 = []
        status = 0
        if self._tr_count == LIMIT_TR_COUNT:
            return -1, df()
        self._scr_no = str((int(self._scr_no) + 1) % 200 + 1)
        self._set_input_value("일자", date)
        self._set_input_value("종목코드", com_code)
        self._set_input_value("금액수량구분", form_opt)
        self._set_input_value("매매구분", trade_opt)
        self._set_input_value("단위구분", stock_opt)
        condi = self._comm_rq_data("opt10060_req", "opt10060", 0, self._scr_no)

        while self.remained_data:
            if start_date >= self.d10060[-1][0]:
                status = 0
                break
            if self._tr_count == LIMIT_TR_COUNT:
                status = -1
                break
            self._scr_no = str((int(self._scr_no) + 1) % 200 + 1)
            self._set_input_value("일자", date)
            self._set_input_value("종목코드", com_code)
            self._set_input_value("금액수량구분", form_opt)
            self._set_input_value("매매구분", trade_opt)
            self._set_input_value("단위구분", stock_opt)
            condi = self._comm_rq_data("opt10060_req", "opt10060", 2, self._scr_no)

        str_arr = np.array(self.d10060, dtype=np.str_)
        # del self.d10060
        df_data = df(data=str_arr[:, [5,6,4]], index=str_arr[:,0],
                     columns=('fore', 'inst', 'indi'))
        df_data.index = pd.to_datetime(df_data.index, format='%Y%m%d')
        df_data['fore'] = df_data['fore'].str.replace(pat='^([+-])([+-])', repl='\\1')
        df_data['inst'] = df_data['inst'].str.replace(pat='^([+-])([+-])', repl='\\1')
        df_data['indi'] = df_data['indi'].str.replace(pat='^([+-])([+-])', repl='\\1')
        df_data = df_data.astype({'fore': int, 'inst': int, 'indi': int})
        return status, df_data

    ########################################################
    def req_opt10081(self, com_code, end_date, modi_price=True, start_date=datetime.datetime(1,1,1)):
        '''
        this method require all tr 10,081 data
        (tr10,081 : stock daily candle chart data)
        %screen number : '0081'
        :PARAM :com_code[str] stock code(6digit) :end_date[datetime] last day of chart
        :modi_price[bool] whether modified price(True) or not(False)
        :start_date[datetime] first day of chart. if default, all past data
        :RETURN :status[int] 0-succes -1-some data because of limited tr count
        :df_data[DataFrame] index[datetime]=date, columns[int]=opening price, closing price,
        high price, low price, volume, volume_price
        '''
        date = end_date.strftime('%Y%m%d')
        start_date = start_date.strftime('%Y%m%d')
        modi_price = '1' if modi_price is True else ('0' if modi_price is False else
                        (self._error('Argument', 'modi_price')))

        self.d10081 = []
        status = 0
        if self._tr_count == LIMIT_TR_COUNT:
            return -1, df()
        self._scr_no = str((int(self._scr_no) + 1) % 200 + 1)
        self._set_input_value("종목코드", com_code)
        self._set_input_value("기준일자", date)
        self._set_input_value("수정주가구분", modi_price)
        condi = self._comm_rq_data("opt10081_req", "opt10081", 0, self._scr_no)
        
        while self.remained_data:
            if start_date >= self.d10081[-1][4]:
                status = 0
                break
            if self._tr_count == LIMIT_TR_COUNT:
                status = -1
                break
            self._scr_no = str((int(self._scr_no) + 1) % 200 + 1)
            self._set_input_value("종목코드", com_code)
            self._set_input_value("기준일자", date)
            self._set_input_value("수정주가구분", modi_price)
            condi = self._comm_rq_data("opt10081_req", "opt10081", 2, self._scr_no)

        str_arr = np.array(self.d10081, dtype=np.str_)
        # del self.d10081
        df_data = df(data=str_arr[:,[5,1,6,7,2,3]], index=str_arr[:,4],
                     columns=('open','close','high','low','volume_q','volume_p'))
        df_data.index = pd.to_datetime(df_data.index, format='%Y%m%d')
        df_data['open'] = df_data['open'].str.replace(pat='^([+-])([+-])', repl='\\1')
        df_data['close'] = df_data['close'].str.replace(pat='^([+-])([+-])', repl='\\1')
        df_data['high'] = df_data['high'].str.replace(pat='^([+-])([+-])', repl='\\1')
        df_data['low'] = df_data['low'].str.replace(pat='^([+-])([+-])', repl='\\1')
        df_data['volume_q'] = df_data['volume_q'].str.replace(pat='^([+-])([+-])', repl='\\1')
        df_data['volume_p'] = df_data['volume_p'].str.replace(pat='^([+-])([+-])', repl='\\1')
        df_data = df_data.astype({'open':int, 'close':int, 'high':int, 'low':int,
                                  'volume_q':int, 'volume_p':int})
        return status, df_data

    ########################################################
    def get_master_stock_info(self, *str_code_list):
        '''
        this method get stock information about market, size, sectors
        * input
        *str_code_list [unpacking list str] : stock code
        * output
        info_list [two-dim str] : stock information
                                  (format : [[market, size, sectors], ...])
        '''
        info_list = []
        for str_code in str_code_list:
            infos = self.KOA_Functions('GetMasterStockInfo', str_code)
            infos = infos.split(';')
            try:
                market = infos[0].split('|')[1]
            except IndexError:
                market = ""
            try:
                size = infos[1].split('|')[1]
            except IndexError:
                size = ""
            try:
                stock_type = infos[2].split('|')[1]
            except IndexError:
                stock_type = ""
                
            info = [market, size, stock_type]
            info_list.append(info)
        return info_list

    ########################################################
    def get_master_listed_stock_cnt(self, str_code):
        '''
        this method returns number of stocks in market
        * input
        *str_code[str] : stock code
        * output
        num_stocks[int] : number of stocks
        '''
        num_stocks = self.GetMasterListedStockCnt(str_code)
        return num_stocks

    ########################################################
    def send_order(self, acc_no, order_type, code, qty, deal_type, price=0, org_order_no=None):
        '''
        CALL EVENT [_receive_chejan_data]
        this method send order to kiwoom server.
        * input
        acc_no [str] : account number(10)
        order_type [int] : order type, refer variable [order_type_lookup]
        code [str] : code number that you order(6)
        qty [int] : stock quantity
        price [int] : stock price
        deal_type [str] : deal type, refer varialbe [deal_type_lookup]
        org_order_no [str] : original order number to modify or cancel original order
        * output
        self._order_no [str] : this method order number
        :RETURN :ret_val[int] {1} order success {rest} order fail
        * caution
        in virtual trading, you can only use deal type 'LIMIT' and 'MARKET'. 
        '''
        rq_name = 'send_order_req'
        self._scr_no = str(int(self._scr_no) + 1 % 200 + 1)
        order_type_lookup = {'BUY':1, 'SELL':2, 'CANCEL_BUY':3,
                             'CANCEL_SELL':4, 'MODI_BUY':5, 'MODI_SELL':6}
        deal_type_lookup = {'LIMIT':'00', 'MARKET':'03', 
                            'CONDI_LIMIT':'05', 'ADVAN_LIMIT':'06', 'PRIOR_LIMIT':'07',
                            'LIMIT_IOC':'10', 'MARKET_IOC':'13', 'ADVAN_IOC':'16',
                            'LIMIT_FOK':'20', 'MARKET_FOK':'23', 'ADVAN_FOK':'26',
                            'BEFORE_MARKET':'61', 'TIMEOUT':'62', 'AFTER_MARKET':'81'}
        if order_type in order_type_lookup:
            order_type = order_type_lookup[order_type]
        if deal_type in deal_type_lookup:
            deal_type = deal_type_lookup[deal_type]
            
        ret_val = self.SendOrder(rq_name, self._scr_no, acc_no, order_type,
                                 code, qty, price, deal_type, org_order_no)
        return ret_val

    ########################################################
    def get_tr_count(self):
        '''
        this method get current tr count for checking limitation of required lookup 
        
        * output
        self._tr_count [int] : required tr count  
        '''
        return self._tr_count
    
    ########################################################
    def close(self, app):
        th = Thread(target=self._close_app, args=(app,))
        th.daemon=False
        th.start()
        #app.exec_()
        
    ########### USER-USED METHOD END ##############
    def _close_app(self, app):
        time.sleep(0.5)
        app.quit()

    def _error(self, error, kwarg):
        argument = {'modi_price': (True, False),
                    'form_opt': ('MONEY', 'QUANTITY'),
                    'trade_opt': ('TOTAL', 'SELL', 'BUY'),
                    'stock_opt': (1, 1000),
                   }
        if error == 'Argument':
            msg = "{0} must have value in {1}".format(kwarg, argument[kwarg])
            raise ArgumentError(msg)

#############  ERROR : MODULE DEFINED ############################
class ArgumentError(Exception):
    pass

##################################################################
if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = Kiwoom()
    #kiwoom.comm_connect()

    #status, data = kiwoom.req_opt10060("128660", datetime.datetime(2020, 8, 10))
    #print(data)
    #print(status)

    #print(kiwoom.GetLoginInfo("ACCLIST"))
    #kiwoom.comm_connect()
    #print(kiwoom.GetLoginInfo("ACCLIST"))
    #a = kiwoom.req_opt10086("357780", datetime.date(2020, 8, 16), 'MONEY', "ALL")
    #a = kiwoom.req_opt10081("357780", datetime.date(2020,8,16), True, "ALL")
    #a = kiwoom.req_opt10081("000050", datetime.date(2000, 8, 16), True, "ALL")
    #print(kiwoom.d10081.tail(5))
    #print('end')

    #kospi = kiwoom.get_code_list_by_market('0')

    #print(kiwoom.GetLoginInfo("USER_NAME"))
    #kiwoom.req_opt10081("000050", "20191230", "QUANTITY", "ALL")
    #com_list = kiwoom.get_condition_search_result("시총2000억이상")
    #stock = kiwoom.get_master_stock_info(*kospi)
    #com_name = kiwoom.get_master_code_name(*com_list)
    #com_infos = kiwoom.get_master_stock_info(*com_list)
