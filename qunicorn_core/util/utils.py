# Copyright 2023 University of Stuttgart
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
import os

from qiskit import QuantumCircuit
from qiskit.qasm2 import dumps as dumps2


def get_default_qasm2_string(hadamard_amount: int = 1) -> str:
    qc = QuantumCircuit(2)
    for _ in range(hadamard_amount):
        qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()
    return dumps2(qc)


def calculate_probabilities(counts: dict) -> dict:
    """Calculates the probabilities from the counts, probability = counts / total_counts"""

    total_counts = sum(counts.values())
    probabilities = {}
    for key, value in counts.items():
        probabilities[key] = value / total_counts
    return probabilities


def is_experimental_feature_enabled() -> bool:
    return os.environ.get("ENABLE_EXPERIMENTAL_FEATURES") == "True"


def is_running_in_docker() -> bool:
    return os.environ.get("RUNNING_IN_DOCKER", "") == "True"


def is_running_asynchronously() -> bool:
    return os.environ.get("EXECUTE_CELERY_TASK_ASYNCHRONOUS") == "True"
