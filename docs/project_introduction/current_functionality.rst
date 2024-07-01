Current Functionality
#####################

As a brief overview of the current functionality of the application, the main way to access the application is through the defined API Endpoints.

A good way to get an overview, is to access the `Swagger UI <http://localhost:5005/swagger-ui>`_.
It also contains samples values for API calls.
An alternative interface based on rapidoc is also provided under `/rapidoc <http://localhost:5005/rapidoc>`_.

The defined Endpoints can be found in the API documentation under :doc:`API Documentation <../architecture_documentation/api_documentation/apidocumentation>`.

Available Providers
^^^^^^^^^^^^^^^^^^^
Currently the following providers are available:

* IBMQ:
   * Base languages:
        * Qiskit
   * Available Job Types:
        * RUNNER
        * ESTIMATOR
        * SAMPLER
   * Experimental Job Types:
        * IBM_UPLOAD (Uploads a Job to the IBM Backend)
        * IBM_RUNNER (Runs a previously uploaded job from the IBM Backend)

* AWS
    * Base languages:
        * QASM3
        * BRAKET
    * Available Functions
        * RUNNER

* Rigetti:
    * Base languages:
        * Quil
    * Available Functions
        * RUNNER

Please note that this list is not exhaustive and will be updated as more providers are added.


Supported Assembler languages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Qunicorn supports a vast array of different assembler languages in the context of quantum computing.

* QASM2
* QASM3
* Braket
* Qiskit
* Python
* Qrisp
* Quil

Please note that this list is not exhaustive and will be updated as more assembler languages are added.


Job Types
^^^^^^^^^^

The following Job Types are currently available, check with the provider for more information on the specific job types.

* RUNNER
* SAMPLER
* ESTIMATOR
* IBM_UPLOAD (Experimental)
* IBM_RUNNER (Experimental)
