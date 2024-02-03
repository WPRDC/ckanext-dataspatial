# encoding: utf-8
import json
import logging
from typing import Any, Union, Iterable

import geojson
from ckan.logic import NotFound
from ckan.plugins import toolkit
from geomet import wkt

from ckanext.dataspatial.lib.constants import WKT_FIELD_NAME
from ckanext.dataspatial.lib.postgis import (
    prepare_and_populate_geoms,
)
from ckanext.dataspatial.lib.util import (
    get_resource_file_path,
    DEFAULT_CONTEXT,
)
from ckanext.dataspatial.lib.types import StatusCallback, GeoreferenceStatus

logger = logging.getLogger(__name__)


def validate_sub_geoms(geom_type, sub_geom_type, coords):
    """
    Validates set of geometries returning only the valid ones
    """
    valid_sub_geoms = []
    for sub_coords in coords:
        sub_geom = sub_geom_type(sub_coords)
        if sub_geom.is_valid:
            valid_sub_geoms.append(sub_geom)

    if valid_sub_geoms:
        return geom_type(coords)
    return None


def validate_geojson_geom(geojson_geo: dict) -> dict | None:
    """Validates a GeoJSON geometry.
    Returns the geometry if valid, otherwise returns None
    """
    geo_type = geojson_geo.get("type").lower()

    # load geom into geojson library geometry
    data = None
    coords = geojson_geo.get("coordinates")
    if geo_type == "point":
        data = geojson.Point(coords)
    elif geo_type == "linestring":
        data = geojson.LineString(coords)
    elif geo_type == "polygon":
        data = geojson.Polygon(coords)

    # for collections, build them from validated child geoms
    elif geo_type == "multipoint":
        data = validate_sub_geoms(geojson.MultiPoint, geojson.Point, coords)
    elif geo_type == "multilinestring":
        data = validate_sub_geoms(geojson.MultiLineString, geojson.LineString, coords)
    elif geo_type == "multipolygon":
        data = validate_sub_geoms(geojson.MultiPolygon, geojson.Polygon, coords)

    if data and data.is_valid:
        return data
    return None


def geojson2wkt(geojson_geo: dict) -> str | None:
    geo_data = validate_geojson_geom(geojson_geo)
    try:
        if geo_data:
            return wkt.dumps(geo_data, decimals=7)
        else:
            return None
    except Exception as e:
        logger.warning(e)
        return None


def to_row(feature: dict, fields: Iterable[dict]) -> dict:
    row = {}
    # transfer available fields
    for field in fields:
        row[field] = feature["properties"].get(field, None)
    wkt_value = geojson2wkt(feature["geometry"])
    row[WKT_FIELD_NAME] = wkt_value

    return row


def load_geojson_to_datastore(
    resource_id: str,
    aliases: Union[list[str], str] = None,
    indexes: list[str] = None,
    status_callback: StatusCallback = lambda d: None,
):
    """Converts geojson to tabular format and loads in to the datastore"""
    resource: dict = toolkit.get_action("resource_show")(
        DEFAULT_CONTEXT, {"id": resource_id}
    )
    if not resource or not resource["id"]:
        toolkit.ValidationError("Resource not found.")

    if resource["format"].lower() != "geojson":
        toolkit.ValidationError("Only GeoJSON is supported at the moment.")

    # load geojson data and convert to list of dicts
    with open(get_resource_file_path(resource_id)) as f:
        geojson: dict = json.load(f)

    #   find the full set of keys
    fields = set()
    for feature in geojson["features"]:
        fields |= set(feature["properties"].keys())

    rows: list[dict[str, Any]] = [
        to_row(feature, fields)
        for feature in geojson["features"]
        if feature["geometry"]
    ]

    # get datastore_create options
    try:
        fields = resource["dataspatial_fields_definition"]
    except KeyError:
        fields = None

    # ensure metadata lists the correct WKT field name
    if (
        not resource.get("dataspatial_wkt_field", False)
        or resource.get("dataspatial_wkt_field") != WKT_FIELD_NAME
    ):
        toolkit.get_action("resource_patch")(
            DEFAULT_CONTEXT,
            {"id": resource_id, "dataspatial_wkt_field": WKT_FIELD_NAME},
        )

    create_options: dict = {
        "resource_id": resource_id,
        "aliases": aliases,
        "records": rows,
        "fields": fields or [{"id": k, "type": "text"} for k in rows[0].keys()],
        "force": True,
    }
    if indexes:
        create_options["indexes"] = indexes

    # delete datastore table if it exists
    try:
        toolkit.get_action("datastore_info")(DEFAULT_CONTEXT, {"id": resource_id})
        logger.info(f"DELETING {resource_id}")
        toolkit.get_action("datastore_delete")(
            DEFAULT_CONTEXT, {"resource_id": resource_id, "force": True}
        )
    except NotFound:
        pass

    # create table in datastore
    logger.info(f"Creating datastore table for {resource_id}")
    status_callback(
        GeoreferenceStatus.WORKING,
        value={"notes": f"Creating datastore table for {resource_id}"},
    )
    toolkit.get_action("datastore_create")({"user": "default"}, create_options)

    # now that this has a datastore table with a WKT field, run it through the common process
    prepare_and_populate_geoms(
        resource,
        from_geojson_add=True,
        status_callback=status_callback,
    )
