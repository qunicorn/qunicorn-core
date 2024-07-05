Documentation and ReadTheDocs Setup
===================================

Using the Documentation Locally
-------------------------------

.. note:: This tutorial assumes, that the project is already installed via poetry!

* To build the documentation run the following command from the qunicorn root directory:

.. code-block:: bash

    poetry run invoke doc

* To view the generated documentation open :file:`docs/_build/index.html` in your browser or use the following command to open the browser:

.. code-block:: bash

    poetry run invoke browse-doc

* To update the source code documentation under :file:`docs/source` run

.. code-block:: bash

    poetry run invoke update-source-doc

To search for valid reference targets use the following command after building the documentation at least once:

.. code-block:: bash

    poetry run invoke doc-index -f <insert search string here>

.. seealso:: The documentation is built using Sphinx and reStructuredText.

    Documentation for the **reStructuredText syntax** and available roles/directives: https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html

.. hint:: Markdown files are also supported:

    Markdown uses the **MyST syntax**: https://myst-parser.readthedocs.io/en/latest/syntax/typography.html

.. hint:: Some documentation parameters are configured in the :file:`pyproject.toml` file.


Updating Requirements
**********************

If the requirements of the main project have changed, run the following command to update the requirements across the whole project (includding the documentation).

.. code-block:: bash

    poetry run invoke update-dependencies

Setting up remote
-------------------------

Initial Setup
**********************

* Register at: `ReadTheDocs <https://about.readthedocs.com/?ref=readthedocs.org>`_
* Import a Project from GitHub
* Choose Branch
* Build the Docs

Testing
**********************

* Push changes to Github
* Rebuild Docs

Setting Up Webhook
**********************

* Create Webhook in Github (:menuselection:`Settings --> Webhooks --> Add Webhook`)
    * Data from ReadTheDocs can be found under :menuselection:`Admin --> Integrations`
    * Tutorial: `How to manually configure a Git repository integration <https://docs.readthedocs.io/en/latest/guides/git-integrations.html>`_
* Webhook automatically appears under Integrations
