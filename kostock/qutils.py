# -*- coding: utf-8 -*-
"""
qutils.py
"""
import datetime
import pandas as pd
import numpy as np


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
