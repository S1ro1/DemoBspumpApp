from collections import defaultdict
import random
from kafka import KafkaProducer
import asyncio
import time
import json

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


def _setup_itemids(n: int) -> dict:
    ids = {}
    for customer, hosts in HOST_NAMES.items():
        for host in hosts:
            m2ids = defaultdict(list)
            for metric in METRICS:
                for _ in range(n):
                    m2ids[metric].append(str(random.randint(10**7, 10**8 - 1)))

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

    async def produce(self):
        while True:
            self.producer.send(self.topic, {"name": "new", "timestamp": int(time.time() * 1000)})
            await asyncio.sleep(self.interval)


if __name__ == "__main__":
    src = PeriodicSource("localhost:9093", "sample_input_topic", 1)

    asyncio.run(src.produce())
