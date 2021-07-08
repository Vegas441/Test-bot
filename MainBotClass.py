from datetime import datetime, timedelta
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
            # gets me last hour of price action in 5M chart
            start_time = (datetime.now() - timedelta(hours=1)).timestamp()
            market_prices = \
                pd.DataFrame(self.messenger.get_historical_prices(market=market_name, 
                                                                  resolution=300, 
                                                                  starTime=start_time
                                                                  )) 
            market_prices.drop(columns=['time', 'volume'], inplace=True)
            market_positions = \
                pd.DataFrame(self.messenger.get_position(name=market_name))
            self.watched_markets[market_name] = Market(market_name, market_prices, market_positions)

    def update_price_data(self) -> None:
        for market in self.watched_markets.values():
            start_time = datetime.strptime(market.price_data.tail(1).iloc[0,0], 
                                           '%Y-%m-%dT%H:%M:%S+00:00'
                                           ).timestamp() + timedelta(minutes=5)
            market.append_price_data(self.messenger.get_historical_prices(market=market.name, 
                                                                          resolution=300, 
                                                                          startTime=start_time 
                                                                          ))

    

a = MainBotClass(['BTC/USD']).update_price_data()
#print(a['BTC/USD'].price_data)
print()

