from Position import Order, Position
from typing import Dict, Optional, Tuple
from Market import Market

Trade = Tuple[Order, Position]

class Strategy:
    extremes = []

    def __init__(self) -> None:
        pass

    def evaluate_market(market: Market) -> Optional[Trade]:
        ''' 
        Returns possible Trade for given market,
        consiting of Order and Position. 
        Order triggers given Position. 
        '''
        pass