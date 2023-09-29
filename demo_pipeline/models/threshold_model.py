from numbers import Number
import operator
from typing import Callable
from .model import (
    Model,
    T,
)


class ThresholdModel(Model):
    def __init__(
        self,
        threshold: float,
        alarm_name: str,
        op: Callable[[Number, Number], bool] = operator.gt,
    ) -> None:
        """Constuctor for threshold model

        Args:
            threshold (float, optional): Threshold to compare against.
            op (Callable[[Number, Number], bool], optional): Comparison operation to be used. Defaults to operator.gt.
        """
        super().__init__()
        self.threshold = threshold
        self.op = op
        self.alarm_name = alarm_name

    def predict(self, _id: T, value: Number, _timestamp: int) -> dict:
        """Returns the value if the threshold is exceeded/subceeded

        Args:
            _id (T): id of the metric, not used
            value (Number): Number to be evaluated
            _timestamp (int): Current timestamp in unix milliseconds, not used

        Returns:
            dict: value if the threshold is exceeded/subceeded, None otherwise
        """
        alarm = {}
        alarm["normalized_score"] = 1.0 if self.op(value, self.threshold) else 0.0
        alarm["is_increase"] = (
            True if self.op == operator.gt or self.op == operator.ge else False
        )
        alarm["alarm_name"] = self.alarm_name
        return alarm

    def train(self) -> None:
        """Does nothing, since the model is static"""
        return
