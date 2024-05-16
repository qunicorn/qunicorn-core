# Result Types of Jobs

* Status: [proposed | rejected | accepted | deprecated | … | superseded by [ADR-0005]] <!-- optional -->
* Deciders: [list everyone involved in the decision] <!-- optional -->
* Date: [YYYY-MM-DD when the decision was last updated] <!-- optional -->

## Context and Problem Statement

The result of a quantum circuit execution can have different forms (e.g., counts, expectation value, quasi-probability distribution, state vector).
Results of the same type/category are similar between vendors, but often have subtle differences.
Qunicorn should provide unified result formats for widely used result types.

## Decision Drivers

* Executing quantum programs can generate different result types depending on the execution target
* Each vendor has their own result specifications
* Qunicorn is expected to provide a uniform access to different quantum providers

## Accepted Formats

* Counts

## Proposed Formats

* Metadata


## Decision Outcome

New formats can be proposed by adding new options to this document.
Accepted formats should be moved to "Accepted Formats" and marked as accepted.
Rejected formats should be marked as rejected.


## Formats

### Counts

Specifier: `COUNTS`

Example:

```JSON
{
    "0": 502,
    "1": 522
}
```

The values represent the counts, i.e., the number of times the result in the key got measured.
The keys contain the measured results.
The string representing measured results follows the qiskit spec for counts.
Individual registers or bits are separated by a single space.
Register values may be encoded as hex (a more efficient encoding in anticipation for larger QPUs).
Counts should only include classical bits (explicitly) marked as results of the quantum program.
A Quantum Circuit without any measurements (or without classical bits/registers) should produce an empty counts dict!

Count specific metadata:

* `format`: **`bin`**|`hex` To determine whether the measured registers are encoded in binary (using only `0` and `1`) or in hexadecimal notation.
* `shots`: The number of shots (useful if the count dict is empty for some reason)
* `registers`: A list of measured/returned registers in the order they appear in the string keys of the counts.
  This metadata key is required when `format=hex` as the register size is otherwise lost because of the hex encoding.
  ```json
  {
    "name": "<the register/bit name>",
    "size": 1
  }
  ```


### Metadata

Metadata is a result type for metadata that is independent of a specific result type (e.g., the execution times, the qubit mapping, the QPU, etc.).

Example:

```json
{
    "timestamp": "2024-05-07T12:03:08+02:00",
    "shots": 1024,
    "seed_simulator": 3772757147,
    "status": "DONE",
    "success": true,
    "time_taken": 0.001725117,
    "QPU": "...",
    "vendor": "...",
    "...": "..."
}
```


## Links

* Related to {doc}`0010-job-results`

<!-- markdownlint-disable-file MD013 -->
