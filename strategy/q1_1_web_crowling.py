# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28 06:13:12 2020

@author: ksme0
"""

import requests
from bs4 import BeautifulSoup
import datetime
import re

dates = []
codes = []
titles = []

pat_1 = re.compile('[\]\)>]+[ ]*[\D]+[,]{1}')
pat_2 = re.compile('[\]\)>]+[ ]*[가-힣a-zA-Z&]+[ ]{1}')
pat_3 = re.compile("' [가-힣a-zA-Z&]+ ")
pat_sub = re.compile("[^가-힣a-zA-Z& ]")

for page_num in range(1,42,1):
    url = 'https://finance.naver.com/news/news_search.nhn?'\
          'rcdate=1&q=%C6%AF%C2%A1%C1%D6+%BE%EE%B4%D7+%BC%AD%C7%C1%B6%F3%C0%CC%C1%EE&'\
          'x=9&y=15&sm=title.basic&pd=4&stDateStart=1997-01-01&stDateEnd=2019-12-31&'\
          'page='+ str(page_num)
          
    raw = requests.get(url).text
    html = BeautifulSoup(raw, 'html.parser')
    
    html_titles = html.select('.articleSubject')
    html_dates = html.select('.wdate')
    
    for html_title in html_titles:
        title = html_title.text.strip()
        code = pat_1.search(title)
        if code is not None:
            code = pat_sub.sub(' ', code.group()).strip()
            codes.append(code)
            continue
        
        code = pat_2.search(title)
        if code is not None:
            code = pat_sub.sub(' ', code.group()).strip()
            codes.append(code)
            continue
        
        code = pat_3.search(title)
        if code is not None:
            code = pat_sub.sub(' ', code.group()).strip()
            codes.append(code)
            continue
        
        codes.append(code)
            
    
    for html_date in html_dates:
        date = datetime.datetime.strptime(html_date.text.strip()[:10], '%Y-%m-%d')
        dates.append(date)

print('crowling done.')

with open('earning.txt', 'w') as file:
    for idx in range(len(codes)):
        file.write('{0} / {1}\n'.format(codes[idx], dates[idx]))
 
