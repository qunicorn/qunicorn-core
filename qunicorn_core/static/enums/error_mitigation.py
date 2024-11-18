# Copyright 2024 University of Stuttgart.
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

from enum import StrEnum


class ErrorMitigationMethod(StrEnum):
    """
    Enum to select the error mitigation method
    """

    none = "none"
    dynamical_decoupling = "dynamical_decoupling"
    pauli_twirling = "pauli_twirling"
    twirled_readout_error_extinction = "twirled_readout_error_extinction"
    zero_noise_extrapolation = "zero_noise_extrapolation"
    probabilistic_error_amplification = "probabilistic_error_amplification"
    probabilistic_error_cancellation = "probabilistic_error_cancellation"
