from fastapi import HTTPException


class BaseHttpExc(HTTPException):
    def __init__(self, status_code: int, detail: str | dict):
        super().__init__(status_code=status_code, detail=detail)


class BadRequestExc(BaseHttpExc):
    def __init__(self, detail: str | dict):
        super().__init__(status_code=400, detail=detail)


class NotFoundExc(BaseHttpExc):
    def __init__(self, detail: str | dict):
        super().__init__(status_code=404, detail=detail)
