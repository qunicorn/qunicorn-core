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

import re
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

        # replace cx with cnot gates and ccx with ccnot gates
        # TODO remove workaround once no longer required!
        circuit = re.sub(
            (
                r"^\s*cx(\s+"  # cx
                r"[a-zA-Z0-9_]+(?:\[[0-9]+\])?\s*,\s+"  # control qubit
                r"[a-zA-Z0-9_]+(?:\[[0-9]+\])?;)"  # target qubit
            ),
            r"cnot\1",
            circuit,
            flags=re.MULTILINE,
        )
        circuit = re.sub(
            (
                r"^\s*ccx(\s+"  # ccx
                r"[a-zA-Z0-9_]+(?:\[[0-9]+\])?\s*,\s+"  # first control qubit
                r"[a-zA-Z0-9_]+(?:\[[0-9]+\])?\s*,\s+"  # second control qubit
                r"[a-zA-Z0-9_]+(?:\[[0-9]+\])?;)"  # target qubit
            ),
            r"ccnot\1",
            circuit,
            flags=re.MULTILINE,
        )

        return Circuit.from_ir(circuit)


class BraketToQasm3(CircuitTranspiler, source="BRAKET", target="QASM3", cost=2):

    def transpile_circuit(self, circuit: Any) -> str:
        assert isinstance(circuit, Circuit)

        qasm = circuit.to_ir(IRType.OPENQASM)

        assert isinstance(qasm, Qasm3Program)

        qasm_str = qasm.source

        qasm_str = qasm_str.replace("OPENQASM 3.0;", 'OPENQASM 3.0;\ninclude "stdgates.inc";', 1)

        # replace cnot with cx gates and ccnot with ccx gates
        # TODO remove workaround once no longer required!
        qasm_str = re.sub(
            (
                r"^\s*cnot(\s+"  # cnot
                r"[a-zA-Z0-9_]+(?:\[[0-9]+\])?\s*,\s+"  # control qubit
                r"[a-zA-Z0-9_]+(?:\[[0-9]+\])?;)"  # target qubit
            ),
            r"cx\1",
            qasm_str,
            flags=re.MULTILINE,
        )
        qasm_str = re.sub(
            (
                r"^\s*ccnot(\s+"  # ccnot
                r"[a-zA-Z0-9_]+(?:\[[0-9]+\])?\s*,\s+"  # first control qubit
                r"[a-zA-Z0-9_]+(?:\[[0-9]+\])?\s*,\s+"  # second control qubit
                r"[a-zA-Z0-9_]+(?:\[[0-9]+\])?;)"  # target qubit
            ),
            r"ccx\1",
            qasm_str,
            flags=re.MULTILINE,
        )

        return qasm_str
