"""Shared schema primitives."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ProvenanceMixin(BaseModel):
    data_provenance: str = Field(
        default="demo",
        description="Origin of the data: demo | verified | estimate",
    )


class HealthResponse(BaseModel):
    status: str
    app: str
    app_env: str = "development"
    demo_mode: bool
    policy_as_of: str | None = None
    schema_version: str | None = None
    mcp_endpoint: str = "/mcp"


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    code: str | None = None
