import unittest
import sys

from kostock import kiwoom
from kostock.configurer import Configurer


class KiwoomTestCase(unittest.TestCase):
    Configurer("config.json")
    APP = kiwoom.QApplication(sys.argv)
    KIWOOM = kiwoom.Kiwoom()
    KIWOOM.manual_login(user_id=Configurer.KIWOOM['USER_ID'],
                     norm_pwd=Configurer.KIWOOM['NORM_PWD'],
                     cert_pwd=Configurer.KIWOOM['CERT_PWD'],
                     is_mock=True)

    def setUp(self) -> None:
        self.kwm = self.__class__.KIWOOM

    def test_get_connect_state(self):
        state = self.kwm.get_connect_state()
        self.assertEqual(state, True)

if __name__ == '__main__':
    unittest.main()
