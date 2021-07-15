from typing import Dict, List

class Order:

    def __init__(self, api_order: dict) -> None:
        self.specs = api_order


class Position:

    def __init__(self, api_position: dict, stop_loss: Order, take_profits: List[Order] ) -> None:
        self.stop_loss = stop_loss
        self.take_profit = take_profits # there can be more than 1 TP
        self.specs = api_position
