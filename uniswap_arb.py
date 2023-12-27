
from scipy.optimize import minimize, Bounds
import click

import timeit
import random
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class UniswapPool:
    def __init__(self, X, Y):
        """
        The UniSwapPool object simulates a Uniswap V2 pool: with two pools of tokens.
        X (DAI) and Y (ETH) are the initial amounts of tokens at the start.

        :param X: amount of DAI token at the start
        :type X:  float
        :param Y: amount of ETH token at the start 
        :type Y:  float
        :param K: the equation X*Y=K where K will remain constant throughout the life of the pool.
                  determined by initial amounts X and Y.
        :type K: float
        :param swap_fee: the fees taken as proportion of input amount for any swap
        :type swap_fee: flaot
        """
        if X <= 0 or Y <= 0: 
            raise ValueError("Invalid input token amounts: can't have negative or zero tokens")
        self.X = X
        self.Y = Y
        self.K = X * Y
        self.swap_fee = 0.003
       
    def add_liquidity(self, X, Y):
        if X/Y != self.X/self.Y:
            raise ValueError("Invalid ratio")
        if X <= 0 or Y <= 0: 
            raise ValueError("Invalid input token amounts: can't add negative or zero tokens")
        self.X += X
        self.Y += Y
        self.K = self.X * self.Y

    def remove_liquidity(self, X, Y):
        if X/Y != self.X/self.Y:
            raise ValueError("Invalid ratio")
        if X <= 0 or Y <= 0: 
            raise ValueError("Invalid input token amounts: can't remove negative or zero tokens")
        self.X -= X
        self.Y -= Y
        self.K = self.X * self.Y

    def swap(self, input_token, input_amount):
        """
        Performs a swap of either DAI for ETH or ETH for DAI.
        Modifies the token amounts X (DAI) and Y (ETH) in the pool.

        :param input_token: Name of token, either "DAI" or "ETH" 
        :type input_token: str
        :param input_amount: Amount of token entering the pool 
        :type input_amount: float
        """
        if input_amount <= 0:
            raise ValueError("Invalid input token amount: can't swap negative or zero tokens")
        if input_token == "DAI":
            output_amount = self.output(input_token, input_amount)
            logger.info(f"Old DAI: {self.X} | Old ETH: {self.Y} | Old K: {self.K}")
            self.X += input_amount
            self.Y -= output_amount
            self.K = self.X * self.Y
            logger.info(f"Input: {input_amount} DAI | Output: {output_amount} ETH")
            logger.info(f"New DAI: {self.X} | New ETH: {self.Y} | New K: {self.K}")
            return output_amount 
        elif input_token == "ETH":
            output_amount = self.output(input_token, input_amount)  
            logger.info(f"Old DAI: {self.X} | New ETH: {self.Y} | Old K: {self.K}")
            self.Y += input_amount
            self.X -= output_amount
            self.K = self.X * self.Y
            logger.info(f"Input: {input_amount} ETH | Output: {output_amount} DAI")
            logger.info(f"New DAI: {self.X} | New ETH: {self.Y} | New K: {self.K}")
            return output_amount
        else:
            raise ValueError("Invalid input/output token combination")

    def output(self, input_token, di):
        """
        Calculates the output amount after considering the swap fee.

        :param input_token: Name of input token, either "DAI" or "ETH"
        :type input_token: str
        :param di: Amount of input token
        :type di: float
        :return: The output amount after applying the swap fee
        :rtype: float
        """
        fees = self.swap_fee * di
        _di = di - fees
        if input_token == "DAI":
            new_amt = self.K/(self.X + _di)
            output_amount = self.Y - new_amt 
        if input_token == "ETH":
            new_amt = self.K/(self.Y + _di)
            output_amount = self.X - new_amt
        return output_amount



def simulate_arb(dy, ax, ay, bx, by, sign=1.0):
    """
    Simulates an arbitrage opportunity between two Uniswap pools (pool_a and pool_b).

    :param dy: Amount of DAI to be used in the arbitrage
    :type dy: float
    :param ax: Amount of DAI in pool_a at the start
    :type ax: float
    :param ay: Amount of ETH in pool_a at the start
    :type ay: float
    :param bx: Amount of DAI in pool_b at the start
    :type bx: float
    :param by: Amount of ETH in pool_b at the start
    :type by: float
    :param sign: Multiplier for the arbitrage profit, defaults to 1.0 (positive)
    :type sign: float, optional
    :return: The simulated profit from the arbitrage opportunity
    :rtype: float
    :raises ValueError: If no arbitrage opportunity is available (prices are equal)
    """
    pool_a = UniswapPool(ax, ay)
    pool_b = UniswapPool(bx, by)
    a_price, b_price = pool_a.Y/pool_a.X, pool_b.Y/pool_b.X 
    if b_price > a_price:
        return sign * (pool_b.swap('DAI', pool_a.swap('ETH', dy)) - dy)
    elif a_price > b_price:
        return sign * (pool_a.swap('DAI', pool_b.swap('ETH', dy)) - dy)
    else:
        raise ValueError("No arbitrage opportunity available")
    


def optimal_profit(ax, ay, bx, by):
    """
    Finds the optimal profit from an arbitrage opportunity between two Uniswap pools (pool_a and pool_b).

    :param ax: Amount of DAI in pool_a at the start
    :type ax: float
    :param ay: Amount of ETH in pool_a at the start
    :type ay: float
    :param bx: Amount of DAI in pool_b at the start
    :type bx: float
    :param by: Amount of ETH in pool_b at the start
    :type by: float
    :return: 1 if an arbitrage opportunity is found, 0 otherwise
    :rtype: int
    :raises ValueError: If no arbitrage opportunity is available (prices are equal) or if input amounts are invalid
    """
    if ax <= 0 or ay <= 0 or bx <= 0 or by <= 0:
        raise ValueError("Invalid input token amounts: cannot have negative or zero tokens")
    if ay/ax == by/bx:
        raise ValueError("No arbitrage opportunity available") 
    a, b = ax + ay, bx + by
    total = a + b
    lower, upper = 1e-05, b/total * abs(ax - ay) + a/total * abs(bx - by)
    midpoint = upper/2
    if by/bx > ay/ax:
        b, s = 'A', 'B'
    else:
        b, s = 'B', 'A'
    res = minimize(simulate_arb, x0=midpoint, bounds=Bounds(lower,upper), args=(ax, ay, bx, by, -1))
    eth_in, eth_profit = res.x[0], -res.fun
    if -res.fun <= 0:
        print(f"Negative profit of {-res.fun} - no arbitrage opportunity exists")
        return 0 
    print(f'ETH in: {eth_in} | ETH profit: {-res.fun}')
    print(f"Buy DAI in pool {b} with {eth_in} ETH and sell it in pool {s} for a profit of {eth_profit}")
    return 1


@click.command()
@click.option('--r', prompt='Randomize inputs?', required=True, is_flag=True)
def run_optimal_profit(r):
    """
    Command-line interface for running the optimal_profit function with user input or random values.

    :param r: Flag indicating whether to randomize inputs
    :type r: bool
    """
    if r:
        ax = random.uniform(7000000, 8000000)
        ay = random.uniform(3000, 5000)
        bx = random.uniform(7000000, 8000000)
        by = random.uniform(3000, 5000)
        click.echo(f"Randomly generated values: X1: {ax}, Y1: {ay}, X2: {bx}, Y2:{by}")
    else:
        ax = click.prompt('Enter DAI in pool A (X1)', type=float)
        ay = click.prompt('Enter ETH in pool A (Y1)', type=float)
        bx = click.prompt('Enter DAI in pool B (X2)', type=float)
        by = click.prompt('Enter ETH in pool B (Y2)', type=float)

    optimal_profit(ax, ay, bx, by)

    
if __name__ == '__main__':
    run_optimal_profit()