from abc import ABC, abstractmethod
from typing import Any


class MarketDataProvider(ABC):
    @abstractmethod
    def get_instruments(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_historical_candles(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_quote(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def subscribe_market_feed(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_market_data(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError
