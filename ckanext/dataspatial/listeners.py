# encoding: utf-8

import logging

from ckan.plugins import toolkit

from ckanext.dataspatial.lib.geofiles import load_geojson_to_datastore
from ckanext.dataspatial.lib.postgis import (
    prepare_and_populate_geoms,
)
from ckanext.dataspatial.lib.util import should_be_updated, DEFAULT_CONTEXT

logger = logging.getLogger(__name__)


def new_resource_listener(sender, **kwargs):
    # when a geojson file is uploaded or modified
    if sender in ["resource_create"]:
        resource = kwargs["result"]
        if resource["format"].lower() == "geojson":
            logger.info("Loading/updating GeoJSON in datastore.")
            load_geojson_to_datastore(resource["id"])

    # when a tabular file is pushed to the datastore
    if (
        sender in ["datapusher_hook"]
        and kwargs["data_dict"]["status"] == "complete"
        and kwargs["data_dict"]["job_type"] == "push_to_datastore"
    ):
        resource_id = kwargs["data_dict"]["metadata"]["resource_id"]
        logger.info(f"Resource {resource_id} pushed to datastore.")
        resource = toolkit.get_action("resource_show")(
            DEFAULT_CONTEXT, {"id": resource_id}
        )
        if should_be_updated(resource):
            logger.info(f"Resource {resource_id} being geocoded...")
            prepare_and_populate_geoms(resource)
        else:
            logger.info(f"Resource {resource_id} not being updated.")
