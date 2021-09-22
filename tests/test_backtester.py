import unittest
import datetime
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
        BackTesterTestCase.DB.close()

    def setUp(self) -> None:
        self.bt = BackTester(self.__class__.DB)

    @unittest.skip
    def test__choose_chart_price(self):
        chart = BackTesterTestCase.DB.get_all_from_chart('005930')
        chart = self.bt._choose_chart_price(chart, 'c', avg_window=None)

    @unittest.skip
    def test_show_test_list(self):
        for i in range(10):
            self.bt.insert(['005930', datetime.date(2000, 12, 30) + timedelta(days=i*10), '1'])
        self.bt.show_test_list()

    def test_ins_chart_pattern(self):
        self.bt.ins_chart_pattern('005930', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.bt.show_test_list(number_of_days=60)

if __name__ == '__main__':
    unittest.main()
