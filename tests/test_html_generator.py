import unittest
import pandas as pd
import os

from kostock.html_generator import TestResultHtmlGenerator


class HtmlGeneratorTestCase(unittest.TestCase):
    def test_test_result_html_generator(self):
        save_path = os.path.dirname(os.path.realpath(__file__))
        result = pd.DataFrame()

        html = TestResultHtmlGenerator(save_path)
        html.create(title='UNITTEST', profit_path='', chart_path=[], result=result)

        self.assertTrue(os.path.exists(html.get_path_name()))
        os.remove(html.get_path_name())


if __name__ == '__main__':
    unittest.main()
