QMWare Pilot
================

This site gives an overview of the functionality of the QMWare Pilot.

The QMWare Pilot is implemented in an experimental form, and currently allows the usage of the testing environment.

**Note**: The Tokens provides by QMWare are necessary for the execution and need to be in environment variables in the form of:

* QMWARE_URL="https://dispatcher.dev.qmware-dev.cloud/"
* QMWARE_API_KEY=""
* QMWARE_API_KEY_ID=""

Standard Devices
^^^^^^^^^^^^^^^^^^

The local simulator (workaround): **fake_qiskit**

The standard device for the testing environment is: **dev**

Main Languages
^^^^^^^^^^^^^^^^^^^^

* QASM2

Supported Job Types
^^^^^^^^^^^^^^^^^^^^

Runner
*******

**Description:** Execute a simple Job on QMWare devices.

**Notes:** Currently only allows for execution on the test environment with respective tokens.

**Required Language:** Quantum circuit can be provided in: QASM2
