# -*- coding: utf-8 -*-
"""
stockdb.py

this module handle MariaDB stock database
"""

import MySQLdb as mysql


class StockDB:
    def __init__(self, user_id, norm_pwd, db_name):
        self.user_id = user_id
        self.norm_pwd = norm_pwd
        self.db_name = db_name

    def open(self):
        self._db = mysql.connect(host='localhost', user=self.user_id,
                                 passwd=self.norm_pwd, db=self.db_name,
                                 )
        self.cur = self._db.cursor()

    def close(self):
        self.cur.close()
        self._db.close()
    
    def commit(self):
        self._db.commit()
        
    def rollback(self):
        self._db.rollback()

    #####################################################################
    # STOCK INFO TABLE METHOD
    # ordered by DDL-DML(del, ins, upd)-DML(select)
    # sinfo DDL
    def create_sinfo_schema(self):
        sql = 'CREATE TABLE stock_info('\
              'code CHAR(6) PRIMARY KEY NOT NULL UNIQUE,'\
              'name VARCHAR(20),'\
              'wics_ls VARCHAR(20),'\
              'wics_ms VARCHAR(20),'\
              'market CHAR(3),'\
              'num_stocks BIGINT UNSIGNED,'\
              'cap INT UNSIGNED);'
        self.cur.execute(sql)
    
    # sinfo DML - DELETE, INSERT, UPDATE
    def delete_row_from_sinfo(self, code):  # code[str] : company code (6 digit)
        sql = "DELETE FROM stock_info WHERE code='{0}';".format(code)
        self.cur.execute(sql)
    
    def add_row_into_sinfo(self, code, name, wics_ls, wics_ms, market, num_stocks):
        '''
        Insert or update data into stock info table.
        when code exist in stock info table, use 'INSERT'
        when not exist, use 'UPDATE'
        :PARAM :code[str] company code(6 digit) :name[str] company name :wics_ls[str] wics large sector
        :wics_ms[str] wics middle sector :market[str] kospi/kosdaq :num_stocks[int] number of stocks in market
        '''
        values = (code, name, wics_ls, wics_ms, market, num_stocks, 0)
        sql = "INSERT INTO stock_info VALUES {0} "\
              "ON DUPLICATE KEY "\
              "UPDATE name='{1}', wics_ls='{2}', wics_ms='{3}', market='{4}', num_stocks={5};"\
              .format(values, name, wics_ls, wics_ms, market, num_stocks)
        self.cur.execute(sql)
   
    # sinfo DML - SELECT
    def get_code_list_from_sinfo(self):
        '''
        get code list from stock info table
        :return :data[1dim] code list(code1, code2,...)
        '''
        sql = 'SELECT code FROM stock_info;'
        self.cur.execute(sql)
        data = self.cur.fetchall()
        data = (c for code in data for c in code)
        return data

    def get_all_from_sinfo(self):
        '''
        get all data from stock info table
        return
        * data[2-dim] : data about wics, name etc 
        '''
        sql = 'SELECT * FROM stock_info;'
        self.cur.execute(sql)
        data = self.cur.fetchall()
        return data
    
    def get_one_from_sinfo(self, code):
        '''
        get one data from stock info table
        parameter
        * code[str] : company code (6 digit)
        return
        * data[1-dim] : data about wics, name etc 
        '''
        sql = "SELECT * FROM stock_info WHERE code='{0}';".format(code)
        self.cur.execute(sql)
        data = self.cur.fetchone()
        return data

    #####################################################################
    # CANDLE CHART TABLE METHOD
    # ordered by DDL-DML
    # chart DDL
    def create_chart_schema(self, code): # code[str] : company code (6 digit)
        sql = 'CREATE TABLE c_{0}('\
              'date DATE PRIMARY KEY NOT NULL UNIQUE,'\
              'open INT UNSIGNED,'\
              'close INT UNSIGNED,' \
              'high INT UNSIGNED,' \
              'low INT UNSIGNED,'\
              'volume INT UNSIGNED,'\
              'fore INT,'\
              'inst INT,'\
              'indi INT);'.format(code)
        self.cur.execute(sql)
    
    def drop_chart_schema(self, code): # code[str] : company code (6 digit)
        sql = "DROP TABLE c_{0};".format(code)
        self.cur.execute(sql)    

    def drop_all_chart_schema(self):
        sql = "SHOW TABLES WHERE Tables_in_{0} LIKE 'c_%';".format(self.db_name)
        self.cur.execute(sql)
        tables = self.cur.fetchall()
        for table in tables:
            sql = "DROP TABLE {0}".format(table[0])
            self.cur.execute(sql)

    # chart DML
    def insert_ohlc_into_chart(self, code, date, p_open, p_close, p_high, p_low, volume_q):
        date = date.strftime('%Y-%m-%d')
        values = (date, p_open, p_close, p_high, p_low, volume_q)
        sql = f"INSERT INTO c_{code}(date, open, close, high, low, volume) VALUES {values} "\
              f"ON DUPLICATE KEY "\
              f"UPDATE open={p_open}, close={p_close}, high={p_high}, low={p_low}, volume={volume_q};"
        self.cur.execute(sql)

    def insert_investor_into_chart(self, code, date, fore, inst, indi):
        date = date.strftime('%Y-%m-%d')
        values = (date, fore, inst, indi)
        sql = f"INSERT INTO c_{code}(date, fore, inst, indi) VALUES {values} "\
              f"ON DUPLICATE KEY "\
              f"UPDATE fore={fore}, inst={inst}, indi={indi};"
        self.cur.execute(sql)

    def get_all_from_chart(self, code):
        '''
        get all data from the one candle chart table
        parameter
        * code[str] : company code (6 digit)
        return
        * data[2-dim] : data about price, volume etc 
        '''
        sql = "SELECT * FROM c_{0};".format(code)
        self.cur.execute(sql)
        data = self.cur.fetchall()
        return data

    def get_one_from_chart(self, code, date=None):
        '''
        get one data from the one candle chart table
        if date is None, func returns latest data
        parameter
        * code[str] : company code (6 digit)
        * date[date] : date 
        return
        * data[1-dim] : data about price, volume etc 
        '''
        if date is None:
            sql = "SELECT * FROM c_{0} ORDER BY date DESC LIMIT 1".format(code)
        else:
            date = date.strftime('%Y-%m-%d')
            sql = "SELECT * FROM c_{0} WHERE date='{1}'".format(code, date)
        self.cur.execute(sql)
        data = self.cur.fetchone()
        return data

    def get_range_from_chart(self, code, start_date, end_date):
        '''
        return chart column value(price, indi,fore,inst quantity)
        :param code: company code
        :param start_date: start date in chart table
        :param end_date: end date in chart table
        :return: chart table data from start date to end date
        '''
        sql = "SELECT * FROM c_{0} WHERE date BETWEEN '{1}' AND '{2}';".format(code, start_date, end_date)
        self.cur.execute(sql)
        data = self.cur.fetchall()
        return data

    def get_ohlc_prev_from_chart(self, code, date, prev_days):
        '''
        return chart colum value(price, institution quantity) from date-prev_days to date
        :param code: code: company code
        :param date: start date in chart table
        :param days: it is used limit
        :return: chart table data from date-prev_days to date
        '''
        sql = f"SELECT date, open, close, high, low, volume FROM c_{code} WHERE date <= '{date}' "\
              f"ORDER BY date DESC LIMIT {prev_days};"
        self.cur.execute(sql)
        data = self.cur.fetchall()
        return data

    #####################################################################
    # META UPDATE TABLE METHOD
    # ordered by DDL-DML(del, ins, upd)-DML(select)
    # meta DDL    
    def create_meta_schema(self):
        sql = 'CREATE TABLE meta_update('\
              'table_name VARCHAR(20) PRIMARY KEY NOT NULL UNIQUE,'\
              'update_date DATE,'\
              'listing_date DATE);'
        self.cur.execute(sql)
    
    # meta DML
    def update_sinfo_date_in_meta(self, update_date):
        '''
        insert or update stock info update date
        '''
        update_date = update_date.strftime('%Y-%m-%d')
        sql = "INSERT INTO meta_update(table_name, update_date) "\
              "VALUES ('stock_info', '{0}') ON DUPLICATE KEY "\
              "UPDATE update_date='{0}'".format(update_date)
        self.cur.execute(sql)

    def insert_listing_date_into_meta(self, code, listing_date):
        listing_date = listing_date.strftime('%Y-%m-%d')
        sql = "INSERT INTO meta_update(table_name, listing_date) "\
              "VALUES ('c_{0}', '{1}') ON DUPLICATE KEY "\
              "UPDATE listing_date='{1}'".format(code, listing_date)
        self.cur.execute(sql)

    def update_chart_date_in_meta(self, code, update_date):
        update_date = update_date.strftime('%Y-%m-%d')
        sql = "UPDATE meta_update SET update_date='{0}' "\
              "WHERE table_name='c_{1}'".format(update_date, code)
        self.cur.execute(sql)

    def delete_chart_table_from_meta(self, code):
        sql = "DELETE FROM meta_update WHERE table_name='c_{0}'".format(code)
        self.cur.execute(sql)

    def get_sinfo_from_meta(self):
        '''
        get sinfo data from meta update table
        return
        * data[1-dim] : update data for sinfo 
        '''
        sql = "SELECT * FROM meta_update WHERE table_name='stock_info';"
        self.cur.execute(sql)
        data = self.cur.fetchone()
        return data
    
    def get_chart_from_meta(self):
        '''
        get candle chart data from meta update table
        return
        * data[2-dim] : data about wics, name etc 
        '''
        sql = "SELECT * FROM meta_update WHERE table_name LIKE 'c_%';"
        self.cur.execute(sql)
        data = self.cur.fetchall()
        return data

    #####################################################################
    def conv_code_to_name(self, code):
        '''
        - it returns stock name corresponding code
        
        input : * code [str]
                - stock code (6 digit)
        
        output : * stock_name [str]
                 - KOREAN stock name 
        '''
        sql = "SELECT name FROM Stock WHERE code='{0}';".format(code)
        self.cur.execute(sql)
        stock_name = self.cur.fetchone()
        
        if stock_name is None:
            return None
        else:
            return stock_name[0]
    
    def conv_name_to_code(self, name):
        '''
        - it returns stock code corresponding name
        
        input : * name [str]
                - KOREAN stock name 
        
        output : * stock_code [str]
                 - stock code (6 digit) 
        '''        
        db_cmd = "SELECT code FROM stock_info WHERE name='{0}';".format(name)
        self.cur.execute(db_cmd)
        stock_code = self.cur.fetchone()
        if stock_code is None:
            return None
        else:
            return stock_code[0]
        
    
    def get_stock_bucket(self):
        db_cmd = "SELECT * FROM Stock;"
        self.cur.execute(db_cmd)
        
        stock_bucket = self.cur.fetchall()
        
        return stock_bucket
    
    
    ### DML RELATED METHOD IN DAILY CANDLE TABLE ### 
    def get_recent_stock_price(self, code, date):
        '''
        ### _get_stock_price ###
        - this method returns stock price corresponding date and code
        - if stock price doesn't exist in the date, 
          it is calculated in MOST RECENTRLY PREVIOUS DATE
        input : * code [str]
                - stock code
                * date [date or datetime(00-00-00)]
                - date
        output : * stock_price [int]
                 - stock price by input date and code
        '''
        sql = "SELECT close FROM c_{0} WHERE date <= '{1}' ORDER BY date DESC LIMIT 1;".format(code, date)
        self.cur.execute(sql)
        p_close = self.cur.fetchone()
        ret_val = p_close[0] if p_close else None
        return ret_val

    def get_future_price_list(self, code,  date, number_of_days=130):
        '''
        - this method access DB and make price list
        - price list is made of later input date price
        - its length is value of number_of_days 
        - if actual data is less than number_of_days, 
          rest of data is filled with None
          
        input : * code [str]
                - stock code
                
                * date [date or datetime(00-00-00)]
                - date 
                
                * number_of_days [int]
                - it determines output data length (price_list)
                - default value is 130(days)
                
        output : * price_list [one-dim list]
                 - price list by date
        '''
        
        date = date.strftime('%Y-%m-%d')
        price_list = []
        sql = f"SELECT close FROM c_{code} WHERE date < '{date}' "\
              f"ORDER BY date DESC LIMIT 1"
        self.cur.execute(sql)
        prev_day = self.cur.fetchone()
        if prev_day:
            price_list.append(prev_day[0])
        else:
            return [float('nan') for _ in range(number_of_days + 2)]

        sql = f"SELECT close FROM c_{code} WHERE date >= '{date}' "\
              f"ORDER BY date ASC LIMIT {number_of_days + 1}"
        self.cur.execute(sql)
        two_dim = self.cur.fetchall()
        price_list.extend([price for one_dim in two_dim for price in one_dim])

        if len(price_list) < number_of_days + 2:
            nan_len = (number_of_days + 2) - len(price_list)
            nan_list = [float('nan') for _ in range(nan_len)]
            price_list.extend(nan_list)
        
        return price_list
