import unittest
import datetime

from kostock.stockdb import StockDB

from config import config


class StockDBTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.db = StockDB(user_id=config.DB['USER_ID'],
                     norm_pwd=config.DB['NORM_PWD'],
                     db_name=config.DB['DB_NAME'])
        self.db.open()

    def tearDown(self) -> None:
        self.db.close()

    def test_get_range_from_chart(self):
        data = self.db.get_range_from_chart('005930', datetime.date(2000, 1, 2), datetime.date(2000, 1, 5))
        answer = ((datetime.date(2000, 1, 4), 6000, 6110, 6110, 5660, 74198350, 0, 0, 0),
                  (datetime.date(2000, 1, 5), 5800, 5580, 6060, 5520, 74680200, 0, 0, 0),
                  )
        self.assertEqual(data, answer)

    def test_get_ohlc_limit_from_chart(self):
        data = self.db.get_ohlc_prev_from_chart('005930', datetime.date(2000, 1, 5), 2)
        answer = ((datetime.date(2000, 1, 4), 6000, 6110, 6110, 5660, 74198350),
                  (datetime.date(2000, 1, 5), 5800, 5580, 6060, 5520, 74680200),
                  )
        self.assertEqual(data, answer)

if __name__ == '__main__':
    unittest.main()
