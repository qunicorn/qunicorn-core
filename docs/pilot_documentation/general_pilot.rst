Pilot Documentation
===================

Introduction
^^^^^^^^^^^^

Pilots are used to communicate with providers of quantum computing resources.
They are used to submit jobs to the provider and to retrieve the results of the jobs.
The Pilot is also responsible for saving the received results to the database.
The pilots are run asynchronously on a worker.
In qunicorn, this is handled by a celery queue.

Implementation
^^^^^^^^^^^^^^

All pilots implement the :py:class:`~qunicorn_core.core.pilotmanager.base_pilot.Pilot` class from the :py:mod:`~qunicorn_core.core.pilotmanager.base_pilot` module.
The :py:class:`~qunicorn_core.core.pilotmanager.base_pilot.Pilot` class is an abstract class and defines the interface for all pilots.
It also implements some general logic used by all pilots.

This ensures a consistent interface for all pilots and allows for easy extension of the pilot framework.
For more information on how to create a new Pilot, refer to this Tutorial:

:doc:`How to create a new pilot <../tutorials/pilot_tutorial>`

Supported/Tested gates on IBM and AWS: X, Y, Z, H, CX, CXX, S, T

Providers
^^^^^^^^^^

Each Pilot belongs to a Provider.
Providers are companies, and other institutions, which provide quantum computing services.
The Pilot communicates with the API of the providers, or uses the provider specific SDKs to perform local simulations.

Available Pilot Implementations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Qunicorn supports various pilots for communication with providers. At this moment, the following pilots are available:

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   aws_pilot
   ibm_pilot
   rigetti_pilot
   qmware_pilot

