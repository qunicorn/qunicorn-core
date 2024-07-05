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

from typing import Any, List, Optional, Sequence, Tuple

from flask import current_app

from qunicorn_core.celery import CELERY
from qunicorn_core.core.mapper import result_mapper
from qunicorn_core.core.pilotmanager import pilot_manager
from qunicorn_core.core.pilotmanager.base_pilot import Pilot
from qunicorn_core.core.transpiler import transpile_circuit, TranspilationError
from qunicorn_core.db.models.job import JobDataclass
from qunicorn_core.db.models.quantum_program import QuantumProgramDataclass
from qunicorn_core.db.models.result import ResultDataclass
from qunicorn_core.static.enums.job_state import JobState
from qunicorn_core.static.qunicorn_exception import QunicornError
from qunicorn_core.util import logging

"""This Class is responsible for running a job on a pilot and scheduling them with celery"""


@CELERY.task()
def run_job(job_id: int):
    """Assign the job to the target pilot which executes the job"""
    job = JobDataclass.get_by_id(job_id)
    if job is None:
        raise QunicornError(f"Could not execute job with id '{job_id}'. Did not find job in database!")
    job.state = JobState.RUNNING.value
    job.save(commit=True)

    try:
        device = job.executed_on

        if not device or not device.provider:
            raise QunicornError(
                f"Job '{job_id}' has no valid device specified. (No device specified or device is missing a provider.)"
            )

        token = job.get_transient_state("token", None)

        # Transpile and Run the Job on the correct provider
        pilot: Pilot = pilot_manager.get_matching_pilot(device.provider.name)
        circuits = _transpile_circuits(job, pilot.supported_languages)

        logging.info(f"Run job with id {job_id} on {pilot.__class__}")
        pilot.execute(job, circuits, token=token)

    except Exception as err:
        for transient_state in job._transient:
            transient_state.delete()
        job.save_error(err)
        raise err


def _transpile_circuits(  # noqa: C901
    job: JobDataclass, dest_languages: Sequence[str]
) -> Sequence[Tuple[QuantumProgramDataclass, Any]]:
    """Transforms all circuits of the deployment into the circuits in the destination language"""
    logging.info(f"Transpile all circuits of job with id{job.id}")
    error_results: list[ResultDataclass] = []

    if job.deployment is None:
        return []

    config = current_app.config

    transpiled_circuits: List[Tuple[QuantumProgramDataclass, Any]] = []

    # Transform each circuit into a transpiled circuit for the necessary language
    for program in job.deployment.programs:
        if program.quantum_circuit is None:
            continue  # skip empty programs
        src_language: Optional[str] = program.assembler_language

        if src_language is None:
            # source language is not known, try circuit as is
            transpiled_circuits.append((program, program.quantum_circuit))
            continue

        try:
            # Preprocess a string to a circuit object if necessary
            last_error = None
            for target in dest_languages:
                try:
                    circuit = transpile_circuit(
                        target,
                        (src_language, program.quantum_circuit),
                        exclude=config.get("EXCLUDE_TRANSPILERS", None),
                        exclude_formats=config.get("EXCLUDE_FORMATS", None),
                        exclude_unsafe=config.get("EXCLUDE_UNSAFE_TRANSPILERS", True),
                    )
                    transpiled_circuits.append((program, circuit))
                    break  # break inner loop after first successfull transpilation
                except KeyError:
                    pass  # did not find a valid transpiler chain
                except TranspilationError as err:
                    last_error = err.__cause__ if err.__cause__ else err
            else:
                if last_error:
                    raise last_error
                else:
                    raise Exception(f"No transpiler chain found from {src_language} to any of {dest_languages}")
        except Exception as exception:
            error_results.extend(result_mapper.exception_to_error_results(exception, program))

    # If an error was caught -> Update the job and raise it again
    if len(error_results) > 0:
        job.save_results(error_results, JobState.ERROR)
        string_errors = " ".join(str(error.result_dict.get("exception_message", "")) for error in error_results)
        if string_errors:
            raise QunicornError("Transpilation Error: " + string_errors)

    return transpiled_circuits


def cancel_job(job: JobDataclass, token: Optional[str], user_id: Optional[str]):
    """Check which pilot was used to execute the job and then cancel it there"""
    pilot: Pilot = pilot_manager.get_matching_pilot(job.executed_on.provider.name)
    pilot.cancel(job.id, user_id=user_id, token=token)
