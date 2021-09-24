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
from kostock.frechetdist import frdist
from kostock.plot import Plot
from kostock.html_generator import TestResultHTMLGenerator


class ArgumentError(Exception):
    pass
class ClassOperationError(Exception):
    pass


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
            raise ArgumentError('insert argument must be (3,) dimension type')
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

    def ins_chart_pattern(self, code, pattern, threshold=None, window_size=60, window_move=None, group='1',
                          price_opt='c', moving_avg=None, min_diff_ratio=0, max_diff_ratio=float('inf'),
                          start_date=None, end_date=None):
        """
        Insert data into this class when chart pattern is found by frechet distance way.
        :param code:[str]company code
        :param pattern: [(1,) int list] pattern to find out (its length must be window size or less)
        :param threshold: [float]chart similarity threshold
        :param window_size: [int]chart pattern window size
        :param window_move: [int]window moving value in chart
        :param group: [str]when inserting, set group value (default '1')
        :param price_opt: [str]price option(only close, close+open, ...)
        :param moving_avg: [int] moving average
        :param min_diff_ratio: [float] minimum chart difference ratio (percent unit)
        :param max_diff_ratio: [float] maximum chart difference ratio (percent unit)
        :param start_date: [date]chart start date
        :param end_date: [date]chart end date
        :return: no return, this method insert test data that pattern matched
        """
        if window_move is None:
            window_move = window_size // 10

        if start_date and end_date:
            chart = self._db.get_range_from_chart(code, start_date, end_date)
        else:
            chart = self._db.get_all_from_chart(code)

        chart = self.__class__._choose_chart_price(chart, price_opt, moving_avg)  # DataFrame type
        fr_pat = self.__class__._trans_pat_to_frpat(pattern, window_size)

        max_pat, min_pat = max(pattern), min(pattern)
        pat_diff = max_pat - min_pat

        if threshold is None:
            threshold = (window_size * pat_diff) / 200

        days = 0
        while days < len(chart):
            part_chart = chart[days:days+window_size]
            if len(part_chart) < window_size:
                break
            max_val, min_val = max(part_chart), min(part_chart)
            cht_diff = max_val - min_val
            cht_diff_ratio = cht_diff / min_val * 100  # percent unit
            if min_val == 0 or cht_diff == 0:
                days += window_move
                continue

            if min_diff_ratio <= cht_diff_ratio <= max_diff_ratio:
                fr_cht = (part_chart - min_val) * (pat_diff / cht_diff) + min_pat
                fr_cht = [[j, data] for j, data in enumerate(fr_cht)]  # convert pd.Series to list

                if frdist(fr_cht, fr_pat) < threshold:
                    date = chart.index[days+window_size-1]
                    self.insert([code, date, group])
                    days += window_size
                    continue
            days += window_move

    @staticmethod
    def _choose_chart_price(chart, price_opt, avg_window=None):
        """
        calculate average chart prices(c:close, o:open, h:high, l:low) by option
        :param chart: chart data
        :param price_opt: c:close, o:open, h:high, l:low
        :param avg_window: average by date like moving average.
        :return: [pd.Series] index:date / data:average price
        """
        columns = ['date', 'open', 'close', 'high', 'low',
                   'volume', 'fore', 'inst', 'indi']
        df_chart = pd.DataFrame(data=chart, columns=columns)
        df_chart['price'] = 0
        if 'c' in price_opt: df_chart['price'] += df_chart['close']
        if 'o' in price_opt: df_chart['price'] += df_chart['open']
        if 'h' in price_opt: df_chart['price'] += df_chart['high']
        if 'l' in price_opt: df_chart['price'] += df_chart['low']
        df_chart['price'] /= len(price_opt)

        ret_chart = pd.Series(data=df_chart['price'].to_numpy(),
                              index=df_chart['date'])

        if avg_window:
            ret_chart = ret_chart.rolling(window=avg_window, center=True, min_periods=1).mean()
        return ret_chart

    @staticmethod
    def _trans_pat_to_frpat(pattern, window_size):
        p = (window_size - 1) // (len(pattern) - 1)
        q = (window_size - 1) % (len(pattern) - 1)
        intervals = [p + 1 if i < q else p for i in range(len(pattern) - 1)]
        fr_pat = [[0, float(pattern[0])]]
        cnt = 0
        for i, itv in enumerate(intervals):
            for j in range(1, itv + 1):
                cnt += 1
                pat_val = pattern[i] + (pattern[i + 1] - pattern[i]) * j / itv
                fr_pat.append([cnt, pat_val])
        return fr_pat

    def ins_institution_condition(self, code, th_fore=1, th_inst=1, days=3, group='1',
                                  start_date=None, end_date=None):
        """
        Insert data into this class when institution buying quantity is more than threshold in days.
        :param code: [str] company code(6digit)
        :param th_fore: [int] threshold foreigner quantity
        :param th_inst: [int] threshold institution quantity
        :param days: [int] continuous days
        :param group: [str] backtest group
        :param start_date: [datetime or date] start date from chart
        :param end_date: [datetime or date] end date from chart
        :return: no returns, insert data into this class attribute.
        """
        if start_date and end_date:
            chart = self._db.get_range_from_chart(code, start_date, end_date)
        else:
            chart = self._db.get_all_from_chart(code)

        if th_fore != 0 and th_inst != 0:
            mode = 'BOTH'
        elif th_fore != 0:
            mode = 'FORE'
        elif th_inst != 0:
            mode = 'INST'
        else:
            raise ArgumentError('At least one param at th_fore and th_inst should be more than 0')

        day_cnt = 0
        for c in chart:
            date = c[0]
            fore = c[6]
            inst = c[7]
            if self.__class__._compare_quantity(mode, th_fore, th_inst, fore, inst):
                day_cnt += 1
            else:
                day_cnt = 0
            if day_cnt == days:
                self.insert([code, date, group])

    @staticmethod
    def _compare_quantity(mode, th_fore, th_inst, fore, inst):
        if mode == 'BOTH':
            if fore and inst:
                if fore >= th_fore and inst >= th_inst:
                    return True
        elif mode == 'FORE':
            if fore:
                if fore >= th_fore:
                    return True
        elif mode == 'INST':
            if inst:
                if inst >= th_inst:
                    return True
        return False


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
        self._groups = []
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
            self._groups.append(group)
            self._means.append(mean)
            self._gmeans.append(gmean)
            self._stddevs.append(std)

    def _make_chart_data(self, number_of_days):
        rc = self._result['code'].isin(['mean', 'g_mean', 'stddev', 'median'])
        cc = ['code', 'date', 'group']
        test_codes = self._result.loc[~rc, cc]

        cols = ['Date', 'Open', 'Close', 'High', 'Low', 'Volume']
        chart_data = []
        for code, date, _ in test_codes:
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

    def save_result_to_html(self, title, save_path, number_of_days=60):
        """
        Save result(profit, chart data) to HTML file.
        :param title: title is used for making folder.
        :param save_path: save path.
        :param number_of_days: prev days to plot chart data
        """
        folder_path = save_path + r"\\result_" + title \
                      + "_{}".format(datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S'))
        graph_path = folder_path + r"\\graph"
        os.makedirs(graph_path)  # make both folder_path folder and graph_path folder

        # save profit, chart graph
        if number_of_days not in self._chart_data:
            self._chart_data[number_of_days] = self._make_chart_data(number_of_days)
        plt = Plot()
        plt.set_save_path(graph_path)
        chart_path = plt.plot_ohlc_all(self._chart_data[number_of_days], save=True)
        profit_path = plt.plot_profit(self._groups, self._means, self._gmeans, self._stddevs, save=True)

        html_gen = TestResultHTMLGenerator(folder_path)
        html_gen.create(title, profit_path, chart_path, self._result)

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
