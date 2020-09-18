# -*- coding: utf-8 -*-
"""
qutils.py
"""
import datetime
import pandas as pd
import numpy as np
import logging
import logging.handlers
from threading import Thread
import platform

class Log():
    def __init__(self):
        self.th = None

    def get_logger(self, name):
        return logging.getLogger(name)

    def listener_start(self, file_path, name, queue):
        '''
        Listener perform getting log data in Queue as consumer
        and writing log in way method self.config_log.
        Listener operate in new thread.
        :param file_path:[str] same file_path with method self.config_log
        :param name:[str] name assigned getLogger
        :param queue:[multiprocessing.Queue] Queue used in QueueHandler
        '''
        self.th = Thread(target=self._proc_log_queue, args=(file_path, name, queue))
        self.th.start()

    def listener_end(self, queue):
        '''
        Multiprocess log listener end method.
        :param queue:[multiprocessing.Queue] same queue with listener_start input queue.
        '''
        queue.put(None)
        self.th.join()
        print('log listener end...')

    def _proc_log_queue(self, file_path, name, queue):
        '''
        This function must be used in another thread
        :param queue: multiprocessing logging queue
        '''
        self.config_log(file_path, name)
        logger = self.get_logger(name)
        while True:
            try:
                record = queue.get()
                if record is None:
                    break
                logger.handle(record)
            except Exception:
                import sys, traceback
                print('log problem', file=sys.stderr)
                #traceback.print_exc(file=sys.stderr)

    def config_queue_log(self, queue, name):
        '''
        You want to use logging in multiprocessing, call this method in multiprocess and
        call self.listener_start, self.listener_end in main process.
        :param queue:[multiprocessing.Queue] Queue used in QueueHandler as producer.
        :param name:[str] name assigned getLogger.
        '''
        qh = logging.handlers.QueueHandler(queue)
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(qh)
        return logger

    def config_log(self, file_path, name):
        # err file handler
        fh_err = logging.handlers.TimedRotatingFileHandler(file_path + '_error.log', when='midnight', encoding='utf-8', backupCount=60)
        fh_err.setLevel(logging.WARNING)
        # file handler
        fh_dbg = logging.handlers.TimedRotatingFileHandler(file_path + '_debug.log', when='midnight', encoding='utf-8', backupCount=60)
        fh_dbg.setLevel(logging.DEBUG)
        # console handler
        sh = logging.StreamHandler()
        sh.setLevel(logging.INFO)
        # logging format setting
        ff = logging.Formatter('''[%(asctime)s] %(levelname)s : %(message)s''')
        sf = logging.Formatter('''[%(levelname)s] %(message)s''')
        fh_err.setFormatter(ff)
        fh_dbg.setFormatter(ff)
        sh.setFormatter(sf)
        if platform.system() == 'Windows':
            import msvcrt
            import win32api
            import win32con
            win32api.SetHandleInformation(msvcrt.get_osfhandle(fh_dbg.stream.fileno()),
                                          win32con.HANDLE_FLAG_INHERIT, 0)
            win32api.SetHandleInformation(msvcrt.get_osfhandle(fh_err.stream.fileno()),
                                          win32con.HANDLE_FLAG_INHERIT, 0)

        # create logger, assign handler
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(fh_err)
        logger.addHandler(fh_dbg)
        logger.addHandler(sh)
        return logger

def get_latest_trading_date(date, excel_path):
    '''
    Calculate latest trading date without market closed day by input date.
    :param date:[datetime] any date.
    :param excel_path:[str] excel file about market closed day location.
    :return:[datetime] latest trading date (previous date).
    '''
    closed_days = get_closed_days(excel_path)
    while date.weekday() in (5, 6) or date in closed_days:
        # 0:MON, 1:TUE, 2:WED, 3:THU, 4:FRI, 5:SAT, 6:SUN
        date = date - datetime.timedelta(days=1)
    return date

def get_closed_days(excel_path):
    '''
    Return
    - dates[1-dim tuple] : market closed day (without weekends)
    '''
    xls = pd.ExcelFile(excel_path)
    sheet = xls.parse()

    dates = pd.to_datetime(sheet['일자 및 요일'], format='%Y-%m-%d')
    return tuple(dates)


def get_wics_url(date, wics_code):
    '''
    Parameter
    - date[date] : the date corresponding data (yyyymmdd)
    - wics_code[int] : the wics code corresponding data (use wics_lc or wics_mc)
    Return
    - url[str]
    '''
    date=date.strftime('%Y%m%d')
    url ='http://www.wiseindex.com/Index/GetIndexComponets?ceil_yn=0&'\
          'dt=' + date + '&sec_cd=G' + str(wics_code)
    return url

def get_comp_main_url(code):
    '''
    Parameter
    - code[str] : the company code corresponding data
    Return
    - url[str]
    '''
    url = 'https://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&'\
          'gicode=A' + code + '&cID=&MenuYn=Y&ReportGB=&NewMenuID=Y&stkGb=701'
    return url

def get_comp_corp_url(code):
    '''
    Parameter
    - code[str] : the company code corresponding data
    Return
    - url[str]
    '''
    url = 'https://comp.fnguide.com/SVO2/ASP/SVD_Corp.asp?pGB=1&'\
          'gicode=A' + code + '&cID=&MenuYn=Y&ReportGB=&NewMenuID=Y&stkGb=701'
    return url

def nangmean(arr, axis=None):
    '''
    Calculate geometric mean in the numpy way.
    :param arr:[(n) or (n,n) dim] 1-dim or 2-dim list
    :param axis:[int] 0-column axis, 1-row axis.
    :return: geometric means[float]
    '''
    arr = np.asarray(arr)
    valids = np.sum(~np.isnan(arr), axis=axis)
    prod = np.nanprod(arr, axis=axis)
    return np.power(prod, 1. / valids)
