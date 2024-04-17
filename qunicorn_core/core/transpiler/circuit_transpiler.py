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
from typing import ClassVar, Any, Sequence, Callable, Union, Optional, Type, cast


class TranspilationError(Exception):
    """Base error for all transpilation failures."""

    def __init__(self, transpiler: "CircuitTranspiler", circuit: Any, *args: object) -> None:
        super().__init__(transpiler, circuit, *args)
        self.transpiler = transpiler
        self.circuit = circuit


class CircuitTranspiler:
    """Base class for all circuit transpilers.

    To create a new transpiler, inherit from this class and implement the :py:meth:`CircuitTranspiler.transpile_circuit` method.

    Example:

    .. code-block:: python

        class DemoTranspiler(CircuitTranspiler, source="source-format", target="target-format", cost=1):
            unsafe = False  # set to True if transpilation may execute unsafe code

            def transpile_circuit(self, circuit: Any) -> Any:
                ...
    """

    __known_formats: set[str] = set()
    __transpilers: dict[str, list["CircuitTranspiler"]] = {}

    source: ClassVar[str] = ""
    target: ClassVar[str] = ""
    cost: ClassVar[int] = 1
    unsafe: ClassVar[bool] = False

    def __init_subclass__(cls, source: str, target: str, cost: int = 1) -> None:
        cls.source = source
        cls.target = target
        cls.cost = cost
        CircuitTranspiler.__known_formats.add(source)
        CircuitTranspiler.__known_formats.add(target)
        CircuitTranspiler.__transpilers.setdefault(source, []).append(cls())

    def transpile_circuit(self, circuit: Any) -> Any:
        """Transpile the given circuit to the target format."""
        raise NotImplementedError()

    @staticmethod
    def get_known_formats() -> set[str]:
        """Get all known formats (i.e., set(target_formats) + set(source_formats))."""
        return CircuitTranspiler.__known_formats.copy()

    @staticmethod
    def get_transpilers(source: str) -> Sequence["CircuitTranspiler"]:
        """Get all transpilers registered for a specific source format.

        Raises:
            KeyError: If the source format is not a known format.

        Returns:
            Sequence[CircuitTranspiler]: all circuit transpilers registered for this source format (may be empty)
        """
        try:
            return tuple(CircuitTranspiler.__transpilers[source])
        except KeyError:
            if source in CircuitTranspiler.__known_formats:
                return tuple()  # format is known, but no transpiler for it exists
            raise KeyError(f"'{source}' is an unknown circuit format!")

    @staticmethod
    def _get_transpiler_chain(
        source: Union[str, Sequence[str]],
        target: str,
        *,
        cost: Callable[["CircuitTranspiler"], float],
        exclude: Optional[set[Union[str, Type["CircuitTranspiler"]]]] = None,
        exclude_formats: Optional[set[str]] = None,
        exclude_unsafe: bool = False,
    ) -> Sequence["CircuitTranspiler"]:
        """Get a list of transpilers from source to target minimizing overall transpilation cost."""
        if exclude_formats and target in exclude_formats:
            raise ValueError("Cannot transpile to an excluded target format!")
        frontier: list[tuple[float, str, tuple[CircuitTranspiler, ...]]] = []

        if isinstance(source, str):
            if not exclude_formats or source not in exclude_formats:
                heappush(frontier, (0, source, tuple()))
        else:
            # Start search from multiple starting points at the same time
            # e.g., when multiple source formats are available
            for s in source:
                if not exclude_formats or s not in exclude_formats:
                    heappush(frontier, (0, s, tuple()))

        if not frontier:
            # frontier is empty because all source formats are excluded formats
            raise ValueError("Cannot transpile from an excluded source format!")

        # longest possible transpiler chain length
        max_len = len(CircuitTranspiler.__known_formats)

        # A* using a heap with "cost" as the heuristic
        while frontier:
            current = heappop(frontier)

            # check for solution
            if current[1] == target:
                return current[2]

            # expand frontier
            if len(current[2]) >= max_len:
                continue  # a transpiler chain cannot be longer than the max linear chain
            transpilers = cast(Sequence["CircuitTranspiler"], CircuitTranspiler.__transpilers.get(current[1], tuple()))
            for transpiler in transpilers:
                if exclude_unsafe and transpiler.unsafe:
                    continue  # transpiler is not safe, i.e., may execute arbitrary code
                if exclude_formats and transpiler.target in exclude_formats:
                    continue  # format is excluded from transpilation
                if exclude:
                    t_class = type(transpiler)
                    if t_class in exclude or t_class.__name__ in exclude or t_class.__qualname__ in exclude:
                        continue  # transpiler was specifically excluded
                if transpiler in current[2]:
                    continue  # transpiler was already used in this chain
                heappush(frontier, (current[0] + cost(transpiler), transpiler.target, (*current[2], transpiler)))

        raise KeyError(f"There is no transpilation path from '{source}' to '{target}'.")

    @staticmethod
    def get_transpilers_limit_depth(
        source: Union[str, Sequence[str]],
        target: str,
        *,
        exclude: Optional[set[Union[str, Type["CircuitTranspiler"]]]] = None,
        exclude_formats: Optional[set[str]] = None,
        exclude_unsafe: bool = False,
    ) -> Sequence["CircuitTranspiler"]:
        """Get a list of transpilers from source to target format using a constant cost of 1 for each step."""
        return CircuitTranspiler._get_transpiler_chain(
            source,
            target,
            cost=lambda x: 1,
            exclude=exclude,
            exclude_formats=exclude_formats,
            exclude_unsafe=exclude_unsafe,
        )

    @staticmethod
    def get_transpilers_limit_cost(
        source: Union[str, Sequence[str]],
        target: str,
        *,
        exclude: Optional[set[Union[str, Type["CircuitTranspiler"]]]] = None,
        exclude_formats: Optional[set[str]] = None,
        exclude_unsafe: bool = False,
    ) -> Sequence["CircuitTranspiler"]:
        """Get a list of transpilers from source to target format using the transpiler cost."""
        return CircuitTranspiler._get_transpiler_chain(
            source,
            target,
            cost=lambda x: x.cost,
            exclude=exclude,
            exclude_formats=exclude_formats,
            exclude_unsafe=exclude_unsafe,
        )


def transpile_circuit(
    target: str,
    *circuit: tuple[str, Any],
    exclude: Optional[set[Union[str, Type[CircuitTranspiler]]]] = None,
    exclude_formats: Optional[set[str]] = None,
    exclude_unsafe: bool = False,
) -> Any:
    """Transpile a circuit available in one or more source formats to a specific target format.

    Args:
        target (str): the target format for transpilation
        exclude (set[str | Type[CircuitTranspiler]], optional): exclude specific transpilers (by class, class name or qualified class name).
        exclude_formats (set[str], optional): exclude specific formats from transpilation. Applies to both source and target formats!
        exclude_unsafe (bool, optional): exclude unsafe transpilers from transpilation. Defaults to False.

    Raises:
        ValueError: If no circuit is provided or either the target format or all source formats are excluded by `exclude_formats`.
        KeyError: If no transpilation chain could be found to transpile the circuit to the target format.
        TranspilationError: If a transpilation step fails.

    Returns:
        Any: The transpiled circuit (this may be one of the input circuits if the format matches the target format)
    """
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

    transpiler_chain = CircuitTranspiler.get_transpilers_limit_depth(
        source=source_format,
        target=target,
        exclude=exclude,
        exclude_formats=exclude_formats,
        exclude_unsafe=exclude_unsafe,
    )

    assert len(transpiler_chain) > 0, "There should always be at least one transpiler present."

    # get the format the transpiler chain starts with
    first_circuit_format = transpiler_chain[0].source if transpiler_chain else target

    current_circuit = next(c for s, c in circuit if s == first_circuit_format)

    for transpiler in transpiler_chain:
        try:
            current_circuit = transpiler.transpile_circuit(current_circuit)
        except Exception as err:
            raise TranspilationError(transpiler, current_circuit) from err

        if isinstance(current_circuit, (str, bytes)):
            # circuit is in a format that can be safely stored in the database
            pass  # TODO implement persistence

    return current_circuit
