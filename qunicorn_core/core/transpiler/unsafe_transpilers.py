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

from typing import Any

from pyquil import Program
from qrisp import QuantumCircuit as QrispQC

from braket.circuits import Circuit  # noqa
from qiskit import QuantumCircuit  # noqa

from .circuit_transpiler import CircuitTranspiler


class QiskitPythonToQiskit(CircuitTranspiler, source="QISKIT-PYTHON", target="QISKIT", cost=1):
    unsafe = True

    def transpile_circuit(self, circuit: Any) -> QuantumCircuit:
        circuit_globals = {"QuantumCircuit": QuantumCircuit}
        exec(circuit, circuit_globals)
        try:
            qiskit_circuit = circuit_globals["circuit"]
        except KeyError:
            raise ValueError("The circuit program did not contain a variable called 'circuit'!")
        if isinstance(qiskit_circuit, QuantumCircuit):
            return qiskit_circuit
        raise TypeError(
            "The circuit type does not match the expected type. "
            f"(Expected {QuantumCircuit}, but got {type(qiskit_circuit)})"
        )


class BraketPythonToBraket(CircuitTranspiler, source="BRAKET-PYTHON", target="BRAKET", cost=1):
    unsafe = True

    def transpile_circuit(self, circuit: Any) -> Circuit:
        circuit_globals = {"Circuit": Circuit}
        braket_circuit = eval(circuit, circuit_globals)
        if isinstance(braket_circuit, Circuit):
            return braket_circuit
        raise TypeError(
            f"The circuit type does not match the expected type. (Expected {Circuit}, but got {type(braket_circuit)})"
        )


class QrispPythonToQrisp(CircuitTranspiler, source="QRISP-PYTHON", target="QRISP", cost=1):
    unsafe = True

    def transpile_circuit(self, circuit: Any) -> QrispQC:
        circuit_globals = {"QuantumCircuit": QrispQC}
        exec(circuit, circuit_globals)
        try:
            qrisp_circuit = circuit_globals["circuit"]
        except KeyError:
            raise ValueError("The circuit program did not contain a variable called 'circuit'!")
        if isinstance(qrisp_circuit, QrispQC):
            return qrisp_circuit
        raise TypeError(
            f"The circuit type does not match the expected type. (Expected {QrispQC}, but got {type(qrisp_circuit)})"
        )


class QuilPythonToQuil(CircuitTranspiler, source="QUIL-PYTHON", target="QUIL", cost=1):
    unsafe = True

    def transpile_circuit(self, circuit: Any) -> Program:
        circuit_globals = {"Program": Program}  # TODO: test this...
        exec(circuit, circuit_globals)
        try:
            quil_circuit = circuit_globals["circuit"]
        except KeyError:
            raise ValueError("The circuit program did not contain a variable called 'circuit'!")
        if isinstance(quil_circuit, Program):
            return quil_circuit
        raise TypeError(
            f"The circuit type does not match the expected type. (Expected {Program}, but got {type(quil_circuit)})"
        )
