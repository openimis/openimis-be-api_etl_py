import abc
from typing import Any


class DataSource(metaclass=abc.ABCMeta):
    """
    Represents Data Source
    Provides the data for Data Adapter
    """

    class Error(Exception):
        pass

    @abc.abstractmethod
    def pull(self) -> Any:
        raise NotImplementedError("pull() not implemented")
