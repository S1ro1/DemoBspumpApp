import operator
from .models.model import Model
from .models.threshold_model import ThresholdModel
from .models.kde_model import KDEModel
from .models.kde_sliding_model import KDESlidingModel
import yaml


class ConfigLoader:
    """Class that loads config from yaml file
    To load config, call method load_config with path to yaml file
    """

    operator_mapping = {
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
        "=": operator.eq,
    }

    # tags that are used for models
    tags = ["!threshold", "!kde", "!kde_sliding"]

    @staticmethod
    def threshold_constructor(loader: yaml.Loader, node: yaml.Node) -> ThresholdModel:
        """Constructor for threshold model

        Args:
            loader (yaml.Loader): yaml loader (safeloader used by default)
            node (yaml.Node): yaml node with model parameters

        Raises:
            ValueError: if operator is not supported

        Returns:
            ThresholdModel: new threshold model instance
        """
        mapping = loader.construct_mapping(node)
        if mapping["op"] not in ConfigLoader.operator_mapping:
            raise ValueError(f"Operator {mapping['op']} is not supported")

        mapping["op"] = ConfigLoader.operator_mapping[mapping["op"]]
        return ThresholdModel(**mapping)

    @staticmethod
    def kde_constructor(loader: yaml.Loader, node: yaml.Node) -> KDEModel:
        """Constructor for KDE model

        Args:
            loader (yaml.Loader): yaml loader (safeloader used by default)
            node (yaml.Node): yaml node with model parameters

        Returns:
            KDEModel: new KDE model instance
        """
        mapping = loader.construct_mapping(node)
        return KDEModel(**mapping)

    @staticmethod
    def kde_sliding_constructor(
        loader: yaml.Loader, node: yaml.Node
    ) -> KDESlidingModel:
        """Constructor for KDE sliding model

        Args:
            loader (yaml.Loader): yaml loader (safeloader used by default)
            node (yaml.Node): yaml node with model parameters

        Returns:
            KDESlidingModel: new KDE model with sliding window instance
        """
        mapping = loader.construct_mapping(node)
        return KDESlidingModel(**mapping)

    @classmethod
    def load_config(cls, config_path: str) -> dict[str, list[Model]]:
        """Loads config from yaml file

        Args:
            config_path (str): path to the yaml file

        Returns:
            dict[str, list[Model]]: dictionary with metric names as keys and list of models as values
        """

        loader = yaml.SafeLoader
        for tag in cls.tags:
            # adds the constructor for each tag
            loader.add_constructor(tag, getattr(cls, tag[1:] + "_constructor"))

        with open(config_path, "r") as f:
            config = yaml.load(f, Loader=loader)

        return config
