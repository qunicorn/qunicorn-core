Linting and Formatting
=======================

Local Linting with Flake8 (VSC):
################################

* Install `Flake8 Extension <https://marketplace.visualstudio.com/items?itemName=ms-python.flake8>`_
    * If python environment included flake8 already, it will automatically start linting the python files
    * Otherwise: Install Flake8 (`Documentation <https://flake8.pycqa.org/en/latest/>`_)
* Qunicorn Flake8 Settings can be found in .flake8
* Display the current problems in the console: :code:`flake8 .`
* Check for Linting Errors  (black & flake) with:

.. code-block:: bash

    poetry run invoke check-linting

Flake8 Settings
****************

* Ignore single line: Add :code:`# noqa` to the end of the line

* Ignore specific error in a single line: Add :code:`# noqa E711` to the end of the line

* Ignore whole file: Add :code:`# flake8: noqa` at the start of the file

* Ignore certain warnings in files, add to .flake8 file

.. code-block:: bash

    per-file-ignores =
        filename:ErrorCode

    e.g.:

    per-file-ignores =
        __init__.py:F401,F403,C901

Formatting with black
################################

* Install Black

.. code-block:: bash

    pip install black

* Check if there are open black warnings/errors in the project

.. code-block:: bash

    black --check .

* Run Black on a single file:

.. code-block:: bash

    black filename

* OR: Run Black on directory or directly on the current navigated folder

.. code-block:: bash

    black directory/
    black .

This will automatically format the selected files

* Files or directories can also be excluded

.. code-block:: bash

    black --check --extend-exclude="regex" directory

* To get more information on the progress add :code:`--verbose` option

Automatic Formatting on Save
*****************************

* In Pycharm:
    * Strg+Alt+A → Search for “Actions on Save” → check “Reformat code” and “Optimize imports”
    * “Settings” → “Editor” → “Code Style” → “Python”
    * Furthermore: Disable Line breaks reformatting and increase hard wrap
