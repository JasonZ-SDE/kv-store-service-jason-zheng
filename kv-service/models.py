"""Pydantic models and custom exceptions for the KV Store Service."""
from fastapi import HTTPException, status
from pydantic import BaseModel, Field, field_validator
import json
from typing import Any


class ValueModel(BaseModel):
    """Model for key-value pair requests with JSON validation."""
    key: str
    value: Any = Field(
        ..., 
        description="JSON-serializable value (string, number, boolean, null, object, or array)"
    )
    
    @field_validator('value')
    @classmethod
    def validate_json_serializable(cls, v):
        """Ensure the value is JSON serializable"""
        try:
            json.dumps(v)
            return v
        except (TypeError, ValueError) as e:
            raise ValueError(f"Value must be JSON serializable: {e}")


class ErrorResponse(BaseModel):
    """Standard error response format."""
    success: bool = False
    error: str


class KeyNotFoundError(HTTPException):
    """Exception raised when a key is not found in storage."""
    def __init__(self, key: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": f"Key '{key}' not found"}
        )


class KeyMismatchError(HTTPException):
    """Exception raised when path key doesn't match body key."""
    def __init__(self, path_key: str, body_key: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": f"Key in path '{path_key}' does not match key in body '{body_key}'"}
        )


class ValidationError(HTTPException):
    """Exception raised for validation errors."""
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"success": False, "error": f"Validation error: {message}"}
        )


class InternalServerError(HTTPException):
    """Exception raised for internal server errors."""
    def __init__(self, message: str = "Internal server error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": message}
        )