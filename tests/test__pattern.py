import unittest

from kostock._pattern import Singleton


class MyTestCase(unittest.TestCase):
    class TestClass(metaclass=Singleton):
        pass

    def test_something(self):
        tc1 = self.TestClass()
        tc2 = self.TestClass()
        self.assertIs(tc1, tc2)


if __name__ == '__main__':
    unittest.main()
