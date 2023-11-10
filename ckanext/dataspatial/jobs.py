from ckan.plugins import toolkit
from ckan.types import Context

from ckanext.dataspatial.lib import geofiles, postgis
from ckanext.dataspatial.types import StatusCallback, JOB_COMPLETION_STATUS


JOB_TYPE = "dataspatial_georeference"


def make_status_callback(
    resource_id: str,
    job_created: str,
    context: Context,
) -> StatusCallback:
    def callback(status: str = "") -> None:
        return toolkit.get_action("dataspatial_hook")(
            context,
            {
                "resource_id": resource_id,
                "job_created": job_created,
                "status": status,
            },
        )

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
        raise toolkit.ValidationError(
            "Can only georeference geojson files or resources pushed to datastore."
        )

    callback(JOB_COMPLETION_STATUS)
