import unittest
import sys

from config import config

from kostock import kiwoom


class KiwoomTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.app = kiwoom.QApplication(sys.argv)
        self.kwm = kiwoom.Kiwoom()
        self.kwm.manual_login(user_id=config.KIWOOM['USER_ID'],
                              norm_pwd=config.KIWOOM['NORM_PWD'],
                              cert_pwd=config.KIWOOM['CERT_PWD'],
                              is_mock=True)

    def test_get_connect_state(self):
        state = self.kwm.get_connect_state()
        self.assertEqual(state, True)

if __name__ == '__main__':
    unittest.main()
