# Copyright 2024 University of Stuttgart
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""test circuit transpilers"""

from qiskit import QuantumCircuit

from qunicorn_core.core.transpiler import transpile_circuit
from qunicorn_core.core.transpiler.circuit_transpiler import CircuitTranspiler


def test_no_transpile():
    circuit = QuantumCircuit()
    transpiled = transpile_circuit("QISKIT", ("QISKIT", circuit))
    assert transpiled is circuit


def test_no_transpile_multiple():
    circuit = QuantumCircuit()
    transpiled = transpile_circuit("QISKIT", ("QASM2", "test"), ("QISKIT", circuit), ("QASM3", "test2"))
    assert transpiled is circuit


def test_qasm2_roundtrip():
    circuit = QuantumCircuit(1)
    circuit.h(0)
    qasm2 = transpile_circuit("QASM2", ("QISKIT", circuit))
    assert isinstance(qasm2, str)
    assert "OPENQASM 2.0;" in qasm2
    assert "h q[0];" in qasm2
    assert "measure" not in qasm2
    transpiled = transpile_circuit("QISKIT", ("QASM2", qasm2))
    assert isinstance(transpiled, QuantumCircuit)
    assert transpiled.num_qubits == circuit.num_qubits
    for t_gate, c_gate in zip([g for g in transpiled], [g for g in circuit]):
        assert t_gate.operation.name == c_gate.operation.name
        assert len(t_gate.qubits) == len(c_gate.qubits)
        for t_qubit, c_qubit in zip(t_gate.qubits, c_gate.qubits):
            assert t_qubit.index == c_qubit.index
        assert len(t_gate.clbits) == len(c_gate.clbits)


def test_connectivity():
    """Assert that all formats can be transpiled to all other formats."""

    # use this to set exeptions to full connectivity
    known_partially_connected = {"QISKIT-PYTHON", "BRAKET-PYTHON", "QRISP-PYTHON", "QUIL-PYTHON", "QUIL"}

    formats = CircuitTranspiler.get_known_formats()

    full_connectivity = formats - known_partially_connected

    known_full_connectivity = set()

    missing_connections = {}

    def is_fully_connected(format_):
        connectivity = {format_}  # set for all reachable formats
        explored = set()  # set for all already expanded formats
        while explored != connectivity:  # all reachable formats expanded
            for source in connectivity - explored:  # all not expanded formats
                explored.add(source)
                for transpiler in CircuitTranspiler.get_transpilers(source):
                    connectivity.add(transpiler.target)
                if not known_full_connectivity.isdisjoint(connectivity):
                    # at least one already known fully connected format was reached
                    return True
        if connectivity >= full_connectivity:
            return True
        else:
            missing_connections[format_] = full_connectivity - connectivity
            return False

    for format_ in formats:
        if is_fully_connected(format_):
            known_full_connectivity.add(format_)

    missing = "\n".join((f"{source}: " + ", ".join(targets)) for source, targets in missing_connections.items())

    assert known_full_connectivity >= full_connectivity, f"Missing connections:\n {missing}"
