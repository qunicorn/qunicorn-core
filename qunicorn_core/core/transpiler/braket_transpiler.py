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

from braket.circuits import Circuit
from braket.circuits.serialization import IRType
from braket.ir.openqasm.program_v1 import Program as Qasm3Program

from .circuit_transpiler import CircuitTranspiler


class Qasm3ToBraket(CircuitTranspiler, source="QASM3", target="BRAKET", cost=2):

    def transpile_circuit(self, circuit: Any) -> Circuit:
        assert isinstance(circuit, str)

        circuit = circuit.replace("\r\n", "\n")

        # remove stdgates.inc import to avoid FileNotFoundError
        circuit = circuit.replace('include "stdgates.inc";', "")

        return Circuit.from_ir(circuit)


class BraketToQasm3(CircuitTranspiler, source="BRAKET", target="QASM3", cost=2):

    def transpile_circuit(self, circuit: Any) -> str:
        assert isinstance(circuit, Circuit)

        qasm = circuit.to_ir(IRType.OPENQASM)

        assert isinstance(qasm, Qasm3Program)

        qasm_str = qasm.source

        qasm_str = qasm_str.replace("OPENQASM 3.0;", 'OPENQASM 3;\ninclude "stdgates.inc";', 1)

        return qasm_str
