import unittest
import datetime
import os
from datetime import timedelta

from kostock.configurer import Configurer
from kostock.backtester import BackTester
from kostock.stockdb import StockDB


class BackTesterTestCase(unittest.TestCase):
    Configurer("config.json")
    DB = StockDB()

    def setUp(self) -> None:
        self.bt = BackTester()

    # Test start #
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


if __name__ == '__main__':
    unittest.main()
