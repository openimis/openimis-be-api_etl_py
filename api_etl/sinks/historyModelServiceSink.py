import logging

from django.db import transaction

from api_etl.sinks import DataSink
from core.services import BaseService

logger = logging.getLogger(__name__)


class HistoryModelServiceSink(DataSink):
    def __init__(self, service: BaseService, rollback_on_fail=True):
        super().__init__()
        self.service = service
        self.rollback_on_fail = rollback_on_fail

    def push(self, data: list[dict]):
        """
        Push data to the create() method of the provided service
        The data format is expected do be an iterable of valid service.create() inputs.
        In case of a single error the entire operation is canceled and HistoryModelServiceSink.Error is raised.
        """
        with transaction.atomic():
            for item in data:
                result = self.service.create(item)

                if not result.get("success") and self.rollback_on_fail:
                    error = result.get("detail", "Unknown error")
                    logger.error("Failed to save item: %s, data %s", error, item)
                    if self.rollback_on_fail:
                        raise self.Error(f"Failed to save item: {error}, data: {item}")
