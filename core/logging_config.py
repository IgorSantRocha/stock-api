import logging
import sys
import json
from pythonjsonlogger import jsonlogger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time


def setup_logging():
    logger = logging.getLogger()
    logHandler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)
    logger.setLevel(logging.INFO)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger = logging.getLogger("http")
        start_time = time.time()

        response = await call_next(request)
        duration = time.time() - start_time

        logger.info("Request",
                    extra={
                        "method": request.method,
                        "url": request.url.path,
                        "status": response.status_code,
                        "duration_ms": round(duration * 1000)
                    })

        return response


'''
import logging

logger = logging.getLogger("webhook")

logger.info("Webhook recebido", extra={"order": payload.content.order_number})
logger.warning("Evento ignorado", extra={"event": "DUPLICATE"})
logger.error("Erro inesperado", exc_info=True)
'''
