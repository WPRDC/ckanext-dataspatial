#!/usr/bin/env python
# encoding: utf-8

import logging

from ckanext.dataspatial.lib.geofiles import load_geojson_to_datastore
from ckanext.dataspatial.lib.postgis import (
    prepare_and_populate_geoms,
)
from ckanext.dataspatial.lib.util import should_be_updated

logger = logging.getLogger(__name__)


def new_resource_listener(sender, **kwargs):
    # when a geojson file is uploaded or modified
    if sender in ["resource_create", "resource_update"]:
        resource = kwargs["data_dict"]
        if resource["format"].lower() == "geojson":
            logger.info("🗺️ Loading/updating GeoJSON in datastore.")
            load_geojson_to_datastore(resource["id"])

    # when a tabular file is pushed to the datastore
    if (
        sender in ["datapusher_hook"]
        and kwargs["data_dict"]["status"]
        and kwargs["data_dict"]["job_type"] == "push_to_datastore"
    ):
        logger.debug(
            f"\n🔴🔴{sender} 🔴🔴\n{kwargs['data_dict']}\n{kwargs['result']}\n🔵🔵🔵🔵"
        )
        resource = kwargs["data_dict"]["metadata"]
        if should_be_updated(resource):
            prepare_and_populate_geoms(resource)
