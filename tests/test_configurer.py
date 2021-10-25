import unittest

from kostock.configurer import Configurer


class MyTestCase(unittest.TestCase):

    Configurer("config.json")

    def test_update_number_of_process(self):
        self.assertEqual(Configurer.UPDATE_NUMBER_OF_PROCESS, 2)

    def test_db(self):
        self.assertEqual(Configurer.DB["USER_ID"], "your_id")


if __name__ == '__main__':
    unittest.main()
