from ckan.plugins.toolkit import get_validator, get_converter
from ckan.types import Schema

from ckanext.dataspatial.validators import json_object_list

boolean_validator = get_validator("boolean_validator")
isodate = get_validator("isodate")
ignore_empty = get_validator("ignore_empty")
ignore_not_sysadmin = get_validator("ignore_not_sysadmin")
resource_id_validator = get_validator("resource_id_validator")
resource_id_exists = get_validator("resource_id_exists")
default = get_validator("default")

convert_to_json_if_string = get_converter("convert_to_json_if_string")


def dataspatial_modify_resource_schema() -> Schema:
    return {
        # status
        "dataspatial_active": [boolean_validator],
        "dataspatial_last_geom_updated": [isodate, ignore_empty],
        # for preparing tabular files
        "dataspatial_longitude_field": [ignore_not_sysadmin, ignore_empty],
        "dataspatial_latitude_field": [ignore_not_sysadmin, ignore_empty],
        "dataspatial_wkt_field": [ignore_not_sysadmin, ignore_empty],
        # for preparing geojson
        "dataspatial_fields_definition": [
            ignore_not_sysadmin,
            ignore_empty,
            convert_to_json_if_string,
            json_object_list,
        ],
        # for linking non-geographic tables
        "dataspatial_geom_resource": [
            ignore_not_sysadmin,
            ignore_empty,
            resource_id_validator,
            resource_id_exists,
        ],
        "dataspatial_geom_link": [ignore_not_sysadmin, ignore_empty],
    }


def dataspatial_show_resource_schema() -> Schema:
    return {
        "dataspatial_longitude_field": [ignore_empty, default(None)],
        "dataspatial_latitude_field": [ignore_empty, default(None)],
        "dataspatial_wkt_field": [ignore_empty, default(None)],
        "dataspatial_fields_definition": [ignore_empty, default(None)],
        "dataspatial_geom_resource": [ignore_empty, default(None)],
        "dataspatial_geom_link": [ignore_empty, default(None)],
        "dataspatial_last_geom_updated": [ignore_empty, default(None)],
        "dataspatial_active": [boolean_validator, ignore_empty, default(False)],
    }
