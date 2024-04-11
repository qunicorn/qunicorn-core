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

from heapq import heappush, heappop
from typing import ClassVar, Any, Sequence, Callable, Union


class CircuitTranspiler:

    __known_formats: set[str] = set()
    __transpilers: dict[str, list["CircuitTranspiler"]] = {}

    source: ClassVar[str] = ""
    target: ClassVar[str] = ""
    cost: ClassVar[int] = 1

    def __init_subclass__(cls, source: str, target: str, cost: int = 1) -> None:
        cls.source = source
        cls.target = target
        cls.cost = cost
        CircuitTranspiler.__known_formats.add(source)
        CircuitTranspiler.__known_formats.add(target)
        CircuitTranspiler.__transpilers.setdefault(source, []).append(cls())

    def transpile_circuit(self, circuit: Any) -> Any:
        raise NotImplementedError()

    @staticmethod
    def get_known_formats() -> set[str]:
        return CircuitTranspiler.__known_formats.copy()

    @staticmethod
    def get_transpilers(source: str) -> Sequence["CircuitTranspiler"]:
        try:
            return tuple(CircuitTranspiler.__transpilers[source])
        except KeyError:
            if source in CircuitTranspiler.__known_formats:
                return tuple()  # format is known, but no transpiler for it exists
            raise KeyError(f"'{source}' is an unknown circuit format!")

    @staticmethod
    def _get_transpiler_chain(
        source: Union[str, Sequence[str]], target: str, cost: Callable[["CircuitTranspiler"], int]
    ) -> Sequence["CircuitTranspiler"]:
        frontier: list[tuple[int, str, tuple[CircuitTranspiler, ...]]] = []

        if isinstance(source, str):
            heappush(frontier, (0, source, tuple()))
        else:
            # Start search from multiple starting points at the same time
            # e.g., when multiple source formats are available
            for s in source:
                heappush(frontier, (0, s, tuple()))

        # longest possible translator chain length
        max_len = len(CircuitTranspiler.__known_formats)

        # A* using a heap with "cost" as the heuristic
        while frontier:
            current = heappop(frontier)
            if current[1] == target:
                return current[2]
            if len(current[2]) >= max_len:
                continue  # a translator chain cannot be longer than the max linear chain
            transpilers: Sequence["CircuitTranspiler"] = CircuitTranspiler.__transpilers.get(current[1], tuple())
            for transpiler in transpilers:
                if transpiler in current[2]:
                    continue  # transpiler was already used in this chain
                heappush(frontier, (current[0] + cost(transpiler), transpiler.target, (*current[2], transpiler)))

        raise KeyError(f"There is no transpilation path from '{source}' to '{target}'.")

    @staticmethod
    def get_transpilers_limit_depth(source: Union[str, Sequence[str]], target: str) -> Sequence["CircuitTranspiler"]:
        return CircuitTranspiler._get_transpiler_chain(source, target, cost=lambda x: 1)

    @staticmethod
    def get_transpilers_limit_cost(source: Union[str, Sequence[str]], target: str) -> Sequence["CircuitTranspiler"]:
        return CircuitTranspiler._get_transpiler_chain(source, target, cost=lambda x: x.cost)


def transpile_circuit(target: str, *circuit: tuple[str, Any]) -> Any:
    if len(circuit) == 0:
        raise ValueError("Must provide a circuit to compile!")
    elif len(circuit) == 1:
        source_format = circuit[0][0]
    else:
        source_format = [c[0] for c in circuit]

    for source, c in circuit:
        if source == target:
            # return fast if target format is already available
            return c

    transpiler_chain = CircuitTranspiler.get_transpilers_limit_depth(source=source_format, target=target)

    assert len(transpiler_chain) > 0, "There should always be at least one transpiler present."

    # get the format the transpiler chain starts with
    first_circuit_format = transpiler_chain[0].source if transpiler_chain else target

    current_circuit = next(c for s, c in circuit if s == first_circuit_format)

    for transpiler in transpiler_chain:
        current_circuit = transpiler.transpile_circuit(current_circuit)

        if isinstance(current_circuit, (str, bytes)):
            # circuit is in a format that can be safely stored in the database
            pass  # TODO implement persistence

    return current_circuit
