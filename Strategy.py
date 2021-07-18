from Position import Order, Position
from typing import Dict, List, Optional, Tuple
from Market import Market
from scipy.signal import argrelextrema
import numpy as np
from strategy_config import PRICE_RANGE_CHECKED
from enum import Enum


Trade = Tuple[Order, Position]
Date = str
Price = int
Weight = int # datapoint importance
Market_name = str
Datapoint = str

class Trend(Enum):
    UP = 0
    DOWN = 1
    CONSOLIDATION = 2

class Strategy:
    market_datapoints = dict()
    market_last_check = dict()

    def __init__(self,watched_markets: Dict[str, Market]) -> None:
        for market_name, market in watched_markets.items():
            self.market_datapoints[market_name] = dict()
            self.analyze_price_action(market)

    def evaluate_market(self, market: Market) -> Optional[Trade]:
        ''' 
        Returns possible Trade for given market,
        consiting of Order and Position. 
        Order triggers given Position. 
        '''
        if market.has_active_position():
            return None

        self.update_analysis(market)

        if self.market_datapoints['trend'] == Trend.UP:
            return None
        elif self.market_datapoints['trend'] == Trend.DOWN:
            return None
        return None

    def analyze_price_action(self, market: Market, start_time: str = None) -> None:
        relevant_candles = market.price_data
        if start_time is not None:
            relevant_candles = market.price_data.loc[market.price_data['startTime'] > start_time]

        self.market_datapoints['top'] = argrelextrema(relevant_candles['high'].values, np.greater, 
                   order=PRICE_RANGE_CHECKED)
        self.market_datapoints['bottom'] = argrelextrema(relevant_candles['low'].values, np.less, 
                   order=PRICE_RANGE_CHECKED)
        self.calculate_zones()

    def calculate_zones(self) -> None:
        pass # TODO

    def update_analysis(self, market: Market) -> None:
        last_historical_price = market.price_data.tail(1).iloc[0,0]
        if last_historical_price != self.market_last_check[market.name]:
            self.analyze_price_action(market, self.market_last_check[market.name])


        
        