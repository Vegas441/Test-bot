from Trend import Trend
from FtxClient import FtxClient
from typing import Any, Dict, Optional, Tuple, List


class MainBotClass:
    messenger: FtxClient = None
    active_positions: Dict[str, List[Dict[Any, Any]]] = None
    currency_data: Dict[str, List[Tuple[int]]] = None # este rozsir typovanie Tuple podla tvaru celeho data pointu
    trend: Trend = None

    def __init__(self, api_key: Optional[str], api_secret: Optional[str], subaccount_name: Optional[str]) -> None:
        self.messenger = FtxClient(api_key, api_secret, subaccount_name)
        pass
