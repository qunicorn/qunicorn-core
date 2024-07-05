Run using docker-compose
=========================================
Execute the following commands to start the deployment using docker-compose. This will build the docker image
containing the application and creates all required containers including the database and the message queue.

Start the docker-compose:

.. code-block:: bash

  docker-compose up -d


For testing with a local build use:

.. code-block:: bash

    docker-compose -f docker-compose.yaml -f docker-compose.local.yaml up -d


.. image:: ../resources/images/docker-compose-architecture.svg
  :width: 700
  :alt: Architecture

