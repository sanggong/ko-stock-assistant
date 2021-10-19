# -*- coding: utf-8 -*-
"""
backtester.py

this is back test module
"""
from collections import defaultdict
import pandas as pd
import numpy as np
import datetime
import copy
import os

from sqlalchemy import create_engine
from sqlalchemy.dialects.mysql import DATE, FLOAT, INTEGER, VARCHAR

from kostock import qutils
from kostock.plot import Plot
from kostock.html_generator import TestResultHtmlGenerator


class BackTester:
    def __init__(self, db=None):
        self._test_list = []  # (,3) dim list. [['code', 'date', 'group'], ...]
        self._code_nums = defaultdict(int)
        self._tax = 0.3
        self._commission = 0.015
        self._db = db

    def set_tax(self, tax):
        self._tax = tax

    def set_commission(self, commission):
        self._commission = commission

    def insert(self, data):
        """
        insert data into test_list.
        :param data:[(3,)dim] (code[str],date[date or datetime],group[str])
        """
        if len(data) != 3:
            raise ValueError('insert argument must be (3,) dimension type')
        no = str(self._code_nums[data[0]])
        code = '_'.join([data[0], no])
        date = data[1]
        group = data[2]
        self._test_list.append([code, date, group])
        self._code_nums[data[0]] += 1

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
        """
        - this method calculate time-varying stock profit ratio by group.
        - it use self._test_list.
        :param number_of_days:[int] backtest check after number_of_days.
        :return testResult:[class testResult] backtest result, it has result DataFrame and Group list.
        DataFrame columns : 'group', 'code', 'date', 'prev_price', 'price', 'captured', after days
        (1) time-varying profit ratio in stock.  (2) statics(mean, geometric mean, std dev, median) in time.
        """
        data_list = []
        group_list = []

        # captured means rate of rise in captured date
        column_list = ['group', 'code', 'date', 'prev_price', 'price', 'captured']
        days = ['_' + str(i) for i in range(1, number_of_days+1)]
        column_list.extend(days)

        self._db.open()
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
        self._db.close()

        # add mean, g_mean, stddev, median row
        static = {'mean': np.nanmean, 'g_mean': qutils.nangmean, 'stddev': np.nanstd, 'median': np.nanmedian}
        for group in group_list:
            rest = [None for _ in range(number_of_days + 4)]
            for stat in static:
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
                gc = (result['group'] == group)
                sc = (result['code'] == stat)
                result.loc[gc & sc, days] = stat_func(result.loc[gc, days], axis=0)

        return TestResult(result, self._db)


class TestResult:
    """
    This class has result of back test.
    :attribute: self.result[DataFrame] profit ratio and statistics data by code and date.
    :attribute: self.group_list[(?,)] collection user-inserted group data.
    To save or load result,
    you can use method self.set_bt_db() -> self.save() or self.load.
    """
    def __init__(self, result=None, db=None):
        # columns of result = ['group', 'code', 'date', 'prev_price', 'price', 'captured', day1, day2, ...]
        self._result = result
        self._groups = result['group'].drop_duplicates()
        self._means = []
        self._gmeans = []
        self._stddevs = []
        self._chart_data = {}
        self._db = db
        self._bt_info = None

        self._max = self._get_max_idx_value()  # {group:{row:, column:, profit:}, ...}
        self._min = self._get_min_idx_value()  # {group:{row:, column:, profit:}, ...}
        self._cal_statics_per_group()

    def _get_max_idx_value(self):
        max_group = {}
        cols = self._result.columns[6:]
        sc = self._result['code'].isin(['mean', 'g_mean', 'stddev', 'median'])
        for group in self._groups:
            gc = self._result['group'] == group
            max_col_idx = self._result.loc[gc & ~sc, cols].idxmax()
            max_sr = pd.Series([self._result.at[max_col_idx[i], i] for i in max_col_idx.index],
                               index=max_col_idx.index)   # [Series] max_col_idx has (idx:df column, value:df index)
            max_col = max_sr.idxmax()
            max_group[group] = {'row': max_col_idx[max_col], 'col': max_col, 'profit': max_sr[max_col]}
        return max_group

    def _get_min_idx_value(self):
        min_group = {}
        cols = self._result.columns[6:]
        sc = self._result['code'].isin(['mean', 'g_mean', 'stddev', 'median'])
        for group in self._groups:
            gc = self._result['group'] == group
            min_col_idx = self._result.loc[gc & ~sc, cols].idxmin()
            min_sr = pd.Series([self._result.at[min_col_idx[i], i] for i in min_col_idx.index],
                               index=min_col_idx.index)   # [Series] min_col_idx has (idx:df column, value:df index)
            min_col = min_sr.idxmax()
            min_group[group] = {'row': min_col_idx[min_col], 'col': min_col, 'profit': min_sr[min_col]}
        return min_group

    def _cal_statics_per_group(self):
        cols = self._result.columns[6:]
        for group in self._groups:
            gc = (self._result['group'] == group)
            sc_mean = (self._result['code'] == 'mean')
            sc_gmean = (self._result['code'] == 'g_mean')
            sc_std = (self._result['code'] == 'stddev')

            mean = self._result.loc[gc & sc_mean, cols].squeeze()  # change (days, 1) into (days,)
            gmean = self._result.loc[gc & sc_gmean, cols].squeeze()  # change (days, 1) into (days,)
            std = self._result.loc[gc & sc_std, cols].squeeze()  # change (days, 1) into (days,)

            self._means.append(mean)
            self._gmeans.append(gmean)
            self._stddevs.append(std)

    def _make_chart_data(self, number_of_days):
        rc = self._result['code'].isin(['mean', 'g_mean', 'stddev', 'median'])
        cc = ['code', 'date', 'group']
        test_codes = self._result.loc[~rc, cc]

        cols = ['Date', 'Open', 'Close', 'High', 'Low', 'Volume']
        chart_data = []
        for row in test_codes.itertuples():
            code = getattr(row, 'code')
            date = getattr(row, 'date')
            ohlc = self._db.get_ohlc_prev_from_chart(code[:6], date, number_of_days)

            df_ohlc = pd.DataFrame(data=ohlc, columns=cols)
            df_ohlc['Date'] = df_ohlc['Date'].astype('datetime64[ns]')
            df_ohlc.set_index('Date', inplace=True)

            chart_data.append({'code': code, 'df': df_ohlc})

        return chart_data

    def show_summary(self):
        """
        Print mean, geometric mean, standard deviation, median over time
        and max profit, min profit data in result of back test
        """
        stats = ['mean', 'g_mean', 'stddev', 'median']
        col = self._result.columns[-1]
        for group in self._groups:
            gc = (self._result['grp'] == group)
            print(f"## GROUP_{group} RESULT ##")
            print(f"AFTER {col} DAYS")
            for stat in stats:
                sc = (self._result['code'] == stat)
                val = float(self._result.loc[gc & sc, col])
                print(f"{stat:<8}: {val:.3f}")
            print(f"max val > code : {self._result.at[self._max[group]['row'], 'code'][:6]}")
            print(f"          date : {self._result.at[self._max[group]['row'], 'date']}")
            print(f"          days : {self._max[group]['col']}")
            print(f"          prof : {self._max[group]['profit']:.3f}\n")
            print(f"min val > code : {self._result.at[self._min[group]['row'], 'code'][:6]}")
            print(f"          date : {self._result.at[self._min[group]['row'], 'date']}")
            print(f"          days : {self._min[group]['col']}")
            print(f"          prof : {self._min[group]['profit']:.3f}\n")

    def show_profit_graph(self):
        """
        Show two graph in different window.
        one is mean/geometric mean graph, another is standard deviation graph over time
        """
        plt = Plot()
        plt.plot_profit(self._groups, self._means, self._gmeans, self._stddevs)

    def show_test_code_chart(self, number_of_days=60):
        if number_of_days not in self._chart_data:
            self._chart_data[number_of_days] = self._make_chart_data(number_of_days)
        plt = Plot()
        plt.plot_ohlc_all(self._chart_data[number_of_days])

    def save_result_to_html(self, title, save_path, prev_chart_days=60):
        """
        Save result(profit, chart data) to HTML file.
        :param title: title is used for making folder.
        :param save_path: save path.
        :param number_of_days: prev days to plot chart data
        """
        folder_path = save_path + "\\result_" + title \
                      + "_{}".format(datetime.datetime.now().strftime('%Y-%m-%d_%Hh-%Mm-%Ss'))
        graph_path = folder_path + "\\graph"
        os.makedirs(graph_path)  # make both folder_path folder and graph_path folder

        # save profit, chart graph
        if prev_chart_days not in self._chart_data:
            self._chart_data[prev_chart_days] = self._make_chart_data(prev_chart_days)
        plt = Plot()
        plt.set_save_path(graph_path)
        chart_paths = plt.plot_ohlc_all(self._chart_data[prev_chart_days], save=True)
        profit_path = plt.plot_profit(self._groups, self._means, self._gmeans, self._stddevs, save=True)

        html_gen = TestResultHtmlGenerator(folder_path)
        path = html_gen.create(title, profit_path, chart_paths, self._result)
        return path

    def set_bt_db(self, user_id, norm_pwd, db_name):
        self._bt_info = {'USER_ID': user_id, 'NORM_PWD': norm_pwd, 'DB_NAME': db_name}

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
