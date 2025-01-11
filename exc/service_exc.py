from builtins import Exception


class ServiceError(Exception):
    def __init__(self, message: str | dict = ""):
        super().__init__(message)


class BadRequestError(ServiceError):
    def __init__(self, message: str | dict = ""):
        super().__init__(message)


class NotFoundError(ServiceError):
    def __init__(self, message: str | dict = ""):
        super().__init__(message)
