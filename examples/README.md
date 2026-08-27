# InkChroma examples

These are deterministic synthetic PNG scans for learning the input format and
checking the real image pipeline. They are demonstration fixtures, not experimental
measurements.

- `blue-family`: three same-size strips. The two midnight-blue variants should be
  the closest pair.
- `different-sizes`: two scans with different pixel dimensions and marked travel
  intervals. Both normalize to the project's 64 profile points.
- `blank-strip`: a deliberate failure. It should name `blank-a`, report no
  measurable signal, and leave no output directory.

Run the success case from the repository root:

```console
uv run inkchroma compare examples/blue-family/project.json --out demo-output
```
