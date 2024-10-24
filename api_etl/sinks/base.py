import abc
from typing import Any


class DataSink(metaclass=abc.ABCMeta):
    """
    Represents Data Sink
    Allows to store the result of Data Adapter
    """

    class Error(Exception):
        pass

    @abc.abstractmethod
    def push(self, data: Any):
        """
        Push data to the data sink
        The data format is dependent on the Data Adapter user for this sink
        """
        raise NotImplementedError("push() not implemented")
