# -*- coding: utf-8 -*-
"""
Trader.py

this is backtest module
"""
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import datetime
import copy
from sqlalchemy import create_engine
from sqlalchemy.dialects.mysql import DATE, FLOAT, INTEGER, VARCHAR
from . import qutils
from .StockDB import StockDB

class ArgumentError(Exception):
    pass

class BackTester():
    def __init__(self):
        self._test_list = [] # (,3) dim list. [['code', 'date', 'group'], ...]
        self._tax = 0.3
        self._commission = 0.015
        self._db = None

    def set_stock_db(self, user_id, norm_pwd, db_name):
        '''
        You must call this method to connect DB before you call backtest.
        :param user_id: maria DB id.
        :param norm_pwd: maria DB passward.
        :param db_name: stock db name in MariaDB.
        '''
        self._db = StockDB(user_id=user_id, norm_pwd=norm_pwd, db_name=db_name)

    def set_tax(self, tax):
        self._tax = tax

    def set_commission(self, commission):
        self._commission = commission

    def insert(self, data):
        '''
        insert data into test_list.
        :param data:[(?,3)dim] (code[str],date[date or datetime],group[str])
        '''
        if len(data) != 3:
            raise ArgumentError('insert argument must be (,3) dimension type')
        data[0] = data[0] + '_0'  # '005930_0'
        for idx in range(len(self._test_list)-1, -1, -1):
            if data[0][0:7] == self._test_list[idx][0][0:7]:
                data[0] = data[0][0:7] + str(int(self._test_list[idx][0][7:]) + 1)
                break
        self._test_list.append(data)

    def delete_all(self):
        self._test_list.clear()

    def delete(self, data=None):
        if data is None:
            self._test_list.pop()
        else:
            self._test_list.remove(data)

    def get_test_list(self):
        return copy.deepcopy(self._test_list)
    
    def back_test(self, number_of_days=130):
        '''
        - this method calculate time-varying stock profit ratio by group.
        - it use self._test_list.
        :param number_of_days:[int] backtest check after number_of_days.
        :return testResult:[class testResult] backtest result, it has result DataFrame and Group list.
        DataFrame columns : 'group', 'code', 'date', 'prev_price', 'price', 'captured', after days
        (1) time-varying profit ratio in stock.  (2) statics(mean, geometric mean, std dev, median) in time.
        '''
        self._db.open()
        data_list = []
        group_list = []

        # captured means rate of rise in captured date
        column_list = ['grp', 'code', 'date', 'prev_price', 'price', 'captured']
        days = ['_' + str(i) for i in range(1, number_of_days+1)]
        column_list.extend(days)

        # input list iteration
        for i in range(len(self._test_list)):
            code = self._test_list[i][0]
            date = self._test_list[i][1]
            group = self._test_list[i][2]
            if group not in group_list:
                group_list.append(group)
            row = [group, code, date]
            price = self._db.get_future_price_list(code[:6], date, number_of_days)
            if np.isnan(price[1]):
                continue
            row.extend(price)
            row.insert(5, 0)  # 'captured' column

            data_list.append(row)

        static = {'mean': np.nanmean, 'g_mean': qutils.nangmean, 'stddev': np.nanstd, 'median': np.nanmedian}
        for group in group_list:
            rest = [None for _ in range(number_of_days + 4)]
            for stat in static.keys():
                row = [group, stat]
                row.extend(rest)
                data_list.append(row)

        result = pd.DataFrame(data=data_list, columns=column_list)
        for day in days:
            result[day] = result[day] / result['price']
        result['captured'] = result['price'] / result['prev_price']

        days.append('captured')
        for group in group_list:
            for stat, stat_func in static.items():
                gc = result['grp'] == group
                sc = result['code'] == stat
                result.loc[gc & sc, days] = stat_func(result.loc[gc, days], axis=0)

        print(result)

        self._db.close()
        return testResult(result, group_list)


class testResult():
    '''
    This class has result of back test.
    :attribute: self.result[DataFrame] profit ratio and statistics data by code and date.
    :attribute: self.group_list[(?,)] collection user-inserted group data.
    To save or load result,
    you can use method self.set_bt_db() -> self.save() or self.load.
    '''
    def __init__(self, result=None, group_list=None):
        self._result = result
        self._groups = group_list
        self._max = None
        self._min = None

    def _get_max_idx_value(self):
        max_group = {}
        cols = self._result.columns[6:]
        sc = self._result['code'].isin(['mean', 'g_mean', 'stddev', 'median'])
        for group in self._groups:
            gc = self._result['grp'] == group
            max_col_idx = self._result.loc[gc & ~sc, cols].idxmax()
            max_sr = pd.Series([self._result.at[max_col_idx[i], i] for i in max_col_idx.index],
                               index=max_col_idx.index)   # [Series] max_col_idx has (idx:df column, value:df index)
            max_col = max_sr.idxmax()
            max_group[group] = [max_col_idx[max_col], max_col, max_sr[max_col]]  # index, column, value
        return max_group

    def _get_min_idx_value(self):
        min_group = {}
        cols = self._result.columns[6:]
        sc = self._result['code'].isin(['mean', 'g_mean', 'stddev', 'median'])
        for group in self._groups:
            gc = self._result['grp'] == group
            min_col_idx = self._result.loc[gc & ~sc, cols].idxmin(axis=1)
            min_sr = pd.Series([self._result.at[min_col_idx[i], i] for i in min_col_idx.index],
                               index=min_col_idx.index)   # [Series] min_col_idx has (idx:df column, value:df index)
            min_col = min_sr.idxmax()
            min_group[group] = [min_col_idx[min_col], min_col, min_sr[min_col]]  # index, column, value
        return min_group

    def show_summary(self):
        '''
        Print mean, geometric mean, standard deviation, median over time
        and max profit, min profit data in result of back test
        '''
        if self._max is None:
            self._max = self._get_max_idx_value()  # {group:[row, column, value], ...}
        if self._min is None:
            self._min = self._get_min_idx_value()  # {group:[row, column, value], ...}

        stats = ['mean', 'g_mean', 'stddev', 'median']
        col = self._result.columns[-1]
        for group in self._groups:
            gc = self._result['grp'] == group
            print(f"## GROUP_{group} RESULT ##")
            print(f"AFTER {col} DAYS")
            for stat in stats:
                sc = self._result['code'] == stat
                val = float(self._result.loc[gc & sc, col])
                print(f"{stat:<8}: {val:.3f}")
            print(f"max val > code : {self._result.at[self._max[group][0], 'code'][:6]}")
            print(f"          date : {self._result.at[self._max[group][0], 'date'].date()}")
            print(f"          days : {self._max[group][1]}")
            print(f"          prof : {self._max[group][2]:.3f}\n")
            print(f"min val > code : {self._result.at[self._min[group][0], 'code'][:6]}")
            print(f"          date : {self._result.at[self._min[group][0], 'date'].date()}")
            print(f"          days : {self._min[group][1]}")
            print(f"          prof : {self._min[group][2]:.3f}\n")

    def show_graph(self):
        '''
        Show two graph in different window.
        one is mean/geometric mean graph, another is standard deviation graph over time
        '''
        color = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                 '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        cols = self._result.columns[6:]
        int_cols = pd.to_numeric(cols.str.replace('_', ''))
        # mean, g_mean graph
        plt.figure('Profit Graph')
        for i, group in enumerate(self._groups):
            gc = self._result['grp'] == group
            sc_mean = self._result['code'] == 'mean'
            sc_gmean = self._result['code'] == 'g_mean'
            mean = self._result.loc[gc & sc_mean, cols].squeeze()  # change (1, days) into (days,)
            g_mean = self._result.loc[gc & sc_gmean, cols].squeeze()  # change (1, days) into (days,)
            plt.plot(int_cols, mean, color=color[i], label=f"[G_{group}] mean", linestyle='-')
            plt.plot(int_cols, g_mean, color=color[i], label=f"[G_{group}] g_mean", linestyle='-.')
        plt.title('Profit Graph')
        plt.xlabel('Days')
        plt.legend()

        # stddev graph
        plt.figure('Stddev Graph')
        for i, group in enumerate(self._groups):
            gc = self._result['grp'] == group
            sc_std = self._result['code'] == 'stddev'
            std = self._result.loc[gc & sc_std, cols].squeeze()  # change (1, days) into (days,)
            plt.plot(int_cols, std, color=color[i], label=f"[G_{group}] stddev")
        plt.title('Stddev Graph')
        plt.xlabel('Days')
        plt.legend()
        plt.show()

    def set_bt_db(self, user_id, norm_pwd, db_name):
        self._bt_info = {'USER_ID':user_id, 'NORM_PWD':norm_pwd, 'DB_NAME':db_name}

    def get_result_data(self):
        return self._result.copy()
    
    def save(self, table_name, msg, path):
        con_str = f"mysql+mysqldb://{self._bt_info['USER_ID']}:{self._bt_info['NORM_PWD']}"\
                  f"@localhost/{self._bt_info['DB_NAME']}"
        engine = create_engine(con_str)
        type_dict = {'grp': VARCHAR(10), 'code': VARCHAR(10), 'date': DATE(),
                     'prev_price': INTEGER(), 'price': INTEGER(), 'captured': FLOAT()}
        for day in self._result.columns[6:]:
            type_dict[day] = FLOAT()

        # Making DB from self._result_data
        self._result.to_sql(name=table_name, con=engine, chunksize=1000,
                            index_label='idx', dtype=type_dict)
        with engine.connect() as con:
            con.execute(f"ALTER TABLE {table_name} ADD PRIMARY KEY (idx);")
            con.execute(f"ALTER TABLE {table_name} MODIFY idx INTEGER;")

        date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(path + 'backtest.log', 'a') as f:
            f.write(f"[{date}] {table_name} : {msg}\n")

    def load(self, table_name):
        con_str = f"mysql+mysqldb://{self._bt_info['USER_ID']}:{self._bt_info['NORM_PWD']}"\
                  f"@localhost/{self._bt_info['DB_NAME']}"
        engine = create_engine(con_str)

        self._result = pd.read_sql_table(table_name=table_name, con=engine, index_col='idx')
        self._groups = self._result['grp'].drop_duplicates()
