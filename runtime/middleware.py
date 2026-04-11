from runtime.utils import utc_now


class MiddlewareStack:
    def __init__(self, logger):
        self.logger = logger

    def run(self, operation_name: str, payload: dict, handler):
        correlation_id = f"{operation_name}-{utc_now()}"
        start = utc_now()
        self.logger.info("middleware.start operation=%s correlation_id=%s", operation_name, correlation_id)
        result = handler({**payload, "_correlation_id": correlation_id, "_started_at": start})
        self.logger.info("middleware.end operation=%s correlation_id=%s", operation_name, correlation_id)
        return result
