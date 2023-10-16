#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-dataspatial
# Created by the Natural History Museum in London, UK

config = {
    "query_extent": "postgis",
    "postgis.field": "_geom",
    "postgis.mercator_field": "_geom_webmercator",
    "solr.index_field": "_geom",
    "solr.latitude_field": "latitude",
    "solr.longitude_field": "longitude",
}
