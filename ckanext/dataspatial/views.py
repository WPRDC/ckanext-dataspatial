# encoding: utf-8

from flask import Blueprint
from flask.views import MethodView

import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
import ckan.lib.helpers as core_helpers
import ckan.lib.base as base

from ckan.common import _

dataspatial = Blueprint("dataspatial", __name__)


def get_blueprints():
    return [dataspatial]


class ResourceDataView(MethodView):
    def post(self, id: str, resource_id: str):
        try:
            toolkit.get_action("dataspatial_populate")({}, {"resource_id": resource_id})
        except logic.ValidationError:
            pass

        return core_helpers.redirect_to(
            "dataspatial.resource_dataspatial", id=id, resource_id=resource_id
        )

    def get(self, id: str, resource_id: str):
        try:
            pkg_dict = toolkit.get_action("package_show")({}, {"id": id})
            resource = toolkit.get_action("resource_show")({}, {"id": resource_id})

            # backward compatibility with old templates
            toolkit.g.pkg_dict = pkg_dict
            toolkit.g.resource = resource

        except (logic.NotFound, logic.NotAuthorized):
            base.abort(404, _("Resource not found"))

        try:
            datapusher_status = toolkit.get_action("datapusher_status")(
                {}, {"resource_id": resource_id}
            )
        except logic.NotFound:
            datapusher_status = {}
        except logic.NotAuthorized:
            base.abort(403, _("Not authorized to see this page"))

        return base.render(
            "dataspatial/resource_dataspatial.html",
            extra_vars={
                "status": datapusher_status,
                "pkg_dict": pkg_dict,
                "resource": resource,
            },
        )


dataspatial.add_url_rule(
    "/dataset/<id>/resource_dataspatial/<resource_id>",
    view_func=ResourceDataView.as_view(str("resource_dataspatial")),
)
