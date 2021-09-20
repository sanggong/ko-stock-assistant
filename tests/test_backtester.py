import unittest
import datetime
from datetime import timedelta

from config import config

from kostock.backtester import BackTester
from kostock.stockdb import StockDB

class BackTesterTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.db = StockDB(user_id=config.DB['USER_ID'],
                     norm_pwd=config.DB['NORM_PWD'],
                     db_name=config.DB['DB_NAME'])
        self.db.open()

    def tearDown(self) -> None:
        self.db.close()

    @unittest.skip
    def test__choose_chart_price(self):
        bt = BackTester(self.db)
        chart = self.db.get_all_from_chart('005930')
        chart = bt._choose_chart_price(chart, 'c', avg_window=None)
        self.assertIs(chart)

    @unittest.skip
    def test_show_test_list(self):
        bt = BackTester(self.db)
        for i in range(10):
            bt.insert(['005930', datetime.date(2000, 12, 30) + timedelta(days=i*10), '1'])
        bt.show_test_list()

    def test_ins_chart_pattern(self):
        bt = BackTester(self.db)
        bt.ins_chart_pattern('005930', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        bt.show_test_list(number_of_days=60)

if __name__ == '__main__':
    unittest.main()
