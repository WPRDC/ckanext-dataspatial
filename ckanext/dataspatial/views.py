# encoding: utf-8

import ckan.lib.base as base
import ckan.logic as logic
import ckan.plugins.toolkit as toolkit
from ckan.common import _
from flask import Blueprint
from flask.views import MethodView

from ckanext.dataspatial.actions import TASK_TYPE, TASK_KEY
from ckanext.dataspatial.types import StatusResult

dataspatial = Blueprint("dataspatial", __name__)


def get_blueprints():
    return [dataspatial]


def render_resource_data_view(package_id: str, resource_id: str):
    try:
        pkg_dict = toolkit.get_action("package_show")({}, {"id": package_id})
        resource = toolkit.get_action("resource_show")({}, {"id": resource_id})

        # backward compatibility with old templates
        toolkit.g.pkg_dict = pkg_dict
        toolkit.g.resource = resource

    except (logic.NotFound, logic.NotAuthorized):
        base.abort(404, _("Resource not found"))

    # get job status
    status: StatusResult = toolkit.get_action("dataspatial_status")(
        {"user": "default"},
        {"resource_id": resource_id},
    )

    return base.render(
        "dataspatial/resource_dataspatial.html",
        extra_vars={
            "pkg_dict": pkg_dict,
            "resource": resource,
            "status": status,
        },
    )


class ResourceDataView(MethodView):
    def post(self, id: str, resource_id: str):
        """Submit job and return its status"""
        toolkit.get_action("dataspatial_submit")(
            {"user": "default"}, {"resource_id": resource_id}
        )

        return toolkit.redirect_to(
            "dataspatial.resource_dataspatial", id=id, resource_id=resource_id
        )

    def get(self, id: str, resource_id: str):
        """Return status of the georeference job for this resource if it exists"""
        return render_resource_data_view(id, resource_id)


dataspatial.add_url_rule(
    "/dataset/<id>/resource_dataspatial/<resource_id>",
    view_func=ResourceDataView.as_view(str("resource_dataspatial")),
)
