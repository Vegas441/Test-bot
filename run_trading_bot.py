from EMA_strategy import EMA_strategy
from Ftx_client import Ftx_client
from Trader import Trader
from trader_config import INIT_MARKETS, LOOP_PAUSE
import logging
from time import sleep

# API used:
BROKER_API = Ftx_client()

# Strategy:
STRATEGY = EMA_strategy(INIT_MARKETS)

# Logger
REAL_TIME_LOG_FILE = 'real_time_trader.log'
TEST_LOG_FILE = ''

def run_trading_bot() -> None:
    logging.basicConfig(filename=REAL_TIME_LOG_FILE, level=logging.INFO ,format='%(asctime)s [%(levelname)s]: %(message)s')
    logging.info('Beggining initialization of Trader class.')
    trader = Trader(INIT_MARKETS, BROKER_API, STRATEGY)
    logging.info('Ending Initialization.')
    logging.info('Begging main loop of Trader.')
    while True:
        if not trader.engage_routine():
            break
        sleep(LOOP_PAUSE)
    logging.info('Ending main loop of Trader.')
    logging.info('Shutting down Trader.')
    


def test_trader() -> None:
    trader = Trader(INIT_MARKETS, BROKER_API, STRATEGY)
    print(trader.watched_markets)
    print(trader.watched_markets['BTC-PERP'].price_data)

def test_api_client() -> None:
    a = Ftx_client()
    b = a.get_position('BTC-PERP')
    c = a.get_fills_market('BTC-PERP')
    print(b)
    print(c)
        
#test_trader()
test_api_client()
        