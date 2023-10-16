#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-dataspatial
# Created by the Natural History Museum in London, UK

import re

from ckan.plugins import SingletonPlugin, implements, interfaces, toolkit
from ckanext.datastore.interfaces import IDatastore

from ckanext.dataspatial.config import config
from ckanext.dataspatial.logic.action import create_geom_columns, update_geom_columns
from ckanext.dataspatial.logic.search import datastore_query_extent

try:
    from ckanext.datasolr.interfaces import IDataSolr
except ImportError:
    pass


class DataSpatialPlugin(SingletonPlugin):
    """ """

    implements(interfaces.IConfigurable)
    implements(interfaces.IActions)
    implements(IDatastore)
    try:
        implements(IDataSolr)
    except NameError:
        pass

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
            "create_geom_columns": create_geom_columns,
            "update_geom_columns": update_geom_columns,
            "datastore_query_extent": datastore_query_extent,
        }

    # IDatastore
    def datastore_validate(self, context, data_dict, all_field_ids):
        """

        :param context:
        :param data_dict:
        :param all_field_ids:

        """
        # Validate geom fields
        if "fields" in data_dict:
            geom_fields = [config["postgis.field"], config["postgis.mercator_field"]]
            data_dict["fields"] = [
                f for f in data_dict["fields"] if f not in geom_fields
            ]
        # Validate geom filters
        try:
            # We'll just check that this *looks* like a WKT, in which case we will trust
            # it's valid. Worst case the query will fail, which is handled gracefully
            # anyway.
            for i, v in enumerate(data_dict["filters"]["_tmgeom"]):
                if re.search("^\s*(POLYGON|MULTIPOLYGON)\s*\([-+0-9,(). ]+\)\s*$", v):
                    del data_dict["filters"]["_tmgeom"][i]
            if len(data_dict["filters"]["_tmgeom"]) == 0:
                del data_dict["filters"]["_tmgeom"]
        except KeyError:
            pass
        except TypeError:
            pass

        return data_dict

    def datastore_search(self, context, data_dict, all_field_ids, query_dict):
        """

        :param context:
        :param data_dict:
        :param all_field_ids:
        :param query_dict:

        """
        try:
            tmgeom = data_dict["filters"]["_tmgeom"]
        except KeyError:
            return query_dict

        clauses = []
        field_name = config["postgis.field"]
        for geom in tmgeom:
            clauses.append(
                (
                    'ST_Intersects("{field}", ST_GeomFromText(%s, 4326))'.format(
                        field=field_name
                    ),
                    geom,
                )
            )

        query_dict["where"] += clauses
        return query_dict

    def datastore_delete(self, context, data_dict, all_field_ids, query_dict):
        """

        :param context:
        :param data_dict:
        :param all_field_ids:
        :param query_dict:

        """
        return query_dict

    ## IDataSolr
    def datasolr_validate(self, context, data_dict, fields_types):
        """

        :param context:
        :param data_dict:
        :param fields_types:

        """
        return self.datastore_validate(context, data_dict, fields_types)

    def datasolr_search(self, context, data_dict, fields_types, query_dict):
        """

        :param context:
        :param data_dict:
        :param fields_types:
        :param query_dict:

        """

        # FIXME: Remove _tmgeom search
        if "filters" in query_dict and query_dict["filters"]:
            query_dict["filters"].pop("_tmgeom", None)

        return query_dict
