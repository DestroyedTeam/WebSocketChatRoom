from builtins import Exception


class ServiceErr(Exception):
    def __init__(self, message: str | dict = ""):
        super().__init__(message)


class BadRequestErr(ServiceErr):
    def __init__(self, message: str | dict = ""):
        super().__init__(message)


class NotFoundErr(ServiceErr):
    def __init__(self, message: str | dict = ""):
        super().__init__(message)
