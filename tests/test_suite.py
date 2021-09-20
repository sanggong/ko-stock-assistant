import unittest
from tests.test_backtester import BackTesterTestCase
#from tests.test_frechetdist import FrechetDistTestCase

def suite():
    suite = unittest.TestSuite()
    suite.addTest()
    print(suite)
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())