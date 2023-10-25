#!/usr/bin/env python
# encoding: utf-8
import json
from pathlib import Path
from typing import Any, Literal

from ckan.logic import NotFound
from ckan.plugins import toolkit
from geomet import wkt

from ckanext.dataspatial.lib.postgis import (
    create_postgis_index,
    create_postgis_columns,
    populate_postgis_columns,
    prepare_and_populate_geoms,
)
from ckanext.dataspatial.lib.util import get_resource_file_path

WKT_FIELD_NAME = "_dataspatial_wkt"

DEFAULT_CONTEXT = {"user": "default"}


def load_geojson_to_datastore(
    resource_id: str,
    aliases: list[str] | str = None,
    indexes: list[str] = None,
):
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

    rows: list[dict[str, Any]] = [
        {**row["properties"], WKT_FIELD_NAME: wkt.dumps(row["geometry"])}
        for row in geojson["features"]
    ]

    # get datastore_create options
    try:
        fields = resource["dataspatial_fields_definition"]
    except KeyError:
        fields = None

    # ensure metadata lists the correct WKT field name
    if (
        not resource["dataspatial_wkt_field"]
        or resource["dataspatial_wkt_field"] != WKT_FIELD_NAME
    ):
        toolkit.get_action("resource_patch")(
            DEFAULT_CONTEXT,
            {"resource_id": resource_id, "dataspatial_wkt_field": WKT_FIELD_NAME},
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
        toolkit.get_action("datastore_delete")(
            DEFAULT_CONTEXT, {"id": resource_id, "force": True}
        )
    except NotFound:
        pass

    # create table in datastore
    toolkit.get_action("datastore_create")({"user": "default"}, create_options)

    # now that this has a datastore table with a WKT field, run it through the common process
    prepare_and_populate_geoms(resource)