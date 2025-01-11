import logging

from fastapi import Request, Response
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from exc.database_exc import DatabaseError, NotFoundRecordsError
from exc.http_exc import (
    BadRequestExc,
    BaseHttpExc,
    NotFoundExc,
)
from exc.service_exc import BadRequestError, NotFoundError

logger = logging.getLogger(__name__)


async def handle_exception(e: Exception, session: AsyncSession | None = None) -> None:
    if session:
        await session.rollback()

    def raise_bad_request_exception(detail: str) -> None:
        raise BadRequestExc(detail=detail)

    if isinstance(e, NotFoundError | NotFoundRecordsError):
        raise NotFoundExc(detail=str(e))
    elif isinstance(e, BadRequestError) or isinstance(e, DatabaseError):
        raise_bad_request_exception(str(e))
    elif isinstance(e, BaseHttpExc) or isinstance(e, RequestValidationError):
        logger.error(f"Error: {str(e)}")
        raise e
    else:
        logger.error(f"Error: {str(e)}")
        raise_bad_request_exception("")


async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    serialized_errors = exc.errors()
    # remove unnecessary context for avoiding incorrect json serialization
    for error in serialized_errors:
        if isinstance(error, dict):
            if not error.get("ctx"):
                continue
            del error["ctx"]

    # use exc json response format for validation error
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content=serialized_errors,
    )


async def response_validation_exception_handler(response: Response, exc: ResponseValidationError) -> JSONResponse:
    serialized_errors = exc.errors()
    # remove unnecessary context for avoiding incorrect json serialization
    for error in serialized_errors:
        if isinstance(error, dict):
            if not error.get("ctx"):
                continue
            del error["ctx"]

    # use exc json response format for validation error
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content=serialized_errors,
    )
