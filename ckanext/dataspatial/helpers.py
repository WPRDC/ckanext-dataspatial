from ckan.plugins import toolkit
from ckanext.dataspatial.types import GeoreferenceStatus


def dataspatial_status_description(status: dict) -> str:
    _ = toolkit._

    if status["status"]:
        captions = {
            GeoreferenceStatus.COMPLETE.value: _("Complete"),
            GeoreferenceStatus.PENDING.value: _("Pending"),
            GeoreferenceStatus.SUBMITTING.value: _("Submitting"),
            GeoreferenceStatus.ERROR.value: _("Error"),
        }

        return captions.get(status["status"], _(status["status"]))
    else:
        return _("Not Uploaded Yet")
