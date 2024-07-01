How to create a new pilot
=========================

.. todo:: This documentation needs some work!


1. Locate the :any:`qunicorn_core.core.pilotmanager` module.
2. Create a new python file for the pilot and implement the pilot by referencing one of the existing pilots (e.g., :py:mod:`~qunicorn_core.core.pilotmanager.ibm_pilot`).
3. Make sure to implement all required methods from :py:class:`~qunicorn_core.core.pilotmanager.base_pilot.Pilot` (i.e. implement all methods that raise a :py:class:`NotImplementedError`).
4. Add your pilot to the imports in the ``__init__.py`` file of the :any:`qunicorn_core.core.pilotmanager` module.
5. Add your pilot to the :py:data:`~qunicorn_core.core.pilotmanager.pilot_manager.PILOTS` list of the :any:`qunicorn_core.core.pilotmanager.pilot_manager` module.
6. Make sure the pilot metadata (such as supported languages, etc.) is added to the relevant enums (i.e. :py:class:`~qunicorn_core.static.enums.provider_name.ProviderName` and :py:class:`~qunicorn_core.static.enums.assembler_languages.AssemblerLanguage`).
7. If required, implement the relevant transpilers to support new formats in the :any:`qunicorn_core.core.transpiler` module and importing in the ``__init__.py`` file of the module.
8. If the dependencies have changed run ``poetry run invoke update-dependencies`` to update the doc dependencies and the list of licences.
9. Write some tests and update the source documentation using ``poetry run invoke update-source-doc``.

