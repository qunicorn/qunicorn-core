Useful Commands
=================

How to create invoke commands
##############################

Add a method to qunicorn-core/tasks.py. All underscores in the method name will be transformed into hyphens (``hello_world`` → ``hello-world``).

To execute something in the terminal use the context :code:`c` that is passed as an argument to the method.
With :code:`c.run` a command can be executed.

The method 'your_new_command' can be executed via the terminal with:

.. code-block:: bash

    poetry run invoke [your-new-command]

How to create flask commands
##############################

Add a method to qunicorn_core.db.cli.py with the annotation :code:`@DB_CLI.command([your-command])`.

This method can be executed via the terminal, with the command

.. code-block:: bash

    flask [your-command]

How to add a dependency to poetry
##################################

.. code-block:: bash

    poetry add [dependency-name]

It will automatically install the dependency and add it to the 'pyproject.toml'- and 'poetry.lock'-file.
Both need to be pushed to git.
