from enum import auto


class SynchronizationErrorType:
    CONNECTION_LOST = auto()
    UNKNOWN = auto()


class SynchronizationError(Exception):
    """
    Custom error if a model cannot be initialized.
    """

    def __init__(self, message: str, error_type: SynchronizationErrorType):
        super().__init__(f"{error_type}: {message}")
        self.error_type = error_type
        self.message = message
