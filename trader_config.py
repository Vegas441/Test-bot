from typing import Dict, List, Tuple, Optional
from Position import Position, Order

Market_name = str
Stop_loss = Optional[Order]
Take_profit = Optional[Order]
Leverage = float
Trade = Tuple[Order, Position, Leverage]
Time = float
EMA_value = float
EMA_data = Tuple[Time, EMA_value]
Command = List[str]
Todos = List[Tuple[Command, Position]]

# Trader config:
INIT_MARKETS = [
    'BTC-PERP',
    'ETH/USD'
]

# API used:
#BROKER_API = Ftx_client()

# Strategy:
#STRATEGY = EMA_strategy(INIT_MARKETS)

LOOP_PAUSE = 300
RISK_PER_TRADE = 0.01
SL_IN_TRADE_PERCENTAGE = 0.0025
ACCEPATBLE_PERCENTGE_FROM_EMA_FOR_CLOSE = 0.1
ACCEPATBLE_PERCENTGE_FROM_EMA_FOR_OPEN = 0.1
EMA_INTERVAL = 21
START_PRICE_RANGE_1H = 24
PRICE_RANGE_5M = 4
CANDLESTICK_RESOLUTION = 300
