import bspump
from .utils import ConfigLoader


class CreateAlarmsGenerator(bspump.Generator):
    def __init__(self, app, pipeline, id=None, config=None):
        super().__init__(app, pipeline, id=None, config=None)
        self.dispatch_dict = ConfigLoader.load_config("config.yaml")

    async def generate(self, context, event, depth):
        if (
            event.get("itemid") is None
            or event.get("value") is None
            or event.get("timestamp") is None
        ):
            return

        # Runs the corresponding analyzer for the metric
        metric = event.get("metric", "")
        if metric in self.dispatch_dict:
            for model in self.dispatch_dict[metric]:
                event_copy = event.copy()
                alarm_data = model.predict(
                    event_copy["itemid"], event_copy["value"], event_copy["timestamp"]
                )
                if alarm_data is not None:
                    event_copy.update(alarm_data)
                self.Pipeline.inject(context, event_copy, depth)
