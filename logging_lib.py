import logging.config
import sys
import logging
from typing import Callable, Optional
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


logging_config = {
    "version":1,
    "formatters":{
        "detailed":{
            "class": "logging.Formatter",
            "format": (
                '%(asctime)s|%(process)s|%(levelname)s|%(name)s'
                '|%(module)s|%(funcName)s|%(lineno)s: %(message)s'
            ),
            "datefmt": '%Y-%m-%d %H:%M:%S %z'
        },
        "json":{
            "class":"pythonjsonlogger.jsonlogger.JsonFormatter",
            "format":"%(asctime)s %(process)s %(levelname)s %(name)s %(module)s %(funcName)s %(lineno)s"
        }
    },
    "handlers":{
        "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "detailed",
                "stream": sys.stderr,
            }
    },
    "root":{
        "level":"DEBUG",
        "handlers":[
            "console"
        ],
    "propagate": True
    }
}

logger = logging.config.dictConfig(logging_config)


class RouterLoggingMiddleware(BaseHTTPMiddleware):
    """
    Ref: https://www.starlette.io/middleware/#basehttpmiddleware
    """
    def __init__(
            self,
            app: FastAPI,
            *,
            logger: Optional[logging.Logger] = None
    ) -> None:
        self._logger = logger if logger else logging.getLogger(__name__)
        super().__init__(app)

    async def dispatch(self,
                       request: Request,
                       call_next: Callable
    ) -> Response:
        response: Response = await call_next(request)

        logging_dict = dict()
        logging_dict["request"] = {
            "method": request.method,
            "path": request.url.path,
            "ip": request.client.host
        }
        logging_dict["response"] = {
            "status": "successful" if response.status_code < 400 else "failed",
            "status_code": response.status_code,
        }
        self._logger.info(logging_dict)

        return response
