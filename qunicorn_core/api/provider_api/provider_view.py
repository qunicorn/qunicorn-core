# Copyright 2023 University of Stuttgart
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Module containing the routes of the Taskmanager API."""
from http import HTTPStatus
from typing import Optional

from flask.globals import current_app
from flask.views import MethodView

from .blueprint import PROVIDER_API
from ..api_models.provider_dtos import ProviderDtoSchema, ProviderFilterParamsSchema
from ...core import provider_service


@PROVIDER_API.route("/")
class ProviderView(MethodView):
    """Root endpoint of the provider api, to list all available provider_apis."""

    @PROVIDER_API.arguments(ProviderFilterParamsSchema(), location="query", as_kwargs=True)
    @PROVIDER_API.response(HTTPStatus.OK, ProviderDtoSchema(many=True))
    def get(self, name: Optional[str] = None):
        """Get all providers from the database"""
        current_app.logger.info("Request: get all providers from database")
        return provider_service.get_all_providers(name=name)


@PROVIDER_API.route("/<int:provider_id>/")
class ProviderIDView(MethodView):
    """Provider Endpoint to get properties of a specific provider."""

    @PROVIDER_API.response(HTTPStatus.OK, ProviderDtoSchema())
    def get(self, provider_id):
        """Get information about a single provider."""
        current_app.logger.info(f"Request: get information about provider with id: {provider_id}")
        return provider_service.get_provider_by_id(provider_id)
