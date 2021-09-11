import unittest
import datetime

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

    def test_show_test_list(self):
        bt = BackTester(self.db)
        bt.insert(['005930', datetime.date(2000, 12, 30), '1'])
        bt.show_test_list()


if __name__ == '__main__':
    unittest.main()
