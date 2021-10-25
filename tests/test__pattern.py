import unittest

from kostock._pattern import Singleton


class MyTestCase(unittest.TestCase):
    class TestClass(metaclass=Singleton):
        count = 0
        def __init__(self):
            self.count += 1

    def test_something(self):
        tc1 = self.TestClass()
        tc2 = self.TestClass()
        self.assertIs(tc1, tc2)
        self.assertEqual(tc1.count, 1)


if __name__ == '__main__':
    unittest.main()
