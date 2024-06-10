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

from qiskit import QuantumCircuit as QiskitCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit import CircuitInstruction
from qiskit.circuit.quantumcircuitdata import QuantumCircuitData
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
        converted: QiskitCircuit = circuit.to_qiskit()
        fused_bits = self._fuse_bits(converted)

        assert isinstance(fused_bits, QiskitCircuit)
        return fused_bits

    @staticmethod
    def _fuse_bits(circuit: QiskitCircuit) -> QiskitCircuit:
        """
        When converting a Qrisp circuit to Qiskit each qubit / clbit is in a separate register. This method fuses them
        into one register.
        @param circuit: Qiskit circuit with each qubit / clbit in a separate register
        @return: a circuit where all qubits / clbits are in the same register
        """
        instructions: QuantumCircuitData = circuit.data
        clbits_count = len(circuit.clbits)
        qubits_count = len(circuit.qubits)
        new_clreg = ClassicalRegister(clbits_count, name="clbits")
        new_qreg = QuantumRegister(qubits_count, name="qubits")

        clbit_map = {}
        qubit_map = {}

        for i, clbit in enumerate(circuit.clbits):
            clbit_map[clbit._register.name] = i

        for i, qubit in enumerate(circuit.qubits):
            qubit_map[qubit._register.name] = i

        inst: CircuitInstruction
        new_instructions = []

        for inst in instructions:
            clbit_names = [clbit._register.name for clbit in inst.clbits]
            new_clbits = [new_clreg[clbit_map[name]] for name in clbit_names]

            qubit_names = [qubit._register.name for qubit in inst.qubits]
            new_qubits = [new_qreg[qubit_map[name]] for name in qubit_names]

            new_instructions.append(
                CircuitInstruction(clbits=tuple(new_clbits), operation=inst.operation, qubits=tuple(new_qubits))
            )

        new_circuit = QiskitCircuit.from_instructions(
            new_instructions, qubits=[reg for reg in new_qreg], clbits=[reg for reg in new_clreg]
        )

        return new_circuit
