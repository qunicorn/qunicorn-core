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

"""File to store all costume exceptions used in qunicorn"""
from http import HTTPStatus

from werkzeug.exceptions import HTTPException


class QunicornError(HTTPException):
    """General Exception raised for errors in qunicorn"""

    def __init__(self, msg, status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR):
        if not msg:
            try:  # try to get the status code description instead
                msg = HTTPStatus(status_code).description
            except ValueError:
                pass  # not a valid HTTP status code
        super().__init__(msg)
        self.code = status_code  # set status code
        self.data = {"message": msg}  # for compatibility with flask smorest
