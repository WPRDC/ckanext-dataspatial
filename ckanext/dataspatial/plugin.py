#!/usr/bin/env python
# encoding: utf-8
from typing import cast

from ckan.common import CKANConfig
from ckan.plugins import SingletonPlugin, implements, interfaces, toolkit
from ckan.types import Schema
from ckanext.datastore.interfaces import IDatastore

from ckanext.dataspatial import cli
from ckanext.dataspatial.config import config
from ckanext.dataspatial.listeners import new_resource_listener, upserted_data_listener
from ckanext.dataspatial.logic.action import populate_geom_columns, update_geom_columns
from ckanext.dataspatial.logic.search import datastore_query_extent
from ckanext.dataspatial.validators import json_object_list


class DataSpatialPlugin(toolkit.DefaultDatasetForm, SingletonPlugin):
    """ """

    implements(interfaces.IValidators)
    implements(interfaces.IConfigurable)
    implements(interfaces.IActions)
    implements(interfaces.IClick)
    implements(interfaces.IDatasetForm)
    implements(interfaces.IConfigurer)
    implements(interfaces.ISignal)
    implements(IDatastore)

    # ISignal
    def get_signal_subscriptions(self):
        return {
            toolkit.signals.action_succeeded: [
                new_resource_listener,
            ],
            toolkit.signals.datastore_upsert: [
                upserted_data_listener,
            ],
        }

    # IValidators

    def get_validators(self):
        return {"json_object_list": json_object_list}

    # IConfigurer
    def update_config(self, config_: CKANConfig):
        toolkit.add_template_directory(config_, "templates")

    # IDatasetForm

    def _modify_package_schema(self, schema) -> Schema:
        cast(Schema, schema["resources"]).update(
            {
                # status
                "dataspatial_last_geom_updated": [
                    toolkit.get_validator("isodate"),
                    toolkit.get_validator("ignore_empty"),
                ],
                # for preparing tabular files
                "dataspatial_longitude_field": [
                    toolkit.get_validator("ignore_not_sysadmin"),
                    toolkit.get_validator("ignore_empty"),
                ],
                "dataspatial_latitude_field": [
                    toolkit.get_validator("ignore_not_sysadmin"),
                    toolkit.get_validator("ignore_empty"),
                ],
                "dataspatial_wkt_field": [
                    toolkit.get_validator("ignore_not_sysadmin"),
                    toolkit.get_validator("ignore_empty"),
                ],
                # for preparing geojson
                "dataspatial_fields_definition": [
                    toolkit.get_validator("ignore_not_sysadmin"),
                    toolkit.get_validator("ignore_empty"),
                    toolkit.get_converter("convert_to_json_if_string"),
                    toolkit.get_validator("json_object_list"),
                ],
                # for linking non-geographic tables
                "dataspatial_geom_resource": [
                    toolkit.get_validator("ignore_not_sysadmin"),
                    toolkit.get_validator("ignore_empty"),
                    toolkit.get_validator("resource_id_validator"),
                    toolkit.get_validator("resource_id_exists"),
                ],
                "dataspatial_geom_link": [
                    toolkit.get_validator("ignore_not_sysadmin"),
                    toolkit.get_validator("ignore_empty"),
                ],
            }
        )
        return schema

    def show_package_schema(self) -> Schema:
        schema = super(DataSpatialPlugin, self).show_package_schema()
        # Add our custom_text field to the dataset schema.
        cast(Schema, schema["resources"]).update(
            {
                "dataspatial_longitude_field": [
                    toolkit.get_validator("ignore_not_sysadmin"),
                    toolkit.get_validator("ignore_empty"),
                ],
                "dataspatial_latitude_field": [
                    toolkit.get_validator("ignore_not_sysadmin"),
                    toolkit.get_validator("ignore_empty"),
                ],
                "dataspatial_wkt_field": [
                    toolkit.get_validator("ignore_not_sysadmin"),
                    toolkit.get_validator("ignore_empty"),
                ],
                "dataspatial_fields_definition": [
                    toolkit.get_validator("ignore_not_sysadmin"),
                    toolkit.get_validator("ignore_empty"),
                ],
                "dataspatial_geom_resource": [
                    toolkit.get_validator("ignore_not_sysadmin"),
                    toolkit.get_validator("ignore_empty"),
                ],
                "dataspatial_geom_link": [
                    toolkit.get_validator("ignore_not_sysadmin"),
                    toolkit.get_validator("ignore_empty"),
                ],
                "dataspatial_last_geom_updated": [
                    toolkit.get_validator("ignore_not_sysadmin"),
                    toolkit.get_validator("ignore_empty"),
                ],
            }
        )

        return schema

    def create_package_schema(self) -> Schema:
        schema = super(DataSpatialPlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self) -> Schema:
        schema = super(DataSpatialPlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def is_fallback(self) -> bool:
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True

    def package_types(self) -> list[str]:
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    # IConfigurable
    def configure(self, ckan_config):
        """

        :param ckan_config:

        """
        prefix = "dataspatial."
        config_items = config.keys()
        for long_name in ckan_config:
            if not long_name.startswith(prefix):
                continue
            name = long_name[len(prefix) :]

            if name in config_items:
                config[name] = ckan_config[long_name]
            else:
                raise toolkit.ValidationError(
                    {long_name: "Unknown configuration setting"}
                )

        if config["query_extent"] not in ["postgis", "solr"]:
            raise toolkit.ValidationError(
                {"dataspatial.query_extent": "Should be either of postgis or solr"}
            )

    # IActions
    def get_actions(self):
        """ """
        return {
            "populate_geom_columns": update_geom_columns,
            "datastore_query_extent": datastore_query_extent,
        }

    # IClick
    def get_commands(self):
        return [cli.dataspatial]
