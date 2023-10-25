#!/usr/bin/env python
# encoding: utf-8
from ckan.plugins import toolkit
from ckan.types import Context, DataDict

from ckanext.dataspatial.lib.postgis import prepare_and_populate_geoms


def populate_geom_columns(context: Context, data_dict: DataDict):
    """Add geom column to the given resource, and optionally populate them.

    Either latitude_field and longitude_field or wkt_field parameters are required unless they are
        already stored in the resource's metadata.

    Providing these will update the resource's metadata.

    :param context: Current context
    :param data_dict: Parameters:
      - resource_id: The resource for which to create geom columns; REQUIRED
      - latitude_field: The existing latitude field in the column.
      - longitude_field: The existing longitude field in the column,
      - wkt_field: The existing wkt field in the column
    """
    try:
        resource_id = data_dict["resource_id"]
    except KeyError:
        raise toolkit.ValidationError({"resource_id": "A Resource id is required"})

    # update metadata if field arguments are passed
    resource = toolkit.get_action("resource_show")(context, {"id": resource_id})

    lat_field = resource.get("dataspatial_latitude_field")
    lng_field = resource.get("dataspatial_longitude_field")
    wkt_field = resource.get("dataspatial_wkt_field")

    arg_lat_field = data_dict.get("latitude_field")
    arg_lng_field = data_dict.get("longitude_field")
    arg_wkt_field = data_dict.get("wkt_field")

    patch_dict = {}
    if arg_lat_field and arg_lat_field != lat_field:
        patch_dict["dataspatial_latitude_field"] = arg_lat_field
    if arg_lng_field and arg_lng_field != lng_field:
        patch_dict["dataspatial_longitude_field"] = arg_lng_field
    if arg_wkt_field and arg_wkt_field != wkt_field:
        patch_dict["dataspatial_wkt_field"] = arg_wkt_field

    # if fields are provided, update metadata with them
    resource = toolkit.get_action("resource_patch")(context, patch_dict)

    # ensure the resource has the minimum metadata
    lat_field = resource.get("dataspatial_latitude_field")
    lng_field = resource.get("dataspatial_longitude_field")
    wkt_field = resource.get("dataspatial_wkt_field")
    if not (lat_field and lng_field) and not wkt_field:
        raise toolkit.ValidationError(
            "Missing required source column(s). Provide lat/lng fieldnames or a wkt field name."
        )

    # prepare and populate the columns
    prepare_and_populate_geoms(resource)
