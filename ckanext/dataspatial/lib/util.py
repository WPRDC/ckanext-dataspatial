#!/usr/bin/env python
# encoding: utf-8
from pathlib import Path

from ckan.plugins import toolkit
from geomet import wkt

STORAGE_PATH = Path(toolkit.config.get("ckan.storage_path"))

DEFAULT_CONTEXT = {"user": "default"}

WKT_FIELD_NAME = "dataspatial_wkt"


def get_common_geom_type(wkt_values: list[str]) -> str:
    """Finds the cdommon geometry type from a list of WKT geometries.

    If only one type is present, it is returned.

    When a single type and its collection type are present, the collection type
        is returned as it supports both.
        (e.g. if "Point" and "Multipoint" are present, it returns "MULTIPOINT")

    If incompatible types are present, "GEOMETRYCOLLECTION" is returned.

    :returns: the common geometry type name in all caps
    """
    geom_types = list(
        set([wkt.loads(wkt_value)["type"].upper() for wkt_value in wkt_values])
    )
    if not geom_types:
        raise TypeError("At least one WKT value must be provided.")
    if len(geom_types) == 1:
        return geom_types[0]
    if len(geom_types) > 2:
        return "GEOMETRYCOLLECTION"

    ordered_types: list[str] = sorted(geom_types, key=lambda x: len(x))
    if ordered_types[0] in ordered_types[1]:
        return ordered_types[1].upper()
    return "GEOMETRYCOLLECTION"


def get_resource_file_path(resource_id: str) -> Path:
    return (
        STORAGE_PATH
        / "resources"
        / resource_id[:3]
        / resource_id[3:6]
        / resource_id[6:]
    )


def should_be_updated(resource: dict):
    return can_be_spatial(resource) and out_of_sync(resource)


def can_be_spatial(resource: dict):
    return resource["datastore_active"] and _has_necessary_metadata(resource)


def out_of_sync(resource: dict):
    return (
        not resource.get("dataspatial_last_geom_updated")
        or resource.get("dataspatial_last_geom_updated") < resource.get("last_modified")
        or resource.get("dataspatial_last_geom_updated")
        < resource.get("metadata_modified")
    )


def _has_necessary_metadata(resource: dict):
    return (
        resource["dataspatial_latitude_field"]
        and resource["dataspatial_longitude_field"]
    ) or resource["dataspatial_wkt_field"]
