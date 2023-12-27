import unittest
import time
from uniswap_arb import UniswapPool, simulate_arb
from scipy.optimize import minimize, Bounds
import pandas as pd

class TestUniswap(unittest.TestCase):

    def setUp(self):
        self.pool = UniswapPool(100, 500)

    def test_add_remove_liquidity(self):
        with self.assertRaises(ValueError):
            self.pool.add_liquidity(10, 40)
            self.pool.add_liquidity(-10, -50)
        with self.assertRaises(ValueError):
            self.pool.remove_liquidity(10, 40)
            self.pool.remove_liquidity(-10, -50)

    def test_invalid_pool_amount(self):
        with self.assertRaises(ValueError):
            self.pool = UniswapPool(-10, 10)
            self.pool = UniswapPool(0, 10)

    def test_valid_swap_amount(self):
        try:
            self.pool.swap("DAI", 100)
        except ValueError:
            raise ValueError
    
    def test_invalid_swap_amount(self):
        with self.assertRaises(ValueError):
            self.pool.swap("DAI", -10)
        with self.assertRaises(ValueError):
            self.pool.swap("DAI", 0)
        with self.assertRaises(ValueError):
            self.pool.swap("ETH", -10)
        with self.assertRaises(ValueError):
            self.pool.swap("ETH", 0)

    
    def test_invalid_swap_amount(self):
        with self.assertRaises(ValueError):
            self.pool.swap("DAI", -10)
        with self.assertRaises(ValueError):
            self.pool.swap("DAI", 0)
        with self.assertRaises(ValueError):
            self.pool.swap("ETH", -10)
        with self.assertRaises(ValueError):
            self.pool.swap("ETH", 0)

    def test_invalid_swap_ticker(self):
        with self.assertRaises(ValueError):
            self.pool.swap("SOL", 100)
    
    def test_increasing_k(self):
        k_before = self.pool.K
        self.pool.swap('DAI', 0.001)
        k_after = self.pool.K
        self.assertGreater(k_after, k_before, "k must increase after swap")
        k_before = self.pool.K
        self.pool.swap('ETH', 0.001)
        k_after = self.pool.K
        self.assertGreater(k_after, k_before, "k must increase after swap")

if __name__ == '__main__':
    unittest.main()
