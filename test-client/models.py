"""Pydantic models for the KV Store Test Client."""
from pydantic import BaseModel


class TestDetails(BaseModel):
    """Details about test execution results."""
    steps_executed: int
    all_assertions_passed: bool


class TestResponse(BaseModel):
    """Standard test response format for successful tests."""
    success: bool
    test_name: str
    details: TestDetails


class TestErrorResponse(BaseModel):
    """Standard test response format for failed tests."""
    success: bool
    test_name: str
    error: str
    step: str