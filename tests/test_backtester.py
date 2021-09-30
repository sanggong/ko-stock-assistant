import unittest
import datetime
import os
from datetime import timedelta

from config import config

from kostock.backtester import BackTester
from kostock.stockdb import StockDB


class BackTesterTestCase(unittest.TestCase):

    DB = StockDB(user_id=config.DB['USER_ID'],
                 norm_pwd=config.DB['NORM_PWD'],
                 db_name=config.DB['DB_NAME'])
    DB.open()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.DB.close()

    def setUp(self) -> None:
        self.bt = BackTester(self.__class__.DB)

    # Test start #
    @unittest.skip
    def test__choose_chart_price(self):
        chart = self.__class__.DB.get_all_from_chart('005930')
        chart = self.bt._choose_chart_price(chart, 'c', avg_window=None)

    @unittest.skip
    def test_ins_chart_pattern(self):
        self.bt.ins_chart_pattern('005930', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    @unittest.skip
    def test_show_profit_graph(self):
        self.bt.insert(['005930', datetime.date(2000, 12, 30), '1'])
        result = self.bt.back_test()
        result.show_profit_graph()

    def test_back_test_all(self):
        self.bt.insert(['005930', datetime.date(2000, 12, 30), '1'])
        result = self.bt.back_test()

        save_path = os.path.dirname(os.path.realpath(__file__))
        path_name = result.save_result_to_html("UNITTEST", save_path)
        self.assertTrue(os.path.exists(path_name))
        print(result._result)


if __name__ == '__main__':
    unittest.main()
