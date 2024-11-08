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

from functools import partial
from math import ceil
from typing import Any, List, Optional, Sequence, Tuple

from flask import current_app

from qunicorn_core.celery import CELERY
from qunicorn_core.core.circuit_cutting_service import cut_circuit
from qunicorn_core.core.mapper import result_mapper
from qunicorn_core.core.pilotmanager import pilot_manager
from qunicorn_core.core.pilotmanager.base_pilot import Pilot, PilotJob
from qunicorn_core.core.transpiler import transpile_circuit, TranspilationError
from qunicorn_core.db.db import DB
from qunicorn_core.db.models.job import JobDataclass
from qunicorn_core.db.models.job_state import TransientJobStateDataclass
from qunicorn_core.db.models.quantum_program import QuantumProgramDataclass, TranslatedProgramDataclass
from qunicorn_core.db.models.result import ResultDataclass
from qunicorn_core.static.enums.job_state import JobState
from qunicorn_core.static.qunicorn_exception import QunicornError

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

        token = job.get_transient_state_key("token", None)

        # Transpile and Run the Job on the correct provider
        pilot: Pilot = pilot_manager.get_matching_pilot(device.provider.name)
        pilot_jobs = _prepare_pilot_jobs(job, pilot.supported_languages)

        current_app.logger.info(f"Run job with id {job_id} on {pilot.__class__}")
        pilot.execute(pilot_jobs, token=token)

    except Exception as err:
        if isinstance(err, QunicornError) and err.data.get("message", "").startswith("Transpilation Error"):
            # transpilation has already saved the errors for the job, nothing to do
            raise err
        for transient_state in job._transient:
            transient_state.delete()
        job.save_error(err)
        raise err


def _prepare_pilot_jobs(job: JobDataclass, dest_languages: Sequence[str]) -> Sequence[PilotJob]:
    max_qubits = job.cut_to_width
    try_circuit_cutting = max_qubits is not None
    circuit_cutting_service: Optional[str] = current_app.config.get("CIRCUIT_CUTTING_URL", None)
    if try_circuit_cutting and not isinstance(circuit_cutting_service, str):
        raise QunicornError("This Qunicorn instance is not configured to support circuit cutting!")

    pilot_jobs: List[PilotJob] = []

    programs = job.deployment.programs if job.deployment else []

    for program in programs:
        if program.quantum_circuit is None:
            continue  # skip empty programs

        cutting_params: Optional[dict] = None

        if try_circuit_cutting:
            cutting_params = _get_circuit_cutting_params(program, max_qubits)

        if cutting_params is not None:
            assert isinstance(circuit_cutting_service, str)
            pilot_jobs.extend(_cut_circuit(job, program, circuit_cutting_service, cutting_params, dest_languages))
        else:
            circuit = program.quantum_circuit
            source_format = program.assembler_language
            if not circuit:
                continue  # skip empty programs
            if not source_format:
                # no sourceformat specified, try circuit as is
                pilot_jobs.append(PilotJob(circuit, job, program, None))
                continue
            pilot_jobs.extend(
                _transpile_circuit(
                    job=job, program=program, circuit=(source_format, circuit, 0), dest_languages=dest_languages
                )
            )

    DB.session.commit()

    return pilot_jobs


def _persist_translation(
    assembler_language: str, quantum_circuit: Any, translation_distance: int, program: QuantumProgramDataclass
):
    if isinstance(quantum_circuit, (str, bytes)):
        # circuit is in a format that can be safely stored in the database
        if any(t.assembler_language == assembler_language for t in program.translations):
            return  # already persisted
        is_string = isinstance(quantum_circuit, str)
        if is_string:
            quantum_circuit = quantum_circuit.encode()
        translated = TranslatedProgramDataclass(
            quantum_circuit=quantum_circuit,
            is_string=is_string,
            assembler_language=assembler_language,
            translation_distance=translation_distance,
            program=program,
        )
        translated.save(commit=True)


def _get_circuit_cutting_params(program: QuantumProgramDataclass, max_qubits: int):  # noqa: C901
    if max_qubits < 1:
        raise QunicornError(f"The maximum width of a cut circuit must allow for at least one Qubit! (got {max_qubits})")

    src_language: Optional[str] = program.assembler_language

    if src_language is None:
        # source language is not known, try circuit as is (without cutting)
        return

    config = current_app.config

    existing_translations = [(t.assembler_language, t.circuit, t.translation_distance) for t in program.translations]

    try:
        transpiled_qiskit = transpile_circuit(
            "QISKIT",
            (src_language, program.quantum_circuit, 0),
            *existing_translations,
            exclude=config.get("EXCLUDE_TRANSPILERS", None),
            exclude_formats=config.get("EXCLUDE_FORMATS", None),
            exclude_unsafe=config.get("EXCLUDE_UNSAFE_TRANSPILERS", True),
            visitor=partial(_persist_translation, program=program),
        )
    except (KeyError, TranspilationError):
        raise QunicornError(
            "Failed to inspect circuit for cutting."
            f" Circuit format {src_language} could not be transpiled into the required format for inspection."
        )

    num_qubits: int = transpiled_qiskit.num_qubits

    if num_qubits <= max_qubits:
        return

    max_circuits: int = ceil(num_qubits / max_qubits)
    max_allowed_cuts: int = {2: 3, 3: 6, 4: 10}.get(max_circuits, 10)

    if max_circuits > 4:
        raise QunicornError("Qunicorn only supports cutting circuits into at most 4 smaller circuits!")

    existing_translations = [(t.assembler_language, t.circuit, t.translation_distance) for t in program.translations]

    for target in ("QASM2", "QASM3"):
        try:
            transpiled_circuit = transpile_circuit(
                target,
                (src_language, program.quantum_circuit, 0),
                *existing_translations,
                exclude=config.get("EXCLUDE_TRANSPILERS", None),
                exclude_formats=config.get("EXCLUDE_FORMATS", None),
                exclude_unsafe=config.get("EXCLUDE_UNSAFE_TRANSPILERS", True),
                visitor=partial(_persist_translation, program=program),
            )
            return {
                "circuit": transpiled_circuit,
                "method": "automatic",
                "max_subcircuit_width": max_qubits,
                "max_num_subcircuits": max_circuits,
                "max_cuts": max_allowed_cuts,
                "circuit_format": "openqasm2" if target == "QASM2" else "openqasm3",
            }
        except KeyError:
            pass  # did not find a valid transpiler chain
        except TranspilationError as err:
            raise QunicornError(f"Transpilation to {target} format failed!") from (
                err.__cause__ if err.__cause__ else err
            )

    raise QunicornError("Failed to transpile circuit into a format required for cutting!")


def _cut_circuit(
    job: JobDataclass,
    program: QuantumProgramDataclass,
    circuit_cutting_service: str,
    cutting_params: dict,
    dest_languages: Sequence[str],
) -> Sequence[PilotJob]:
    pilot_jobs: List[PilotJob] = []

    try:
        cut_data = cut_circuit(cutting_params, circuit_cutting_service)
    except Exception as err:
        raise QunicornError("Failed to cut circuit.") from err

    cut_state = TransientJobStateDataclass(
        job=job,
        program=program,
        data={
            "type": "CUT_CIRCUIT",
            "origninal_circuit": cutting_params["circuit"],
            "circuit_format": cutting_params["circuit_format"],
            "cut_data": cut_data,
            "circuit_fragment_ids": [i for i in range(len(cut_data["individual_subcircuits"]))],
        },
    )
    cut_state.save()

    source_format = "QASM2" if cutting_params["circuit_format"] == "openqasm2" else "QASM3"

    for circuit_fragment_id, circuit in cut_data["individual_subcircuits"]:
        pilot_jobs.extend(
            _transpile_circuit(
                job=job,
                program=program,
                circuit_fragment_id=circuit_fragment_id,
                circuit=(source_format, circuit, 0),
                dest_languages=dest_languages,
            )
        )

    return pilot_jobs


def _transpile_circuit(  # noqa: C901
    job: JobDataclass,
    program: QuantumProgramDataclass,
    circuit: Tuple[str, Any, int],
    dest_languages: Sequence[str],
    circuit_fragment_id: Optional[int] = None,
) -> Sequence[PilotJob]:
    """Transforms all circuits of the deployment into the circuits in the destination language"""
    current_app.logger.info(f"Transpile all circuits of job with id {job.id}")
    error_results: list[ResultDataclass] = []

    if job.deployment is None:
        return []

    config = current_app.config

    pilot_jobs: List[PilotJob] = []

    existing_translations = [(t.assembler_language, t.circuit, t.translation_distance) for t in program.translations]

    try:
        # Preprocess a string to a circuit object if necessary
        last_error = None
        for target in dest_languages:
            try:
                transpiled_circuit = transpile_circuit(
                    target,
                    circuit,
                    *existing_translations,
                    exclude=config.get("EXCLUDE_TRANSPILERS", None),
                    exclude_formats=config.get("EXCLUDE_FORMATS", None),
                    exclude_unsafe=config.get("EXCLUDE_UNSAFE_TRANSPILERS", True),
                    visitor=partial(_persist_translation, program=program),
                )
                pilot_jobs.append(
                    PilotJob(
                        circuit=transpiled_circuit, job=job, program=program, circuit_fragment_id=circuit_fragment_id
                    )
                )
                break  # break inner loop after first successfull transpilation
            except KeyError:
                pass  # did not find a valid transpiler chain
            except TranspilationError as err:
                last_error = err.__cause__ if err.__cause__ else err
        else:
            if last_error:
                raise last_error
            else:
                raise Exception(f"No transpiler chain found from {circuit[0]} to any of {dest_languages}")
    except Exception as exception:
        error_results.extend(result_mapper.exception_to_error_results(exception, program))

    # If an error was caught -> Update the job and raise it again
    if len(error_results) > 0:
        job.save_results(error_results, JobState.ERROR)
        string_errors = " ".join(str(error.data.get("exception_message", "")) for error in error_results)
        if string_errors:
            raise QunicornError("Transpilation Error: " + string_errors)

    return pilot_jobs


def cancel_job(job: JobDataclass, token: Optional[str], user_id: Optional[str]):
    """Check which pilot was used to execute the job and then cancel it there"""
    pilot: Pilot = pilot_manager.get_matching_pilot(job.executed_on.provider.name)
    pilot.cancel(job.id, user_id=user_id, token=token)
