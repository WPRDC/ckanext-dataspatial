#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-dataspatial
# Created by the Natural History Museum in London, UK
from typing import Optional, Callable

from ckan.plugins import toolkit
from ckan.types import DataDict
from ckanext.datastore import backend as datastore_db
from ckanext.datastore.helpers import is_single_statement

from ckanext.dataspatial.config import config
from ckanext.dataspatial.db import (
    create_geom_column,
    create_index,
    fields_exist,
    get_connection,
    index_exists,
    invoke_search_plugins,
    Connection,
)

GEOM_MERCATOR_FIELD: str = config["postgis.mercator_field"]
GEOM_FIELD: str = config["postgis.field"]


def has_postgis_columns(
    resource_id: str,
    connection: Optional[Connection] = None,
) -> bool:
    """Returns TRUE if the given resource already has postgis columns

    The name of the columns is read from the configuration.

    :param resource_id: Resource to test
    :param connection: Database connection. If None, one will be
        created for this operation. (Default value = None)
    :returns: s: True if the resource database table already has postgis
              columns, False otherwise.

    """
    with get_connection(connection) as c:
        return fields_exist(c, resource_id, [GEOM_FIELD, GEOM_MERCATOR_FIELD])


def has_postgis_index(resource_id: str, connection: Optional[Connection] = None):
    """Returns TRUE if the given resource already has an index on postgis columns

    :param resource_id: The resource to test
    :param connection: Database connection. If None, one will be
        created for this operation. (Default value = None)
    :returns: s: True if the resource database already has the index for the
              postgis columns
    """
    with get_connection(connection) as c:
        return (
            has_postgis_columns(resource_id, c)
            and index_exists(c, resource_id, GEOM_FIELD)
            and index_exists(c, resource_id, GEOM_MERCATOR_FIELD)
        )


def create_postgis_columns(
    resource_id: str, geom_type: str, connection: Optional[Connection] = None
):
    """Create the PostGIS columns

    The column names are read from the configuration

    :param resource_id: The resource id to create the columns on
    :param geom_type: The type of geometry being created.
    :param connection: Database connection. If None, one will be
        created for this operation. (Default value = None)

    """
    c: Connection
    with get_connection(connection, write=True) as c:
        create_geom_column(c, resource_id, GEOM_FIELD, 4326, geom_type)
        create_geom_column(c, resource_id, GEOM_MERCATOR_FIELD, 3857, geom_type)


def create_postgis_index(resource_id: str, connection: Optional[Connection] = None):
    """Create geospatial index

    The column name to create the index on is read from the configuration

    :param resource_id: The resource to create the index on
    :param connection: Database connection. If None, one will be
        created for this operation. (Default value = None)
    """
    c: Connection
    with get_connection(connection, write=True) as c:
        if not has_postgis_index(resource_id, c):
            create_index(c, resource_id, GEOM_FIELD)
            create_index(c, resource_id, GEOM_MERCATOR_FIELD)


def _populate_columns_with_lat_lng(
    resource_id: str,
    lat_field: str,
    lng_field: str,
    progress: Callable[[int], None] = None,
    connection=None,
):
    with get_connection(connection, write=True, raw=True) as c:
        # This is timing out for big datasets (KE EMu), so we're going to break into a
        #  batch operation
        # We need two cursors, one for reading; one for writing
        # And the write cursor will be committed every x number of times (
        # incremental_commit_size)
        read_cursor = c.cursor()
        write_cursor = c.cursor()

        # Retrieve all IDs of records that require updating
        # Either: lat/lng field doesn't match that in the geom column
        # OR geom is  null and /lat/lon is populated
        read_sql = f"""
            SELECT _id
            FROM "{resource_id}"
            WHERE "{lat_field}" <= 90
              AND "{lat_field}" >= -90
              AND "{lng_field}" <= 180
              AND "{lng_field}" >= -180
              AND ("{GEOM_FIELD}" IS NULL
                AND (("{lat_field}" IS NOT NULL OR ST_Y("{GEOM_FIELD}") <> "{lat_field}") OR
                     ("{lng_field}" IS NOT NULL OR ST_X("{GEOM_FIELD}") <> "{lng_field}"))
                )
            """

        read_cursor.execute(read_sql)

        count = 0
        incremental_commit_size = 1000

        update_sql = f"""
            UPDATE "{resource_id}"
            SET "{GEOM_FIELD}" = st_setsrid(st_makepoint("{lng_field}"::float8, 
            "{lat_field}"::float8), 4326),
              "{GEOM_MERCATOR_FIELD}" = st_transform(st_setsrid(st_makepoint("{lng_field}"::float8, "{lat_field}"::float8), 4326), 3857)
              WHERE _id = %s
         """

        # todo: move all this work to postgres or at least do more than one row per query
        while True:
            output = read_cursor.fetchmany(incremental_commit_size)
            if not output:
                break

            for row in output:
                count += 1
                write_cursor.execute(update_sql, ([row[0]]))

            # commit, invoked every incremental commit size
            c.commit()
            if progress:
                progress(count)

        c.commit()


def _populate_columns_with_wkt(
    resource_id: str,
    wkt_field: str = None,
    progress: Callable[[int], None] = None,
    connection=None,
):
    with get_connection(connection, write=True, raw=True) as c:
        update_query = f"""
            UPDATE "{resource_id}"
            SET "{GEOM_FIELD}"          = st_geomfromtext("{wkt_field}", 4326),
                "{GEOM_MERCATOR_FIELD}" = st_transform(st_geomfromtext("{wkt_field}", 4326), 3857)
        """
        c.cursor().execute(update_query)


def populate_postgis_columns(
    resource_id: str,
    lat_field: str = None,
    lng_field: str = None,
    wkt_field: str = None,
    progress: Callable[[int], None] = None,
    connection: Optional[Connection] = None,
):
    """Populate the PostGis columns from the give lat & long fields

    :param resource_id: The resource to populate
    :param lat_field: The latitude field to populate from
    :param lng_field: The longitude field to populate from
    :param wkt_field: The Well-Known Text field to populate from
    :param progress: Optionally, a callable invoked at regular interval with
        the number of rows that were updated (Default value = None)
    :param connection: Database connection. If None, one will be
        created for this operation. (Default value = None)
    """
    if lat_field and lng_field:
        _populate_columns_with_lat_lng(
            resource_id, lat_field, lng_field, progress=progress, connection=connection
        )
    elif wkt_field:
        _populate_columns_with_wkt(
            resource_id, wkt_field, progress=progress, connection=connection
        )


def query_extent(data_dict: DataDict, connection: Optional[Connection] = None):
    """Return the spatial query extent of a datastore search

    :param data_dict: Dictionary defining the search
    :param connection:  (Default value = None)
    :returns: s a dictionary defining:
        {
            total_count: The total number of rows in the query,
            geom_count: The number of rows that have a geom,
            bounds: ((lat min, long min), (lat max, long max)) for the
                  queries rows
        }
    """
    r = toolkit.get_action("datastore_search")({}, data_dict)

    if "total" not in r or r["total"] == 0:
        return {"total_count": 0, "geom_count": 0, "bounds": None}

    result = {"total_count": r["total"], "bounds": None}

    field_types = dict([(f["id"], f["type"]) for f in r["fields"]])
    field_types["_id"] = "int"

    # Call plugin to obtain correct where statement
    (ts_query, where_clause, values) = invoke_search_plugins(data_dict, field_types)
    # Prepare and run our query
    query = """
        SELECT COUNT(r) AS count,
               ST_YMIN(ST_EXTENT(r)) AS ymin,
               ST_XMIN(ST_EXTENT(r)) AS xmin,
               ST_YMAX(ST_EXTENT(r)) AS ymax,
               ST_XMAX(ST_EXTENT(r)) AS xmax
        FROM   (
          SELECT "{geom_field}" AS r
          FROM   "{resource_id}" {ts_query}
          {where_clause}
        ) _tilemap_sub
    """.format(
        geom_field=config["postgis.field"],
        resource_id=data_dict["resource_id"],
        where_clause=where_clause,
        ts_query=ts_query,
    )

    if not is_single_statement(query):
        raise datastore_db.ValidationError(
            {"query": ["Query is not a single statement."]}
        )

    with get_connection(connection) as c:
        query_result = c.execute(query, values)
        r = query_result.fetchone()

    result["geom_count"] = r["count"]
    if result["geom_count"] > 0:
        result["bounds"] = ((r["ymin"], r["xmin"]), (r["ymax"], r["xmax"]))
    return result
