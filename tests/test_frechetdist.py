import unittest
from kostock.frechetdist import frdist

class FrechetDistTestCase(unittest.TestCase):

    def test_frdist(self):
        P = [[1, 1], [2, 1], [2, 2]]
        Q = [[2, 2], [0, 1], [2, 4]]
        res = frdist(P, Q)
        ans = 2.0
        self.assertEqual(res, ans)

    def test_frdist2(self):
        N = 100
        P = [[i, i] for i in range(N)]
        Q = [[N+i, N+i] for i in range(N)]
        res = frdist(P, Q)
        ans = 100 * (2**0.5)
        self.assertEqual(res, ans)

    def test_frdist3(self):
        N = 100
        P = [[i, i % 10] for i in range(N)]
        Q = [[i, (i+1) % 10] for i in range(N-1)]
        Q.append([N-1, N % 10])
        res = frdist(P, Q)
        ans = 9
        self.assertEqual(res, ans)

    def test_frdist4(self):
        N = 80
        P = [[i, i] for i in range(N)]
        Q = [[N+i, N+i] for i in range(N)]
        res = frdist(P, Q)
        ans = 80 * (2**0.5)
        self.assertEqual(res, ans)

    def test_frdist5(self):
        N = 80
        for _ in range(5000):
            P = [[i, i] for i in range(N)]
            Q = [[N+i, N+i] for i in range(N)]
            res = frdist(P, Q)


if __name__ == '__main__':
    unittest.main()
