[![CKAN](https://img.shields.io/badge/ckan-2.10.1-orange.svg?style=flat-square)](https://github.com/ckan/ckan)
# ckanext-dataspatial
_A CKAN extension that provides geospatial awareness of datastore data._

<img src=".github/wprdc-mark-light.png#gh-light-mode-only" height="50px" alt="WPRDC Logo"/>
<img src=".github/wprdc-mark-dark.png#gh-dark-mode-only" height="50px" alt="WPRDC Logo"/>


__A product of the [Western Pennsylvania Regional Data Center](https://www.wprdc.org).__

[Built upon the work fo the Natural History Museum in London.](#acknowledgements)

## Overview
This extension provides geospatial awareness of datastore data. This includes:

- Geospatial searches within datasets;
- Spatial extent of datastore searches;
- Pushing GeoJSON data (properties and geometries) in to the datastore.
- Support for [PostGIS](http://postgis.net);
- Support for tile servers that inject PostGIS data. (e.g. [martin](https://github.com/maplibre/martin))

## Installation
Path variables used below:
- `$INSTALL_FOLDER` (i.e. where CKAN is installed), e.g. `/usr/lib/ckan/default`
- `$CONFIG_FILE`, e.g. `/etc/ckan/default/development.ini`

1. Clone the repository into the `src` folder:

  ```bash
  cd $INSTALL_FOLDER/src
  git clone https://github.com/NaturalHistoryMuseum/ckanext-dataspatial.git
  ```

2. Activate the virtual env:

  ```bash
  . $INSTALL_FOLDER/bin/activate
  ```

3. Install the requirements from requirements.txt:

  ```bash
  cd $INSTALL_FOLDER/src/ckanext-dataspatial
  pip install -r requirements.txt
  ```

4. Run setup.py:

  ```bash
  cd $INSTALL_FOLDER/src/ckanext-dataspatial
  python setup.py develop
  ```

5. Add 'dataspatial' to the list of plugins in your `$CONFIG_FILE`:

  ```ini
  ckan.plugins = ... dataspatial
  ```

## Configuration
There are a number of options that can be specified in your .ini config file. They all have defaults set, so none are _required_.

Name|Description|Default
--|---|--
`dataspatial.postgis.field`|WGS data field in the PostGIS database|\_geom
`dataspatial.postgis.mercator_field`|Mercator field in the PostGIS database|_geom\_webmercator

## Further Setup
Geospatial searches and query extent work both with PostGIS and Solr, but both require further setup before they can be used.

### PostGIS
To use this extension, your PostgreSQL database must have [PostGIS](http://postgis.net) support.

1. Install the correct version of PostGIS for your version of PostgreSQL: https://postgis.net/documentation/getting_started/

2. You will then need to create PostGIS columns on your resources. Invoking the command below will create the two columns named above (`dataspatial.postgis.field` and `dataspatial.postgis.mercator_field`) on table `$RESOURCE_ID`.  One represents the [WGS](http://en.wikipedia.org/wiki/World_Geodetic_System) (World Geodetic System) data, and one uses the web mercator projection, which is useful for generating maps.
    ```bash
    ckan dataspatial create-columns $RESOURCE_ID -c $CONFIG_FILE
    ```

## Usage
### Actions
#### `populate_geom_columns`
Updates the geospatial column when a row is updated (this is not done automatically so must be implemented in your own workflow). Equivalent to the `populate-columns` [command](#commands).

```python
from ckan.plugins import toolkit

toolkit.get_action('update_geom_columns')(
    context,
    {
        'resource_id': 'RESOURCE_ID',
        'latitude_field': 'LATITUDE_COLUMN',
        'longitude_field': 'LONGITUDE_COLUMN',
        'wkt_field': 'WKT_COLUMN'
    }
)
```

#### `datastore_search`
Searching by geospatial fields involves passing a custom filter to `datastore_search`. The filter `_tmgeom` contains a [WKT](http://en.wikipedia.org/wiki/Well-known_text) (Well-Known Text) string representing the area to be searched (currently, only the types `POLYGON` or `MULTIPOLYGON` will work). e.g.:

```python
from ckan.plugins import toolkit

search_params = {
    'resource_id': 'RESOURCE_ID',
    'filters': '_tmgeom:POLYGON(36 114, 36 115, 37 115, 37 114, 36 114)'
}
search = toolkit.get_action(u'datastore_search')(context, search_params)
```

#### `datastore_query_extent`
To see the geospatial extent of the query, the same parameters as above can be submitted to the action `datastore_query_extent`:

```python
from ckan.plugins import toolkit

search_params = {
    'resource_id': 'RESOURCE_ID',
    'filters': '_tmgeom:POLYGON(36 114, 36 115, 37 115, 37 114, 36 114)'
}
search = toolkit.get_action(u'datastore_query_extent')(context, search_params)
```

This will return a `dict`:
Key|Description
---|-----------
`total_count`|Total number of rows matching the query
`geom_count`|Number of rows matching the query that have geospatial information
`bounds`|((lat min, long min), (lat max, long max)) for the queries rows

### Commands
#### `dataspatial`

1. `create-columns`: create the PostGIS columns on the `$RESOURCE_ID` table.
    ```bash
    ckan dataspatial create-columns $RESOURCE_ID --geom-type=$GEOM_TYPE -c $CONFIG_FILE
    ```

2. `create-index`: create index for PostGIS columns on the `$RESOURCE_ID` table.
    ```bash
    ckan dataspatial create-index $RESOURCE_ID -c $CONFIG_FILE
    ```

3. `populate-columns`: populate the PostGIS columns from the given lat & long fields. Equivalent to the `update_geom_columns()` action.
    ```bash
    ckan dataspatial populate-columns $RESOURCE_ID -l $LATITUDE_COLUMN -g $LONGITUDE_COLUMN -c $CONFIG_FILE
    ```


## Testing
*tests coming soon*


## Acknowledgements
Based on [ckanext-dataspatial](https://github.com/NaturalHistoryMuseum/ckanext-dataspatial) created by the Natural History Museum in London, UK.
<img src=".github/nhm-logo.svg" align="left" width="150px" height="100px" hspace="40"/>

