""" Defines the strucuture of all error types"""

from enum import Enum

class ErrorTypes(str, Enum):
    """List of all possible error types in format reason/issue"""
    BUSSINESS = "bussiness"
    NOT_VALID = "invalid"
    TWILIO = "twilio"

class CustomError(Exception):
    """Custom exception with an error type."""
    def __init__(self, message, error_type: ErrorTypes):
        self.message = message
        self.error_type = error_type
        super().__init__(f"{error_type}: {message}")
