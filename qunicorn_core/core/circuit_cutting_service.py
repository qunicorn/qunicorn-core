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


from urllib.parse import urljoin
from typing import Optional, List, Dict, Sequence

from flask.globals import current_app
from requests import post


def cut_circuit(cutting_params: dict, circuit_cutting_service: Optional[str] = None) -> dict:
    if circuit_cutting_service is None:
        circuit_cutting_service = current_app.config.get("CIRCUIT_CUTTING_URL", None)
    if circuit_cutting_service is None:
        raise ValueError("URL for circuit cutting service must not be None!")

    cut_result = post(urljoin(circuit_cutting_service, "/cutCircuits"), json=cutting_params, timeout=300)
    cut_result.raise_for_status()
    return cut_result.json()


def prepare_results(fragment_results: Dict[int, List[dict]], circuit_fragment_ids: Sequence[int]) -> List[List[float]]:
    """Prepares qunicorn style subcircuit results in the format required for combining results with the cutting service.

    The results for the cutting service are a probability distribution over all possible measurements.
    Probabilities are stored as a list, where the list index corresponds to the measurement
    (i.e. ``0b00`` = ``l[0]`` and ``0b10`` = ``l[2]``).
    """
    subcircuit_results: List[List[float]] = []
    # FIXME implement this
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
    return combined_result.json()
