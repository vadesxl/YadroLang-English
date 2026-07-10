# Policy specification v1.0

A policy is UTF-8 JSON with exactly `version`, `sources`, `sinks`, and `sanitizers` (unknown fields are reserved for a future strict-schema update).

- `sources`: symbol to one built-in label.
- `sinks`: symbol to required capability.
- `sanitizers`: symbol to labels it may declassify.
- Built-in labels: `PII`, `Financial`, `Health`, `Credentials`, `Location`.

Custom entries extend built-ins for one CLI invocation and are reset afterward. Invalid versions, shapes, or labels fail closed. Built-in reserved symbols cannot be redefined by source code. Policy compatibility follows major-version semantics.
