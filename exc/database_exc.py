from typing import Any


class DatabaseError(Exception):
    def __init__(self, message: str = ""):
        super().__init__(f"{message}")


class NotFoundRecordsError(DatabaseError):
    def __init__(self, reason: Any = None):
        super().__init__(f"{f'{reason}' if reason else '.'}")


class IntegrityError(DatabaseError):
    def __init__(self, reason: Any = None):
        super().__init__(f"Record(s) Integrity Error{f': `{reason}`' if reason else '.'}")
