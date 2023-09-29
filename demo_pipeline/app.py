import bspump
import bspump.kafka

from demo_pipeline.pipeline import DemoPipeline


class DemoApp(bspump.BSPumpApplication):
    def __init__(self):
        super().__init__()

        svc = self.get_service("bspump.PumpService")
        svc.add_connection(bspump.kafka.KafkaConnection(self, "KafkaConnection"))

        svc.add_pipeline(DemoPipeline(self, "DemoPipeline"))
