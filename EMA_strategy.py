import pandas as pd
from Position import Order, Position
from datetime import timedelta
from Market import Market
from typing import Dict, List, Optional, Tuple
from trader_config import ACCEPATBLE_PERCENTGE_FROM_EMA_FOR_CLOSE, ACCEPATBLE_PERCENTGE_FROM_EMA_FOR_OPEN, EMA_INTERVAL, RISK_PER_TRADE, SL_IN_TRADE_PERCENTAGE
from trader_config import Market_name, Stop_loss, Take_profit, EMA_data, Time, Todos, Trade

class EMA_strategy:
    update_checkpoint = timedelta(minutes=15)
    markets_EMA: Dict[Market_name, pd.DataFrame] = dict()
    market_last_check: Dict[Market_name, Time] = dict()

    def __init__(self, markets: List[Market_name]) -> None:
        for market_name in markets:
            self.markets_EMA[market_name] = []
            self.market_last_check[market_name] = None

    def evaluate_market(self, account_info: dict, market: Market) -> List[Todos]:
        self.calculate_EMA(market)
        todos = self.evaluate_price_action(account_info, market)
        return todos

    def calculate_EMA(self, market: Market) -> None:
        last_check = self.market_last_check[market.name]
        last_EMA = market.price_data['close'].loc[0:EMA_INTERVAL - 1].sum(axis=0) / EMA_INTERVAL if last_check is None \
            else self.markets_EMAs[market.name][-1][1]

        relevant_candles = market.price_data.loc[20:] if last_check is None else \
            market.price_data.loc[market.price_data['time'] > last_check]

        market_EMAs = {
            'time': [],
            'EMA': []
        }

        for _, row in relevant_candles.iterrows():
            close = row['close']
            time = row['time']
            last_EMA = (2 / (EMA_INTERVAL + 1)) * (close - last_EMA) + last_EMA
            market_EMAs['time'].append(time)
            market_EMAs['EMA'].append(last_EMA)
        
        self.markets_EMAs[market.name] = pd.DataFrame(market_EMAs)
        self.market_last_check[market.name] = market_EMAs['startTime'][-1]

    def get_last_EMA(self, market: Market) -> float:
        return self.markets_EMA[market.name]['EMA'].tail(1).iloc[0,1]

    def difference_price_EMA(self, market: Market) -> float:
        return market.get_last_price_close() - self.get_last_EMA(market)

    def can_open_position(self, market: Market, price_EMA_diff: float) -> bool:
        ''' Returns if position can be opened. (is in acceptable range)
        '''
        return ACCEPATBLE_PERCENTGE_FROM_EMA_FOR_OPEN >= (abs(price_EMA_diff) / market.get_last_price_close())

    def can_close_position(self, market: Market, price_EMA_diff: float) -> bool:
        ''' Returns if position can be closed. (is in acceptable range)
        '''
        return ACCEPATBLE_PERCENTGE_FROM_EMA_FOR_CLOSE >= (abs(price_EMA_diff) / market.get_last_price_close())

    def asses_risk(self, account_info: dict, market: Market, sl_side: str, price_EMA_diff: float) -> Tuple[float, Order, float]:
        ''' Calculates position sizing and SL order according to strategy risk managment.
        '''
        perc_sl_EMA = (1 + SL_IN_TRADE_PERCENTAGE) if sl_side == 'buy' else (1 - SL_IN_TRADE_PERCENTAGE)
        trigger_price = self.get_last_EMA(market) * perc_sl_EMA
        perc_sl_last_close = perc_sl_EMA + (abs(price_EMA_diff) / market.get_last_price_close())
        size = min((RISK_PER_TRADE / perc_sl_last_close) * account_info['collateral'], account_info['freeCollateral'])
        leverage = min(size / account_info['freeCollateral'], 4)

        sl_specs = {
            "market": market.name,
            "side": sl_side,
            "triggerPrice": trigger_price,
            "size": size,
            "type": "stop",
            "reduceOnly": True
        }

        return size, Order('conditional', sl_specs), leverage
        
    def asses_reward(self, market: Market, tp_side: str, size: float) -> Take_profit:
        ''' Calculates take profit order according to rules.
        '''
        trigger_price = market.get_last_price_close() * (1 + 0.3 if tp_side == 'buy' else 1 - 0.3)
        tp_specs = {
            "market": market.name,
            "side": tp_side,
            "triggerPrice": trigger_price,
            "size": size,
            "type": "takeProfit",
            "reduceOnly": True,
            "retryUntilFilled" : True
        }
        return Order('conditional', tp_specs)

    def create_trade(self, account_info: dict, market: Market, side: str , price_EMA_diff: float) -> Trade:
        ''' Creates new position on market side according to rules.
            Sets SL and TP orders, position size and leverage.
        '''
        size, sl_order, leverage = self.asses_risk(account_info, market, 'buy' if side == 'sell' else 'sell', price_EMA_diff)
        order_specs = {
            'market' : market.name,
            'side' : side,
            'price' : None,
            'size' : size,
            'limit' : 'market',
            'reduceOnly' : False,
            'ioc' : False,
            'postOnly' : False,
            'clientId' : None
        }
        position_order = Order('normal', order_specs)
        position = Position(None, leverage, [sl_order], [self.asses_reward('buy' if side == 'sell' else 'sell', market, size)], is_triggered=False)
        return (position_order, position)

    def create_close_order(self, position: Position) -> Order:
        side = 'buy' if position.specs['side'] == 'sell' else 'sell'
        close_order = {
            "market": position.specs['future'],
            "side": side,
            "price": None,
            "type": "market",
            "size": position.specs['openSize'], # treba odtestovat not sure about this
            "reduceOnly": True,
            "ioc": False,
            "postOnly": False,
            "clientId": None
        }
        return Order('normal', close_order)

    def update_position(self, position: Position, market: Market, 
                        price_EMA_diff: float, evaluated_side: str) -> List[Todos]:
        ''' Checks if price can be closed or even more switched in oposite direction.
            Returns list of todos for trader that will handle what needs to be done.
        '''
        todos = []
        if position.specs['side'] == evaluated_side:
            needed_word = 'above' if evaluated_side == 'buy' else 'below'
            print(f'Price closed {needed_word} EMA and doing nothing for now')
        elif not self.can_close_position(market, price_EMA_diff):
            needed_words = 'above EMA on sell' if evaluated_side == 'buy' else 'below EMA on buy'
            print(f'Price closed {needed_words} side of the trade but is in acceptable range')
        else:
            todos.append(('close', position))
            if self.can_open_position(market, price_EMA_diff):
                todos.append(('open', self.create_trade(market, evaluated_side, price_EMA_diff)))       
        return todos

    def evaluate_price_action(self, account_info: dict, market: Market) -> List[Todos]:
        ''' Creates commands for Trader class according results
            of strategy rules applied on price action
            Rules:
                1.) Market is always in 1 position
                2.) Position is evaluated according to last candle close and it's EMA value
        '''
        todos = []
        price_EMA_diff = self.difference_price_EMA(market)
        if market.in_position():
            market_position = market.positions[0]
            if price_EMA_diff > 0:
                todos = self.update_position(account_info, market_position, market, price_EMA_diff, 'buy')
            elif price_EMA_diff < 0:
                todos = self.update_position(account_info, market_position, market, price_EMA_diff, 'sell')
        else:
            new_position = None
            if self.price_in_acceptable_range_from_EMA(market, price_EMA_diff):
                if price_EMA_diff > 0:
                    new_position = self.create_trade(account_info, market, 'buy', price_EMA_diff)
                elif price_EMA_diff < 0:
                    new_position = self.create_trade(account_info, market, 'sell', price_EMA_diff)
                if new_position is not None:
                    todos.append(('open', new_position))
        return todos

    