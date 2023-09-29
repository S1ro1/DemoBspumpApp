from numbers import Number
import numpy as np
from scipy.stats import gaussian_kde
from collections import defaultdict
from typing import TypeVar, Hashable, Optional
from .model import Model, AlarmVal

T = TypeVar("T", bound=Hashable)


class KDEModel(Model):
    def __init__(self, window_size: Number, alarm_name: str):
        """Constructor for KDE model

        Args:
            window_size (Number): length of a history window size in minutes
            alarm_name (str): name of the alarm
        """
        super().__init__()
        self.window_size = int(window_size * 60 * 1000)
        self._minute_window_size = window_size
        self.alarm_name = alarm_name
        self.kernels: dict[T, Optional[gaussian_kde]] = {}
        self.values: dict[T, list[AlarmVal]] = defaultdict(list)

    def _filter_values(self, id: T, timestamp: int) -> None:
        """filters values that are older than window_size

        Args:
            id (T): id of the metric
            timestamp (int): current timestamp in unix milliseconds
        """
        self.values[id] = list(
            filter(
                lambda x: timestamp - x.timestamp <= self.window_size, self.values[id]
            )
        )

    def train(self, id: T) -> None:
        """tries to create the kde kernel

        Args:
            id (T): id of the metric
        """
        if len(self.values[id]) < self._minute_window_size * 0.10:
            self.kernels[id] = None
        else:
            try:
                self.kernels[id] = gaussian_kde([x.value for x in self.values[id]])
            except (ValueError, np.linalg.LinAlgError):
                self.kernels[id] = None

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

    def predict(self, id: T, value: Number, timestamp: int) -> Optional[dict]:
        """predicts the anomaly score

        Args:
            id (T): id of the metric
            value (Number): value of the metric
            timestamp (int): current timestamp in unix milliseconds

        Returns:
            Optional[dict]: anomaly data or None if there are not enough values
        """
        self._filter_values(id, timestamp)
        self.train(id)
        self.values[id].append(AlarmVal(timestamp, value))

        return (
            None if self.kernels[id] is None else self._score(value, self.kernels[id])
        )
