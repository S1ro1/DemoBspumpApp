from numbers import Number
import numpy as np
from scipy.stats import gaussian_kde
from statistics import mean
from collections import defaultdict
from typing import (
    TypeVar,
    Hashable,
    Optional,
)
from .model import Model, AlarmVal

T = TypeVar("T", bound=Hashable)


class KDESlidingModel(Model):
    def __init__(
        self,
        history_window_size: Number,
        sliding_window_size: Number,
        alarm_name: str,
    ) -> None:
        """Constructor for KDE model with sliding window

        Args:
            history_window_size (Number): length of a history window size in minutes
            sliding_window_size (Number): length of a sliding window size in minutes
            alarm_name (str): name of the alarm
        """
        super().__init__()
        self.history_window_size = int(history_window_size * 60 * 1000)
        self.sliding_window_size = int(sliding_window_size * 60 * 1000)
        self._history_minute_size = history_window_size
        self._sliding_minute_size = sliding_window_size
        self.alarm_name = alarm_name

        self.total_window_size: int = (
            self.history_window_size + self.sliding_window_size
        )
        self.values: dict[T, list[AlarmVal]] = defaultdict(list)
        self.history_values: dict[T, list[AlarmVal]] = defaultdict(list)
        self.kernels: dict[T, Optional[gaussian_kde]] = {}

    def _split_values(self, id: T, timestamp: int) -> Optional[Number]:
        """splits values into history and sliding windows

        Args:
            id (T): id of the metric
            timestamp (int): current timestamp in unix milliseconds

        Returns:
            Optional[Number]: mean of the sliding window or None if there are not enough values
        """
        self.values[id] = list(
            filter(
                lambda x: timestamp - x.timestamp <= self.total_window_size,
                self.values[id],
            )
        )

        self.history_values[id] = list(
            filter(
                lambda x: x.timestamp <= timestamp - self.sliding_window_size,
                self.values[id],
            )
        )

        sliding_values = list(
            filter(
                lambda x: x.timestamp > timestamp - self.sliding_window_size,
                self.values[id],
            )
        )

        if len(sliding_values) < self._sliding_minute_size * 0.75:
            return None

        return mean(sliding_values)

    def _score(self, value: Number, kernel: gaussian_kde) -> dict:
        """calculates the anomaly score and returns dictionary with metadata

        Args:
            value (Number): value of the metric
            kernel (gaussian_kde): gaussian kernel to use for calculating the score

        Returns:
            dict: alarm metadata
        """
        prob_1 = kernel.integrate_box(value, np.inf)
        prob_2 = 1 - prob_1
        p_val_kde = min(prob_1, prob_2)

        alarm = {}
        alarm["normalized_score"] = round(1 - (p_val_kde * 2), 3)
        alarm["is_increase"] = prob_1 < 0.5
        alarm["alarm_name"] = self.alarm_name
        return alarm

    def train(self, id: T) -> None:
        """tries to create the kde kernel

        Args:
            id (T): id of the metric
        """
        if len(self.history_values[id]) < self._history_minute_size * 0.75:
            self.kernels[id] = None
        else:
            try:
                self.kernels[id] = gaussian_kde(
                    [x.value for x in self.history_values[id]]
                )
            except (ValueError, np.linalg.LinAlgError):
                self.kernels[id] = None

    def predict(self, id: T, value: Number, timestamp: int) -> Optional[dict]:
        """predicts the anomaly score

        Args:
            id (T): id of the metric
            value (Number): value of the metric
            timestamp (int): current timestamp in unix milliseconds

        Returns:
            Optional[dict]: anomaly data or None if there are not enough values
        """
        mean_val = self._split_values(id, timestamp)
        if mean_val is None:
            return None
        self.train(id)
        self.values[id].append(AlarmVal(timestamp, value))

        return (
            None
            if self.kernels[id] is None
            else self._score(mean_val, self.kernels[id])
        )
