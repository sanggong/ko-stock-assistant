import unittest
import datetime

from kostock.stockdb import StockDB
from kostock.configurer import Configurer


class StockDBTestCase(unittest.TestCase):
    Configurer("config.json")
    DB = StockDB()
    DB.open()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.DB.close()

    def setUp(self) -> None:
        self.db = self.__class__.DB

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
