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

from qiskit import QuantumCircuit as QiskitCircuit
from qrisp.circuit.quantum_circuit import QuantumCircuit as QrispCircuit

from .circuit_transpiler import CircuitTranspiler


class QiskitToQrisp(CircuitTranspiler, source="QISKIT", target="QRISP", cost=1):

    def transpile_circuit(self, circuit: Any) -> QrispCircuit:
        assert isinstance(circuit, QiskitCircuit)
        converted = QrispCircuit.from_qiskit(circuit)
        assert isinstance(converted, QrispCircuit)
        return converted


class QrispToQiskit(CircuitTranspiler, source="QRISP", target="QISKIT", cost=1):

    def transpile_circuit(self, circuit: Any) -> QiskitCircuit:
        assert isinstance(circuit, QrispCircuit)
        converted = circuit.to_qiskit()
        assert isinstance(converted, QiskitCircuit)
        return converted
