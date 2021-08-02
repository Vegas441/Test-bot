from typing import Tuple
from numpy import positive
from pandas._libs.tslibs.timestamps import Timestamp
from Position import Order, Position
from EMA_strategy import EMA_strategy
from trader_config import CANDLESTICK_RESOLUTION, START_PRICE_RANGE_1H, Trade
from trader_config import Market_name, List,Dict, Stop_loss, Take_profit
from Ftx_client import Ftx_client
from datetime import timedelta, datetime
import pandas as pd
from Market import Market
import logging

class Trader:
    messenger: Ftx_client = None
    account_info = None
    strategy: EMA_strategy = None
    watched_markets: Dict[str, Market] = dict()


    def __init__(self, markets_to_watch: List[Market_name], api_client: Ftx_client, strategy: EMA_strategy, log_file: str) -> None:
        self.messenger = api_client
        self.account_info = self.update_account_info()
        self.strategy = strategy
        for market_name in markets_to_watch:
            self._add_market(market_name)

    def engage_routine(self) -> bool:
        if not self.watched_markets.values():
            logging.info('No markets to process.')
            return False
        for market in self.watched_markets.values():
            self.update_price_data(market)
            self.update_account_info()
            self.apply_strategy(market)
            self.update_positions(market)
        return True

    def update_account_info(self) -> None:
        return self.messenger.get_account_info()

    def _get_market_data(self, market_name) -> Tuple[Market, int, int]:
        ''' Gets market data in right format '''
        start_time = (datetime.now() - timedelta(hours=START_PRICE_RANGE_1H)).timestamp()
        market_prices = \
            pd.DataFrame(self.messenger.get_historical_prices(market=market_name, 
                                                                resolution=CANDLESTICK_RESOLUTION, 
                                                                start_time=start_time
                                                                )[:-1])
        market_position = self._get_market_position(market_name)
        normal_orders_count = len(self.messenger.get_open_orders(market_name))
        conditional_orders_count = len(self.messenger.get_conditional_orders(market_name))
        return Market(market_name, market_position, market_prices), normal_orders_count, conditional_orders_count

    def recog_orders(self, orders: List[dict]) -> Tuple[Stop_loss, List[Take_profit]]:
        '''
        Sorts existing orders in order: Stop_loss, List[Take_profit]
        Works only for Strategy that uses 1 position (therefore many TP and exactly 1 SL order )
        '''
        if not orders:
            return None, None
        Sl_orders = []
        Tp_orders = []
        for order in orders:
            if order['type'] == 'stop' or order['type'] == 'trailingStop':
                Sl_orders.append(order)
            else:
                Tp_orders.append(order)
        return Sl_orders, Tp_orders

    def _get_market_position(self, market: Market_name) -> Position:
        sl_order, tp_orders = self.recog_orders(self.messenger.get_conditional_orders(market))
        position = self.messenger.get_position(market)
        if sl_order and tp_orders and position:
            return Position(position, None, sl_order, tp_orders, is_triggered=True)
        elif not position:
            return None
        else:
            logging.warning(f'Missing SL or TP for position in market [{market}]')
            self.clear_market(market, position)
            return None

    def clear_market(self, market: Market_name, position: Position) -> None:
        ''' Cancels all orders and given position in market.
        '''
        logging.info(f'Market [{market}]: closing position and clearing waiting orders.')
        self.messenger.cancel_orders(market)
        self._palce_orders([self.strategy.create_close_order(position)])

    def _add_market(self, market: Market_name) -> None:
        try:
            self.messenger.get_market(market)
        except Exception as e:
            logging.warning(f'Api error with market: [ {market} ], error message: {e}, Result: market not added.')
        else:
            self.watched_markets[market], normal_ords, cond_ords = self._get_market_data(market)
            if not self.watched_markets[market].positions:
                self.messenger.cancel_orders(market)
            logging.info(f'Market [{market}] added succesfully with: {normal_ords} normal orders & {cond_ords} conditional orders.')

    def close_position(self, order: Order) -> None:
        ''' Closes all conditional orders in the market.
            Closes given position in the market.
        '''
        position_side = 'Long' if order.specs['side'] == 'sell' else 'Short'
        market_name = order.specs['market']
        logging.info(f'Closing position in market [{market_name}].')
        self.messenger.cancel_orders(order.specs['market'], conditional_orders=True)
        logging.info(f'Cancelling all orders in market [{market_name}].')
        self._palce_orders([order])
        logging.info(f'{position_side} position closed in market [{market_name}].')

    def open_position(self, order: Order) -> None:
        position_side = 'Long' if order.specs['side'] == 'sell' else 'Short'
        market_name = order.specs['market']
        logging.info(f'{position_side} position order placed in market [{market_name}].')
        self._palce_orders([order])

    def set_leverage(self, value: float) -> None:
        self.messenger.set_account_leverage(value)
        logging.info(f'Changing account leverage to {value}x.')

    def apply_strategy(self, market: Market) -> None:
        ''' Applies strategy to given market.
        '''
        todos = self.strategy.evaluate_market(self.account_info, market)
        for todo, cargo in todos:
            if todo == 'close':
                self.close_position(cargo)
                market.remove_position(cargo)
            elif todo == 'open':
                position_order, position = cargo
                self.set_leverage(position.leverage)
                self.open_position(position_order)
                market.add_waiting_trade((position_order, position))

    def update_positions(self, market: Market) -> None:
        ''' Checks if position got filled, if yes position gets 
            updated with actual api fill info and all her orders 
            (SL and TP) will be placed, after that it's added to 
            market positions for track keeping.
        '''
        start_time = self.strategy.market_last_check[market.name] # bacha je to float treba zistit ci funguje a ci netreba zaokruhlit realtime dobre
        new_waiting_trades = []
        for waiting_trade in market.waiting_trades:
            position_triggered = self.messenger.get_fills_market(market, start_time, order_id=waiting_trade[0]['orderId'])
            if position_triggered:
                new_position = waiting_trade[1]
                new_position.update_specs(self.messenger.get_position_by_specs(position_triggered['price']))
                self._place_orders(new_position.stop_losses + new_position.take_profits)
                new_position.triggered_successfully()
                market.add_position(new_position)
                logging.info(f'Opened position: {new_position}.')
            else:
                new_waiting_trades.append(waiting_trade)
        market.replace_waiting_trades(new_waiting_trades)

    def _palce_orders(self, orders: List[Order]) -> List[dict]:
        ''' Makes messenger place all orders in given list.
        '''
        placed_orders = []
        for order in orders:
            if order.type == 'conditional':
                placed_orders.append(self.messenger.place_conditional_order(
                    market=order.specs['market'],
                    side=order.specs['side'],
                    trigger_price=order.specs['triggerPrice'],
                    trail_value=order.specs['trailValue'],
                    size=order.specs['size'],
                    reduce_only=order.specs['reduceOnly'],
                    type=order.specs['type'],
                    cancel=order.specs['cancelLimitOnTrigger'],
                    limit_price=order.specs['orderPrice']
                ))
            elif order.type == 'normal':
                placed_orders.append(self.messenger.place_order(
                    market=order.specs['market'],
                    side=order.specs['side'],
                    price=order.specs['price'],
                    size=order.specs['size'],
                    type=order.specs['type'],
                    reduce_only=order.specs['reduceOnly'],
                    ioc=order.specs['ioc'],
                    post_only=order.specs['postOnly'],
                    client_id=order.specs['clientId']
                ))
            market_name = order.specs['market']
            order_type = order.specs['type'].capitalize()
            logging.info(f'Placed order: {order}.')
        return placed_orders

    def update_price_data(self, market: Market) -> None:
        ''' Updates price data of a market to the 
            depth of strategy update_checkpoint.
        '''
        #start_time = (datetime.strptime(market.price_data.tail(1).iloc[0,0], 
        #                                '%Y-%m-%dT%H:%M:%S+00:00'
        #                                ) + self.strategy.update_checkpoint).timestamp()
        # mozno bude fungovat aj takto
        
        start_time = market.get_last_price_time() + self.strategy.update_checkpoint.timestamp()
        market.load_price_data(pd.DataFrame(self.messenger.get_historical_prices(market=market.name, 
                                                                                 resolution=CANDLESTICK_RESOLUTION, 
                                                                                 start_time=start_time 
                                                                                 )[:-1]))
        logging.info(f'Updating price data for market [{market.name}].')


    
    