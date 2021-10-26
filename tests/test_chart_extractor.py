import unittest
import timeit

from kostock.stockdb import StockDB
from kostock.configurer import Configurer
from kostock.chart_extractor import ChartExtractor as ce


class ChartExtractorTestCase(unittest.TestCase):
    Configurer("config.json")
    db = StockDB()

    def test_capture_chart_pattern_mp(self):
        pattern = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        captured_1 = ce.capture_chart_pattern_mp(self.__class__.db, ["005930", "000660"], pattern, process_count=1)
        captured_2 = ce.capture_chart_pattern_mp(self.__class__.db, ["005930", "000660"], pattern, process_count=2)
        self.assertEqual(captured_1, captured_2)

    @unittest.skip
    def test_capture_chart_pattern(self):
        pattern = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        captured = ce.capture_chart_pattern(self.__class__.db, "005930", pattern)
        self.assertIsNotNone(captured)

    @unittest.skip
    def test_capture_inst_cond(self):
        captured = ce.capture_inst_cond(self.db, "005930", th_fore=10, th_inst=10)
        self.assertIsNotNone(captured)


if __name__ == '__main__':
    unittest.main()
