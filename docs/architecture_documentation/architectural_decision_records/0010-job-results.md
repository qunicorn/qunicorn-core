# Job Results

* Status: proposed
* Deciders: [list everyone involved in the decision] <!-- optional -->
* Date: 2024-05-08

## Context and Problem Statement

Job results currently cannot be associated back with their deploayed program.
Job results are poorly specified.

## Decision Drivers

* Users of Qunicorn expect job results that contain all the required information in a sensible format
* The current way of exposing the result data in the metadata dict is bad for integration

## Considered Options

* Jobs and Job Results must link back to the Deployment/Program
* Result Metadata
* Inline Result Data
* Result Data as Separate REST Resource

## Decision Outcome

TBD


## Pros and Cons of the Options

### Jobs and Job Results must link back to the Deployment/Program

A job should contain a link back to its corresponding deployment, while a job result should link to the specific program the result is for.

* Good, because it saves bandwith in the job endpoint
* Good, because it allows to correctly correlate the result to the program
* Bad, because not everything is inlined in the job resource anymore

### Result Metadata

A job result may contain metadata under an optional metadata key.
The metadata should be in the form of a key value map, i.e., a JSON object with the keys being strings.
Metadata should be directly relevant to the result data type (examples: register information, qubit mapping).
Generic metadata (e.g., timings, the QPU/Vendor) that is relevant for all results should not be repeated for every single result, but rather be a seperate result or a level obove the individual results.

### Inline Result Data

Job results should follow this minimal result schema:

```
{
    "resultType": "<result type>",
    "data": ...
    "metadata": {
        "[key: str]": "value"
    }
}
```

* `resultType`: the string identifier of the result type (see {doc}`0011-result-types` for proposed and accepted result types)
* `data`: the result data (e.g. a counts dict for the "COUNTS" result type).
* `metadata` (optional): a key value mapping of result type specific metadata.

* Good, because fetching results is one operation
* Bad, because results may grow too large for inlining

### Result Data as Separate REST Resource

Job results should follow this minimal result schema:

```
{
    "resultType": "<result type>",
    "data": "<href to result data resource>"
    "metadata": {
        "[key: str]": "value"
    }
}
```

`data` is a link to the REST resource that contains the same data as in the inlined version of this schema.

* Good, because large results can be supported this way
* Bad, because fetching results takes multiple requests

## Links

* Related to {doc}`0011-result-types`

<!-- markdownlint-disable-file MD013 -->
