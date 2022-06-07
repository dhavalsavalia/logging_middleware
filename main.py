from fastapi import FastAPI
from logging_lib import RouterLoggingMiddleware, logger


def get_application() -> FastAPI:
    application = FastAPI(title="FastAPI Logging", debug=True)

    application.add_middleware(
        RouterLoggingMiddleware, logger=logger
    )
    return application


app = get_application()