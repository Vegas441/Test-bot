from typing import List


class Order:

    def __init__(self, type: str, api_order: dict) -> None:
        ''' type: 'normal' or 'conditional'
        '''
        self.type = type
        self.specs = api_order

    def __str__(self) -> str:
        typos = self.sepcs['type']
        market = self.specs['market']
        if self.type == 'normal':
            price = self.specs['price']
            return f'[market: {market}, type: normal, subtype: {typos}, price: {price}]'
        else:
            trig_price = self.specs['triggerPrice']
            order_price = self.specs['orderPrice']
            return f'[market: {market}, type: conditional, subtype: {typos}, trigger price: {trig_price}, order price: {order_price}]'

class Position:
    def __init__(self, api_position: dict, leverage: float, stop_losses: List[Order], take_profits: List[Order], is_triggered: bool) -> None:
        self.is_triggered = is_triggered
        self.leverage = leverage
        self.stop_losses = stop_losses
        self.take_profits = take_profits
        self.specs = api_position

    def __str__(self) -> str:
        market = self.specs['market']
        side = self.specs['side']
        size = self.specs['size']
        entry_price = self.specs['entryPrice']
        return f'[market: {market}, side: {side}, size: {size}, leverage: {self.leverage} entry: {entry_price}, SL: {self.stop_losses}, TP: {self.take_profits}]'

    def update_specs(self, new_position_specs: dict) -> None:
        self.specs = new_position_specs

    def triggered_successfully(self) -> None:
        self.is_triggered = True