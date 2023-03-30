"""Module containing the routes of the Taskmanager API."""

from ..models.users import UserIDSchema, UsersSchema 
from typing import Dict, List
from flask.helpers import url_for
from flask.views import MethodView
from dataclasses import dataclass
from http import HTTPStatus

from .root import USERS_API


@dataclass
class USERS:
    userID: str
    description: str
    simulator: bool


@USERS_API.route("/<string:users_id>/")
class UsersView(MethodView):
    """Users Endpoint to get properties of a specific user via ID."""

    @USERS_API.arguments(UserIDSchema(), location="path")
    @USERS_API.response(HTTPStatus.OK, UsersSchema())
    def get(self):
        """Get information about a sinlge user."""
        
        pass

