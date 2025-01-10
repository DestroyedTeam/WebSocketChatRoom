from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware
from util.logger import init_logger

init_logger()


def register_router(_app: FastAPI):
    from core import api_router, page_router
    _app.include_router(page_router.router)
    _app.include_router(api_router.router, prefix="/api")


def add_custom_exception_handlers(_app: FastAPI):
    from util.exception_util import request_validation_exception_handler, response_validation_exception_handler
    _app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    _app.add_exception_handler(ResponseValidationError, response_validation_exception_handler)


def create_app(span) -> FastAPI:
    _app = FastAPI(lifespan=span)
    register_router(_app)
    add_custom_exception_handlers(_app)
    return _app


@asynccontextmanager
async def lifespan(application: FastAPI): # noqa
    from base.connector import database_connector
    """
    Use context manager to manage the lifespan of the application instead of using the startup and shutdown events.
    """
    yield
    await database_connector.engine.dispose()


app = create_app(lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5555, reload=True, workers=8)
