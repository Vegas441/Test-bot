import pandas as pd

class Market:
    name: str = None
    zones: pd.DataFrame = None
    extremes: pd.DataFrame = None
    price_data: pd.DataFrame = None

    # add second parameter with historical prices already 
    # fetched by main class when initializing it after this functions properly

    def __init__(self, name: str) -> None:
        self.name = name
        self.zones = pd.DataFrame()
        self.extremes = pd.DataFrame()
        self.price_data = pd.DataFrame()

    def append_price_data(self, new_price_data: pd.DataFrame) -> None:
        self.price_data.append(new_price_data, ignore_index=True)