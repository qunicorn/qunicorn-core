Project Structure
#####################

This site gives a brief overview of the project structure of the qunicorn project.
Describing the different packages and components within.

The Structure described can be found within the :py:mod:`qunicorn_core` package.

Structure of the project
*************************

api <Package>:
^^^^^^^^^^^^^^^^

The :py:mod:`api package <qunicorn_core.api>` contains all the api views and models. It is used to define the API.

* :py:mod:`api_models <qunicorn_core.api.api_models>` <Package>:
    * Contains DTOS and Schemas for all Objects
    * These are used for computation and to define the schemas for the api views
* {component}_api <Package>:
    * Contains the api definition for a component.

core <Package>:
^^^^^^^^^^^^^^^^

The :py:mod:`core package <qunicorn_core.core>` contains all the core logic of the project. This includes mappers and various services.

* :py:mod:`mapper <qunicorn_core.core.mapper>` <Package>:
    * Contains mappers to map between different objects.
    * This includes:
        * mapping from DTOs to Dataclass objects
        * mapping from Schemas to DTOs
* :py:mod:`pilotmanager <qunicorn_core.core.pilotmanager>` <Package>:
    * Contains the different pilots, which are used to communicate with different quantum providers
    * Contains the pilot_manager, a service class for handling of pilot data.
    * pilot_resources <Package>:
        * Contains resources for the pilots in the json format.
* :py:mod:`transpiler <qunicorn_core.core.transpiler>` <Package>:
    * Contains the transpiler, which is used to transpile between assembler languages used by different providers.
* {component}_service <.py File>
    * A service file for a component which handles communication between the api and other parts of the core package and the db package.

db <Package>:
^^^^^^^^^^^^^^^^

The :py:mod:`db package <qunicorn_core.db>` contains the database models and the database service. It is used to define the database, and to handle communication with it.

* :py:mod:`models <qunicorn_core.db.models>` <Package>:
    * Contains the definitions of the various database models.
* :py:mod:`cli <qunicorn_core.db.cli>` <.py File>:
    * Contains cli commands to interact with the database, such as setting up the database or pushing clean data.
* :py:mod:`db <qunicorn_core.db.db>` <.py File>:
    * Contains DB constant to avoid circular imports.

static <Package>:
^^^^^^^^^^^^^^^^^^

The :py:mod:`static package <qunicorn_core.static>` contains all static files, such as the enums used in the qunicorn project.

* :py:mod:`enums <qunicorn_core.static.enums>` <Package>:
    * Contains all enums used within the project.

util <Package>:
^^^^^^^^^^^^^^^^

The :py:mod:`util package <qunicorn_core.util>` contains various util files, as well as config files for the project.

* :py:mod:`config <qunicorn_core.util.config>` <Package>:
    * Contains config files for the project.
    * These include: Celery, Smorest and SQLAlchemy config files.
* :py:mod:`debug_routes <qunicorn_core.util.debug_routes>` <Package>:
    * Contains routes for debugging purposes.
* :py:mod:`logging <qunicorn_core.util.logging>` <.py File>:
    * A util file to set up logging.
* :py:mod:`reverse_proxy_fix <qunicorn_core.util.reverse_proxy_fix>` <.py File>
    * A util file to set up reverse proxy fix.
* :py:mod:`utils <qunicorn_core.util.utils>` <.py File>:
    * A util file to set up general util methods.
