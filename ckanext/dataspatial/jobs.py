import json

from ckan.plugins import toolkit
from ckan.types import Context

from ckanext.dataspatial.lib import geofiles, postgis
from ckanext.dataspatial.types import StatusCallback, GeoreferenceStatus


JOB_TYPE = "dataspatial_georeference"


def make_status_callback(
    resource_id: str,
    job_created: str,
    context: Context,
) -> StatusCallback:
    def callback(
        status: str,
        value: dict = None,
        error: str = None,
    ) -> None:
        data_dict = {
            "resource_id": resource_id,
            "job_created": job_created,
            "status": status,
        }
        if error:
            data_dict["error"] = error
        if value:
            data_dict["value"] = value

        return toolkit.get_action("dataspatial_hook")(context, data_dict)

    return callback


def georeference_datastore_table(
    resource_id: str,
    job_created: str,
    logger,
) -> None:
    callback = make_status_callback(resource_id, job_created, {"user": "default"})

    resource = toolkit.get_action("resource_show")(
        {"user": "default"},
        {"id": resource_id},
    )

    if resource["format"].lower() == "geojson":
        geofiles.load_geojson_to_datastore(resource_id, status_callback=callback)

    elif "datastore_active" in resource and resource["datastore_active"]:
        postgis.prepare_and_populate_geoms(resource, status_callback=callback)

    else:
        callback(
            GeoreferenceStatus.ERROR,
            error="Can only georeference geojson files or resources pushed to datastore.",
        )
        raise toolkit.ValidationError(
            "Can only georeference geojson files or resources pushed to datastore."
        )

    callback(GeoreferenceStatus.COMPLETE, value={"notes": ""})
