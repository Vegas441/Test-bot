from typing import List
import pandas as pd

class Market:
    name: str = None
    positions: List[Position] = None
    price_data: pd.DataFrame = None

    # add second parameter with historical prices already 
    # fetched by main class when initializing it after this functions properly

    def __init__(self, name: str, price_data: pd.DataFrame = pd.DataFrame(), positions: pd.DataFrame = pd.DataFrame()) -> None:
        self.name = name
        self.positions = positions
        self.price_data = price_data
        

    def append_price_data(self, new_price_data: pd.DataFrame) -> None:
        self.price_data.append(new_price_data, ignore_index=True)

    def find_extremes(self) -> None:
        pass
    
    def find_zones(self) -> None:
        pass