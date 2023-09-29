from collections import namedtuple
from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    TypeVar,
    Any,
    Hashable,
)

T = TypeVar("T", bound=Hashable)


class Model(ABC):
    """Base class for all models""" ""

    @abstractmethod
    def predict(self, *args, **kwargs) -> Any:
        raise NotImplementedError

    @abstractmethod
    def train(self, *args, **kwargs) -> None:
        raise NotImplementedError


class OperationError(Exception):
    pass


AlarmVal = namedtuple("AlarmVal", ["timestamp", "value"])
