import abc
import logging

from api_etl.adapters import DataAdapter
from api_etl.sinks import DataSink
from api_etl.sources import DataSource

logger = logging.getLogger(__name__)


class ETLService(metaclass=abc.ABCMeta):
    """
    ETL Service class representing a full ETL pipeline
    """

    def __init__(self,
                 source: DataSource,
                 adapter: DataAdapter,
                 sink: DataSink):
        self.source = source
        self.adapter = adapter
        self.sink = sink

    def execute(self):
        """
        Execute the ETL pipeline created by chaining the source, adapter and sink
        """
        try:
            raw_data = self.source.pull()
        except self.source.Error as e:
            logger.error("Error while pulling data from source: %s", str(e), exc_info=e)
            return self._error_result(str(e))

        try:
            transformed_data = self.adapter.transform(raw_data)
        except self.adapter.Error as e:
            logger.error("Error while transforming data: %s", str(e), exc_info=e)
            return self._error_result(str(e))

        try:
            self.sink.push(transformed_data)
        except self.sink.Error as e:
            logger.error("Error while pushing data to sink: %s", str(e), exc_info=e)
            return self._error_result(str(e))

        return self._success_result()

    @staticmethod
    def _error_result(detail):
        return {"success": False, "message": "Failed to execute ETL pipeline", "detail": detail}

    @staticmethod
    def _success_result():
        return {"success": True, "data": None}
