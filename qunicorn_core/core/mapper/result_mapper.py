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
from qiskit.primitives import EstimatorResult, SamplerResult
from qiskit.result import Result

from qunicorn_core.api.api_models import JobCoreDto
from qunicorn_core.db.models.result import ResultDataclass
from qunicorn_core.static.enums.result_type import ResultType


def runner_result_to_db_results(ibm_result: Result, job_dto: JobCoreDto) -> list[ResultDataclass]:
    result_dto_list: list[ResultDataclass] = []
    for i in range(len(ibm_result.get_counts())):
        counts: dict = ibm_result.get_counts()[i]
        circuit: str = job_dto.deployment.program_list[i].quantum_circuit
        result_dto_list.append(
            ResultDataclass(circuit=circuit, result_dict=counts, result_type=ResultType.COUNTS, meta_data=ibm_result.results[i].to_dict())
        )
    return result_dto_list


def estimator_result_to_db_results(ibm_result: EstimatorResult, job: JobCoreDto, observer: str) -> list[ResultDataclass]:
    result_dto_list: list[ResultDataclass] = []
    for i in range(ibm_result.num_experiments):
        value: float = ibm_result.values[i]
        variance: float = ibm_result.metadata[i]["variance"]
        circuit: str = job.deployment.program_list[i].quantum_circuit
        result_dto_list.append(
            ResultDataclass(
                circuit=circuit,
                result_dict={"value": str(value), "variance": str(variance)},
                result_type=ResultType.VALUE_AND_VARIANCE,
                meta_data={"observer": f"SparsePauliOp-{observer}"},
            )
        )
    return result_dto_list


def sampler_result_to_db_results(ibm_result: SamplerResult, job_dto: JobCoreDto) -> list[ResultDataclass]:
    result_dto_list: list[ResultDataclass] = []
    for i in range(ibm_result.num_experiments):
        quasi_dist: dict = ibm_result.quasi_dists[i]
        circuit: str = job_dto.deployment.program_list[i].quantum_circuit
        result_dto_list.append(
            ResultDataclass(
                circuit=circuit,
                result_dict=quasi_dist,
                result_type=ResultType.QUASI_DIST,
            )
        )
    return result_dto_list