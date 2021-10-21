"""
chart_extractor.py

The module captures the chart data you want and returns that moment.
"""
import pandas as pd
from multiprocessing import Pool
from tqdm import tqdm

from kostock.qutils import measure_time
from kostock.frechetdist import frdist


class ChartExtractor:
    def __init__(self, db):
        self._db = db

    """
    def capture_chart_pattern_mp(self, codes, pattern, process_count=1, **kwargs):

        captured = []
        #arguments = [{'code': code, 'pattern': pattern} for code in codes]
        arguments = [(code, pattern) for code in codes]
        print(arguments)
        with Pool(process_count) as p:
            p.starmap(self.capture_chart_pattern, arguments)
    """

    def capture_chart_pattern(self, code, pattern, threshold=None, window_size=60, window_move=None, group='1',
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

        with self._db:
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
        captured = []
        while days < len(chart):
            part_chart = chart[days:days + window_size]
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
                    date = chart.index[days + window_size - 1]
                    captured.append([code, date, group])
                    days += window_size
                    continue
            days += window_move

        return captured

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

    def capture_inst_cond(self, code, th_fore, th_inst, days=3, group='1',
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
        with self._db:
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
            raise ValueError('th_fore or th_inst should be more than 0')

        captured = []
        day_cnt = 0
        for c in chart:
            date, fore, inst = c[0], c[6], c[7]
            if self.__class__._compare_quantity(mode, th_fore, th_inst, fore, inst):
                day_cnt += 1
            else:
                day_cnt = 0
            if day_cnt == days:
                captured.append([code, date, group])
        return captured

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
