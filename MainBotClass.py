from Market import Market
import pandas as pd
from FtxClient import FtxClient
from typing import Any, Dict, Optional, Tuple, List


class MainBotClass:
    messenger: FtxClient = None
    watched_markets: Dict[str, Market] = None

    def __init__(self, markets: List[str]) -> None:
        self.messenger = FtxClient()
        self.watched_markets = dict()
        for market_name in markets:
            self.add_market(market_name)
    

    def add_market(self, market_name: str) -> None:
        try:
            self.messenger.get_market(market_name)
        except Exception as e:
            # Log error event (commandline print for now):
            print(e)
        else:
            # should add initialization with historical prices so it can 
            # be computed right away in Market constructor
            self.watched_markets[market_name] = Market(market_name)

a = MainBotClass(['BTC/USD', 'BRAIN_FUCK', 'ETH/BTC']).watched_markets
print()

