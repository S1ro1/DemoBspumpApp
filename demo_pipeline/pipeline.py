import bspump
import bspump.common
import bspump.kafka
import bspump.trigger
from .create_alarms_processor import CreateAlarmsGenerator

class DemoPipeline(bspump.Pipeline):
    def __init__(self, app, pipeline_id):
        super().__init__(app, pipeline_id)

        self.build(
            # Kafka source
            bspump.kafka.KafkaSource(app, self, "KafkaConnection"),
            bspump.common.BytesToStringParser(app, self),
            bspump.common.StdJsonToDictParser(app, self),

            CreateAlarmsGenerator(app, self),

            bspump.common.StdDictToJsonParser(app, self),
            bspump.common.StringToBytesParser(app, self),
            bspump.kafka.KafkaSink(app, self, "KafkaConnection"),
        )
