# -*- coding: utf-8 -*-
"""
qutils.py
"""
import datetime
import numpy as np
import timeit
import requests
import urllib.parse


def measure_time(func):
    """
    Decorator that measures time
    """
    def timer(*args, **kwargs):
        start = timeit.default_timer()
        ret = func(*args, **kwargs)
        end = timeit.default_timer()
        print("Time[{}] : {}".format(func.__name__, end-start))
        return ret
    return timer


def get_latest_trading_date(date, url, service_key):
    """
    Calculate latest trading date without market closed day by input date.
    :param date:[datetime] any date.
    :param url:[str] Open Data API url for getting holidays.
    :param service_key:[str] Open Data API Service Key for getting holidays.
    :return:[datetime] latest trading date (previous date).
    """
    holidays = get_holidays(date.year, url, service_key)
    holidays.append(datetime.datetime(year=date.year, month=12, day=31))
    holidays = tuple(holidays)
    while date.weekday() in (5, 6) or date in holidays:
        # 0:MON, 1:TUE, 2:WED, 3:THU, 4:FRI, 5:SAT, 6:SUN
        date = date - datetime.timedelta(days=1)
    return date


def get_holidays(year, url, service_key):
    """
    Get holidays using Data API
    :param year[int]
    :param url[str]
    :param service_key[str]
    Return
    - dates[1-dim tuple] : market closed day (without weekends)
    """
    payload = {'solYear': str(year),
               'numOfRows': '50',
               '_type': 'json',
               'ServiceKey': service_key}

    payload_str = urllib.parse.urlencode(payload, safe="%")  # service key contains "%"

    response = requests.get(url, params=payload_str)
    if response.status_code == 200:
        holidays = [item['locdate'] for item in response.json()['response']['body']['items']['item']]
        holidays = list(map(conv_int_to_date, holidays))
        return holidays


def conv_int_to_date(date):
    """
    Convert integer to date type.
    :param date: YYYYMMdd
    :return: datetime type
    """
    year = date // 10000
    month = (date % 10000) // 100
    day = date % 100
    return datetime.datetime(year=year, month=month, day=day)


def get_url(url, *args):
    return url.format(*args)


def get_wics_url(date, wics_code):
    """
    Parameter
    - date[date] : the date corresponding data (yyyymmdd)
    - wics_code[int] : the wics code corresponding data (use wics_lc or wics_mc)
    Return
    - url[str]
    """
    date = date.strftime('%Y%m%d')
    url = 'http://www.wiseindex.com/Index/GetIndexComponets?ceil_yn=0&'\
          'dt=' + date + '&sec_cd=G' + str(wics_code)
    return url


def get_comp_main_url(code):
    """
    Parameter
    - code[str] : the company code corresponding data
    Return
    - url[str]
    """
    url = 'https://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&'\
          'gicode=A' + code + '&cID=&MenuYn=Y&ReportGB=&NewMenuID=Y&stkGb=701'
    return url


def get_comp_corp_url(code):
    """
    Parameter
    - code[str] : the company code corresponding data
    Return
    - url[str]
    """
    url = 'https://comp.fnguide.com/SVO2/ASP/SVD_Corp.asp?pGB=1&'\
          'gicode=A' + code + '&cID=&MenuYn=Y&ReportGB=&NewMenuID=Y&stkGb=701'
    return url


def nangmean(arr, axis=None):
    """
    Calculate geometric mean in the numpy way.
    :param arr:[(n) or (n,n) dim] 1-dim or 2-dim list
    :param axis:[int] 0-column axis, 1-row axis.
    :return: geometric means[float]
    """
    arr = np.asarray(arr)
    valids = np.sum(~np.isnan(arr), axis=axis)
    prod = np.nanprod(arr, axis=axis)
    return np.power(prod, 1. / valids)
