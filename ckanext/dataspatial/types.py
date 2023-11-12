# encoding: utf-8
# Types and Constants used throughout extension.
from typing import Callable, TypedDict, Optional
from enum import Enum

GEOMETRY_TYPES = {
    "POINT",
    "LINESTRING",
    "POLYGON",
    "MULTIPOINT",
    "MULTILINESTRING",
    "MULTIPOLYGON",
}


class GeoreferenceStatus(Enum):
    COMPLETE = "COMPLETE"
    WORKING = "WORKING"
    PENDING = "PENDING"
    SUBMITTING = "SUBMITTING"
    ERROR = "ERROR"


StatusCallback = Callable[[str, str | None, str | None], None]

SpecificStatusCallback = Callable[[str | None, str | None], None]


class HookDataDict(TypedDict):
    resource_id: str
    status: str
    job_created: str
    value: dict | None
    error: str | None


class StatusResult(TypedDict):
    job_id: str
    status: str
    last_updated: str
    rows_completed: int | None
    notes: str | None
