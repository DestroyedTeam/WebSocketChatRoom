from typing import Any


class DatabaseErr(Exception):
    def __init__(self, message: str = ""):
        super().__init__(f"{message}")


class NotFoundRecordsErr(DatabaseErr):
    def __init__(self, reason: Any = None):
        super().__init__(f"{f'{reason}' if reason else '.'}")


class IntegrityErr(DatabaseErr):
    def __init__(self, reason: Any = None):
        super().__init__(f"Record(s) Integrity Error{f': `{reason}`' if reason else '.'}")
