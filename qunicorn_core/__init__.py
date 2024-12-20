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

"""Root module containing the flask app factory."""

from json import load as load_json
from logging import WARNING, Formatter, Handler, Logger, getLogger
from logging.config import dictConfig
from os import environ, makedirs
from pathlib import Path
from typing import Any, Dict, Optional, cast

import click
from flask.app import Flask
from flask.cli import FlaskGroup
from flask.logging import default_handler
from flask_cors import CORS
from tomli import load as load_toml

from . import api, celery, core, db, licenses, util
from .util.config import DebugConfig, ProductionConfig
from .util.reverse_proxy_fix import apply_reverse_proxy_fix

# change this to change tha flask app name and the config env var prefix
# must not contain any spaces!
APP_NAME = __name__
CONFIG_ENV_VAR_PREFIX = APP_NAME.upper().replace("-", "_").replace(" ", "_")
app: Flask


def create_app(test_config: Optional[Dict[str, Any]] = None):
    """Flask app factory."""
    instance_path: str | None = environ.get("INSTANCE_PATH", None)
    if instance_path:
        if Path(instance_path).is_file():
            instance_path = None

    # create and configure the app
    app = Flask(APP_NAME, instance_relative_config=True, instance_path=instance_path)

    # load defaults
    config = app.config
    flask_debug: bool = (
        config.get("DEBUG", False) or environ.get("FLASK_ENV", "production").lower() == "development"
    )  # noqa
    if flask_debug:
        config.from_object(DebugConfig)
    elif test_config is None:
        # only load production defaults if no special test config is given
        config.from_object(ProductionConfig)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        config.from_pyfile("config.py", silent=True)
        # also try to load json config
        config.from_file("config.json", load=load_json, silent=True)
        # also try to load toml config
        config.from_file("config.toml", load=load_toml, silent=True)
        # load config from file specified in env var
        config.from_envvar(f"{CONFIG_ENV_VAR_PREFIX}_SETTINGS", silent=True)
        # TODO load some config keys directly from env vars

        # load Redis URLs from env vars
        if "BROKER_URL" in environ:
            celery_conf = config.get("CELERY", {})
            celery_conf["broker_url"] = celery_conf["result_backend"] = environ["BROKER_URL"]
            config["CELERY"] = celery_conf

        if "RESULT_BACKEND" in environ:
            celery_conf = config.get("CELERY", {})
            celery_conf["result_backend"] = environ["RESULT_BACKEND"]
            config["CELERY"] = celery_conf

        if "CELERY_QUEUE" in environ:
            celery_conf = config.get("CELERY", {})
            celery_conf["task_default_queue"] = environ["CELERY_QUEUE"]
            config["CELERY"] = celery_conf

        if "DB_URL" in environ:
            config["SQLALCHEMY_DATABASE_URI"] = environ["DB_URL"]

        if "SERVER_NAME" in environ:
            config["SERVER_NAME"] = environ["SERVER_NAME"]

        if "REVERSE_PROXY_COUNT" in environ:
            config["REVERSE_PROXY_COUNT"] = int(environ["REVERSE_PROXY_COUNT"])
            apply_reverse_proxy_fix(app)

        if "QPROV_URL" in environ:
            config["QPROV_URL"] = environ["QPROV_URL"]

        if "CIRCUIT_CUTTING_URL" in environ:
            config["CIRCUIT_CUTTING_URL"] = environ["CIRCUIT_CUTTING_URL"]
    else:
        # load the test config if passed in
        config.from_mapping(test_config)

    # fix psycopg2 database urls of old docker compose files
    if (db_url := config.get("SQLALCHEMY_DATABASE_URI", "")).startswith("postgresql+psycopg2:"):
        config["SQLALCHEMY_DATABASE_URI"] = db_url.replace("postgresql+psycopg2:", "postgresql+psycopg:", 1)

    # End Loading config #################

    # Configure logging
    log_config = cast(Optional[Dict[Any, Any]], config.get("LOG_CONFIG"))
    if log_config:
        # Apply full log config from dict
        dictConfig(log_config)
    else:
        # Apply smal log config to default handler
        log_severity = max(0, config.get("DEFAULT_LOG_SEVERITY", WARNING))
        # use percent for backwards compatibility in case of errors
        log_format_style = cast(str, config.get("DEFAULT_LOG_FORMAT_STYLE", "%"))
        log_format = cast(Optional[str], config.get("DEFAULT_LOG_FORMAT"))
        date_format = cast(Optional[str], config.get("DEFAULT_LOG_DATE_FORMAT"))
        if log_format:
            formatter = Formatter(log_format, style=log_format_style, datefmt=date_format)
            default_logging_handler = cast(Handler, default_handler)
            default_logging_handler.setFormatter(formatter)
            default_logging_handler.setLevel(log_severity)
            root = getLogger()
            root.addHandler(default_logging_handler)
            app.logger.removeHandler(default_logging_handler)

    logger: Logger = app.logger
    logger.info(
        f"Configuration loaded. Possible config locations are: 'config.py', "
        f"'config.json', Environment: '{CONFIG_ENV_VAR_PREFIX}_SETTINGS'"
    )

    if config.get("SECRET_KEY") == "debug_secret":
        logger.error('The configured SECRET_KEY="debug_secret" is unsafe and must not be used in production!')

    # ensure the instance folder exists
    try:
        makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Begin loading extensions and routes

    licenses.register_licenses(app)

    celery.register_celery(app)

    db.register_db(app)

    api.register_root_api(app)

    # allow cors requests everywhere (CONFIGURE THIS TO YOUR PROJECTS NEEDS!)
    CORS(app)

    if config.get("DEBUG", False):
        # Register debug routes when in debug mode
        from .util.debug_routes import register_debug_routes

        register_debug_routes(app)

    # To display the errors differently in the swagger ui
    @app.errorhandler(Exception)
    def handle_errors(error):
        logger.error(str(error), exc_info=True)
        if isinstance(error, NotImplementedError):
            error_code: int = 501
        else:
            error_code: int = 500
        return {
            "error": type(error).__name__,
            "message": str(error),
        }, error_code

    return app


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """Cli entry point for autodoc tooling."""
    pass
