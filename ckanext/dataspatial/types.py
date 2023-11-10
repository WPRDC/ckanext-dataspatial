# encoding: utf-8
# Types and Constants used throughout extension.
from typing import Callable

GEOMETRY_TYPES = {
    "POINT",
    "LINESTRING",
    "POLYGON",
    "MULTIPOINT",
    "MULTILINESTRING",
    "MULTIPOLYGON",
}

JOB_COMPLETION_STATUS = "Completed"


StatusCallback = Callable[[str], None]
