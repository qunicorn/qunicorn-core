"""Module containing the root endpoint of the DEVICES API."""

from dataclasses import dataclass
from flask.helpers import url_for
from flask.views import MethodView
from http import HTTPStatus
from ..util import SecurityBlueprint as SmorestBlueprint
from ..models import RootSchema


USERS_API = SmorestBlueprint(
    "users-api",
    "USERS API",
    description="Users API to list available resources.",
    url_prefix="/users",
)


@dataclass()
class RootData:
    root: str


@USERS_API.route("/")
class RootView(MethodView):
    """Root endpoint of the services api, to list all available services."""

    @USERS_API.response(HTTPStatus.OK, RootSchema())
    def get(self):
        """Get the urls of the next endpoints of the users api to call."""
        return RootData(root=url_for("users-api.UsersView", _external=True))
