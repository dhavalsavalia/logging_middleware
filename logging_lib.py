import logging.config
import sys
import time
import logging
import json
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
        response, response_dict = await self._log_response(
            call_next,
            request
        )

        logging_dict = dict()
        logging_dict["request"] = await self._log_request(request)
        logging_dict["response"] = response_dict
        self._logger.info(logging_dict)

        return response
    
    async def _log_request(
            self,
            request: Request
    ) -> str:
        """Logs request part
            Arguments:
           - request: Request

        """

        print("Laaaaaaa")

        path = request.url.path
        if request.query_params:
            path += f"?{request.query_params}"

        request_logging = {
            "method": request.method,
            "path": path,
            "ip": request.client.host
        }

        try:
            body = await request.json()
            request_logging ["body"] = body
        except:
            body = None

        return request_logging
    
    async def _log_response(
        self,
        call_next: Callable,
        request: Request
    ) -> Response:
        """Logs response part
        Arguments:
            - call_next: Callable (To execute the actual path function and get response back)
            - request: Request
        Returns:
            - response: Response
            - response_logging: str
        """

        start_time = time.perf_counter()
        response = await self._execute_request(call_next, request)
        finish_time = time.perf_counter()

        overall_status = "successful" if response.status_code < 400 else "failed"
        execution_time = finish_time - start_time

        response_logging = {
            "status": overall_status,
            "status_code": response.status_code,
            "time_taken": f"{execution_time:0.4f}s"
        }

        resp_body = [section async for section in response.__dict__["body_iterator"]]

        try:
            resp_body = json.loads(resp_body[0].decode())
        except:
            resp_body = str(resp_body)

        response_logging["body"] = resp_body

        return response, response_logging

    async def _execute_request(self,
                               call_next: Callable,
                               request: Request
    ) -> Response:
        """Executes the actual path function using call_next.

               Arguments:
               - call_next: Callable (To execute the actual path function
                            and get response back)
               - request: Request
               Returns:
               - response: Response
        """
        try:
            response: Response = await call_next(request)

            return response

        except Exception as e:
            self._logger.exception(
                {
                    "path": request.url.path,
                    "method": request.method,
                    "reason": e
                }
            )


