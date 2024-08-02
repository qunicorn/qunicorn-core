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

from io import BytesIO
from typing import Any


from qiskit import QuantumCircuit, qpy
from qiskit.qasm2 import loads as loads2, dumps as dumps2, LEGACY_CUSTOM_INSTRUCTIONS
from qiskit.qasm2.exceptions import QASM2ParseError
from qiskit.qasm3 import loads as loads3, dumps as dumps3

from .circuit_transpiler import CircuitTranspiler


class Qasm2ToQiskit(CircuitTranspiler, source="QASM2", target="QISKIT", cost=1):

    def transpile_circuit(self, circuit: Any) -> QuantumCircuit:
        assert isinstance(circuit, str)
        try:
            return loads2(circuit)
        except QASM2ParseError:
            return loads2(circuit, custom_instructions=LEGACY_CUSTOM_INSTRUCTIONS)


class QiskitToQasm2(CircuitTranspiler, source="QISKIT", target="QASM2", cost=1):

    def transpile_circuit(self, circuit: Any) -> str:
        assert isinstance(circuit, QuantumCircuit)
        converted = dumps2(circuit)
        assert converted is not None
        return converted


class Qasm3ToQiskit(CircuitTranspiler, source="QASM3", target="QISKIT", cost=1):

    def transpile_circuit(self, circuit: Any) -> QuantumCircuit:
        assert isinstance(circuit, str)
        return loads3(circuit)


class QiskitToQasm3(CircuitTranspiler, source="QISKIT", target="QASM3", cost=1):

    def transpile_circuit(self, circuit: Any) -> str:
        assert isinstance(circuit, QuantumCircuit)
        return dumps3(circuit)


class QPYToQiskit(CircuitTranspiler, source="QPY", target="QISKIT", cost=1):

    def transpile_circuit(self, circuit: Any) -> QuantumCircuit:
        assert isinstance(circuit, bytes)
        programs = qpy.load(BytesIO(circuit))
        assert len(programs) == 1
        converted = programs[0]
        if not isinstance(converted, QuantumCircuit):
            raise ValueError(
                f"Only QunatumCircuit objects are supported for QPY deserialization. Got '{type(converted)}'."
            )
        return converted


class QiskitToQPY(CircuitTranspiler, source="QISKIT", target="QPY", cost=1):

    def transpile_circuit(self, circuit: Any) -> bytes:
        assert isinstance(circuit, QuantumCircuit)
        dummy_io = BytesIO()
        qpy.dump(circuit, dummy_io)
        dummy_io.seek(0)
        converted = dummy_io.getvalue()
        return converted
