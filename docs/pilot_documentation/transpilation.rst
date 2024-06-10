Transpilation
=============

Introduction
##############

Most circuits need to be transpiled to a suitable format before the pilots can execute them.
Each format is identified by a unique format string (e.g., "QISKIT", "QASM2", "QASM3", etc.).
The format conversions (transpilation) are done by CircuitTranslators that convert from one format to another.
Multiple CircuitTranslators may be chained to reach a specific target format.


Available Formats and Translators
#################################

.. graphviz:: transpilers.dot
    :align: center
    :caption: Available CircuitTranspilers

The graph shows all available formats (the nodes) and transpilation paths between these formats (the edges).
Some transpilation paths have a higher cost, meaning that they are less likely to be used.
Unsafe transpilation paths can be enabled explicitly but are disabled by default.


Adding new CircuitTranspilers
#############################

To add a new transpiler, create a class inheriting from ``CircuitTranspiler`` and implement the ``transpile_circuit`` method.
The new transpiler should specify the ``source`` and ``target`` format in the class definition.

.. code-block:: python

    class DemoTranspiler(CircuitTranspiler, source="source-format", target="target-format", cost=1):
        unsafe = False  # set to True if transpilation may execute unsafe code

        def transpile_circuit(self, circuit: Any) -> Any:
            ...

