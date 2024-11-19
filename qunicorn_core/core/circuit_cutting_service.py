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
from collections import Counter
from random import choices
from urllib.parse import urljoin
from typing import Optional, List, Dict, Sequence, Tuple

from flask.globals import current_app
from requests import post

from qunicorn_core.static.enums.result_type import ResultType
from qunicorn_core.static.qunicorn_exception import QunicornError
from qunicorn_core.util import utils


def cut_circuit(cutting_params: dict, circuit_cutting_service: Optional[str] = None) -> dict:
    if circuit_cutting_service is None:
        circuit_cutting_service = current_app.config.get("CIRCUIT_CUTTING_URL", None)
    if circuit_cutting_service is None:
        raise ValueError("URL for circuit cutting service must not be None!")

    cut_result = post(urljoin(circuit_cutting_service, "/cutCircuits"), json=cutting_params, timeout=300)
    cut_result.raise_for_status()
    return cut_result.json()


def prepare_results_for_combination(
    fragment_results: Dict[int, List[dict]], circuit_fragment_ids: Sequence[int]
) -> List[List[float]]:
    """Prepares qunicorn style subcircuit results in the format required for combining results with the cutting service.

    The results for the cutting service are a probability distribution over all possible measurements.
    Probabilities are stored as a list, where the list index corresponds to the measurement
    (i.e. ``0b00`` = ``l[0]`` and ``0b10`` = ``l[2]``).
    """
    subcircuit_results: List[List[float]] = []

    for fragment_id in circuit_fragment_ids:
        fragment_sub_results = fragment_results[fragment_id]

        for job_result in fragment_sub_results:  # PilotJobResult as dictionary
            result_type: ResultType = ResultType(job_result["result_type"])

            if result_type == ResultType.COUNTS:
                probabilities = utils.calculate_probabilities(job_result["data"])
            elif result_type == ResultType.PROBABILITIES:
                probabilities = job_result["data"]
            else:
                continue

            measurement_format = job_result["meta"]["format"]

            if measurement_format == "bin":
                base = 2
                arbitrary_measurement_key: str = next(iter(probabilities.keys()))

                if arbitrary_measurement_key.startswith("0b"):
                    qubit_count = len(arbitrary_measurement_key) - 2
                else:
                    qubit_count = len(arbitrary_measurement_key)
            elif measurement_format == "hex":
                base = 16
                qubit_count = 0

                for register in job_result["meta"]["registers"]:
                    qubit_count += register["size"]
            else:
                raise QunicornError(f"unknown measurement format {measurement_format}")

            cutting_format = [0.0 for _ in range(2**qubit_count)]

            for measurement, count in probabilities.items():
                cutting_format[int(measurement, base)] = count

            subcircuit_results.append(cutting_format)
            break

        # TODO: if no supported result type...

    return subcircuit_results


def combine_results(
    results: List[List[float]],
    cut_data: dict,
    original_circuit: str,
    circuit_format: str,
    circuit_cutting_service: Optional[str] = None,
):
    if circuit_cutting_service is None:
        circuit_cutting_service = current_app.config.get("CIRCUIT_CUTTING_URL", None)
    if circuit_cutting_service is None:
        raise ValueError("URL for circuit cutting service must not be None!")
    data = {
        "circuit": original_circuit,
        "subcircuit_results": results,
        "cuts": {
            "max_subcircuit_width": cut_data["max_subcircuit_width"],
            "subcircuits": cut_data["subcircuits"],
            "complete_path_map": cut_data["complete_path_map"],
            "num_cuts": cut_data["num_cuts"],
            "counter": cut_data["counter"],
            "classical_cost": cut_data["classical_cost"],
            "individual_subcircuits": cut_data["individual_subcircuits"],
            "init_meas_subcircuit_map": cut_data["init_meas_subcircuit_map"],
        },
        "circuit_format": circuit_format,
        # "unnormalized_results": "True",
        # "shot_scaling_factor": 100,
    }
    combined_result = post(urljoin(circuit_cutting_service, "/combineResults"), json=data)
    combined_result.raise_for_status()
    return combined_result.json()["result"]


def prepare_combined_results(
    results: List[float], shots: int, registers: List[Dict]
) -> List[Tuple[Dict, Dict, ResultType]]:
    print(results)
    counts: Dict[int, int] = dict(Counter(choices(list(range(len(results))), results, k=shots)))
    counts_hex = {hex(k): v for k, v in counts.items()}
    counts_metadata = {"format": "hex", "shots": shots, "registers": registers}

    probabilities = {hex(k): v for k, v in enumerate(results)}
    probability_metadata = {"format": "hex", "shots": shots, "registers": registers}

    return [
        (counts_hex, counts_metadata, ResultType.COUNTS),
        (probabilities, probability_metadata, ResultType.PROBABILITIES),
    ]
