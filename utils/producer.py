from collections import defaultdict
import dataclasses
from pprint import pprint
import random
from kafka import KafkaProducer
import asyncio
import time
import json
import numpy as np
from dataclasses import dataclass


class DataclassEncoder(json.JSONEncoder):
    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        return super().default(obj)


METRICS = [
    "free disk space",
    "processor percent load (1 min average)",
    "incoming network traffic",
    "outgoing network traffic",
    "free ram"
]

HOST_NAMES = {
    "customer1": [
        "host1",
        "host2",
        "host3"
    ],
    "customer2": [
        "host4",
        "host5",
        "host6"
    ],
    "customer3": [
        "host7",
        "host8",
        "host9",
        "host10",
        "host11"
    ],
}


@dataclass
class IdData:
    id: str
    mu: float
    sigma: float


def _setup_itemids(n: int) -> dict:
    ids = {}
    for customer, hosts in HOST_NAMES.items():
        for host in hosts:
            m2ids = defaultdict(list)
            for metric in METRICS:
                for _ in range(n):
                    id = str(random.randint(10**7, 10**8 - 1))
                    match metric:
                        case "free disk space" | "processor percent load (1 min average)":
                            mu_range = (0, 100)
                            sigma_range = (0, 10)
                        case "incoming network traffic" | "outgoing network traffic":
                            mu_range = (0, 10 * 10**9)
                            sigma_range = (1, 0.1 * 10**9)
                        case "free ram":
                            mu_range = (0, 128 * 10**9)
                            sigma_range = (1, 10 * 10**9)
                        case _:
                            raise ValueError(f"Unknown metric {metric}")
                        
                    mu = random.uniform(*mu_range)
                    sigma = random.uniform(*sigma_range)

                    m2ids[metric].append(IdData(id, mu, sigma))

            ids[f"{customer}-{host}"] = m2ids

    return ids


class PeriodicSource:
    def __init__(self, server: str, topic: str, interval: int, ids_per_metric: int):
        self.server = server
        self.topic = topic
        self.interval = interval

        self.producer = KafkaProducer(
            bootstrap_servers=server,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

        self.mapping = _setup_itemids(ids_per_metric)

    def _generate_data(self):
        for host, metrics in self.mapping.items():
            for metric_name, metric_ids in metrics.items():
                for id_data in metric_ids:
                    value = np.random.normal(id_data.mu, id_data.sigma)
                    event = {
                        "timestamp": int(time.time() * 1000),
                        "host": host,
                        "metric": metric_name,
                        "itemid": id_data.id,
                        "device": id_data.id,
                        "value": value,
                        "customer": host.split("-")[0],
                    }
                    yield event

    async def produce(self):
        while True:
            start = time.time()
            for event in self._generate_data():
                self.producer.send(self.topic, event)

            self.producer.flush()
            end = time.time()
            print("Took {} seconds to produce".format(end - start))
            await asyncio.sleep(self.interval)


if __name__ == "__main__":
    src = PeriodicSource("localhost:9093", "src-topic", 60, ids_per_metric=20)

    asyncio.run(src.produce())
