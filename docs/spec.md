# Spec: InkChroma v0.1.0

## Assumptions

1. The target user is a fountain-pen ink hobbyist who can crop a straight paper
   chromatography strip and identify its lane, origin, and solvent-front rows.
2. v0.1.0 compares scans as sRGB-like consumer images. It does not implement ICC
   color management or claim cross-device color accuracy.
3. GitHub Release wheels and source distributions are the publication channel;
   PyPI publication is outside this release.
4. The user's explicit autonomous authorization covers ordinary implementation and
   release choices, so no intermediate product-choice confirmation is required.

## Objective

Build an offline command-line tool that converts marked paper-chromatography strip
images into inspectable color profiles and relative pairwise comparisons.

The successful user flow is:

1. Put two or more PNG/JPEG strip scans beside a JSON project file.
2. Run one command.
3. Receive deterministic `analysis.json`, `distances.csv`, `profiles.svg`, and a
   script-free `report.html` showing the profiles, detected color bands, warnings,
   and ranked pair distances.

The program must fail before creating the output directory when the project is
invalid, an image cannot be decoded, coordinates are unusable, or a strip has no
measurable ink signal. Every error names the sample and a user action that can fix
the input.

## Product contract

### Command

```text
inkchroma compare PROJECT.json --out OUTPUT_DIR
```

Exit codes:

- `0`: complete analysis, including non-blocking warnings.
- `2`: invalid CLI/project/image input or no measurable strip signal.

### Project JSON

```json
{
  "schema_version": 1,
  "profile_points": 96,
  "minimum_signal_delta_e": 2.0,
  "samples": [
    {
      "name": "blue-a",
      "image": "strips/blue-a.png",
      "lane": {"x_start": 24, "x_end": 56},
      "solvent_front_y": 18,
      "origin_y": 220
    },
    {
      "name": "blue-b",
      "image": "strips/blue-b.png",
      "lane": {"x_start": 24, "x_end": 56},
      "solvent_front_y": 18,
      "origin_y": 220
    }
  ]
}
```

Paths are resolved relative to the project file. Coordinates use Pillow pixel
coordinates: `x_start` is inclusive, `x_end` is exclusive, and
`solvent_front_y < origin_y`. Pixels outside the lane on both sides provide the
row-local paper reference; each side must contain at least two pixels.

### Processing

For each sample:

1. Decode and convert the image to RGB.
2. For every row from origin to solvent front, average lane pixels and the paper
   pixels outside the lane.
3. Convert both colors from sRGB to CIE Lab, then store the signed lane-minus-paper
   vector and its Delta E 76 magnitude.
4. Resample the travel interval to `profile_points` normalized Rf positions and
   apply one three-point smoothing pass.
5. Reject the sample when its strongest smoothed signal is below
   `minimum_signal_delta_e`.
6. Summarize contiguous above-threshold regions as bands with weighted Rf center,
   span, peak strength, and representative RGB color.
7. Compare each pair using root-mean-square Euclidean distance between the signed
   Lab vectors. Try integer shifts of at most two profile points and report both
   the best distance and chosen shift.

The distance is only meaningful relative to other pairs produced from comparable
scans. Lower means more visually similar after this normalization; it is not a
probability and not an identity decision.

### Outputs

- `analysis.json`: schema version, settings, warnings, full sample profiles, band
  summaries, and sorted pair comparisons.
- `distances.csv`: one row per pair with distance and alignment shift.
- `profiles.svg`: standalone vector plot of signal strength against normalized Rf.
- `report.html`: script-free, self-contained explanation, summary tables, and the
  inline SVG profile plot.

All files are UTF-8 with stable ordering. The tool analyzes everything before it
creates `OUTPUT_DIR`, so blocking failures leave no partial report. The output
parent must already exist and `OUTPUT_DIR` must be new; the command never overwrites
an earlier report.

## Tech stack

- Python `>=3.11,<3.15`
- Pillow `>=11,<13` for real PNG/JPEG decoding
- Standard library for JSON, CSV, color math, comparison, SVG, HTML, and CLI
- pytest + pytest-cov, Ruff, mypy, build, pip-audit, and uv for development gates

No web framework, numeric framework, database, or runtime network access.

## Commands

```powershell
# Install locked development environment
uv sync --locked --group dev

# Focused tests during TDD
uv run pytest tests/test_analysis.py -q

# Full local and CI acceptance gate
uv run python scripts/check.py

# Direct 60-second demonstration
uv run inkchroma compare examples/blue-family/project.json --out demo-output

# Build distributions
uv build
```

## Project structure

```text
src/inkchroma/       package source and installed CLI
tests/               unit and CLI integration tests
examples/            success, boundary, and failure inputs
scripts/check.py      single local/CI/release acceptance command
docs/selection.md     local inventory, candidates, and neighbor differences
docs/spec.md          this product and engineering contract
tasks/plan.md         dependency-ordered implementation plan
tasks/todo.md         live verification checklist
.github/workflows/    CI and tag-driven release automation
```

## Code style

Typed, direct functions with domain names and explicit data flow:

```python
def compare_profiles(left: Profile, right: Profile) -> PairDistance:
    """Return the best transparent small-shift RMS distance."""
```

- Ruff formatting and linting.
- Strict mypy for package and gate code.
- Dataclasses for internal immutable records; plain dictionaries only at the JSON
  serialization boundary.
- No one-use abstraction, framework wrapper, broad exception catch, silent
  fallback, or guessed coordinate repair.

## Testing strategy

- Unit tests: sRGB/Lab conversion invariants, resampling, band detection, shift
  selection, deterministic ordering, and validation failures.
- Integration tests: real Pillow images, relative path resolution, CLI exit codes,
  complete output set, no partial directory on failure, and script-free HTML.
- Example tests: success (`blue-family`), boundary (`different-sizes`), and failure
  (`blank-strip`) run through the installed entry point.
- Packaging test: build wheel/sdist, create a clean isolated environment, install
  the wheel, run the installed console entry point against copied examples.
- Coverage gate: at least 90% branch coverage; no skipped tests.

## Boundaries

### Always

- Validate project/image inputs at the CLI boundary and fail with a repair action.
- Keep comparison math deterministic and its assumptions visible in outputs.
- Run `uv run python scripts/check.py` after any release-affecting change.
- Keep the final worktree clean and commits authored only as KanadeK.

### Ask first

- Any scope expansion beyond this repository or beyond the authorized GitHub and
  Gmail release workflow.
- Any action requiring credentials outside the official interactive login flow.

### Never

- Claim chemical identity, authenticity, concentration, safety, or forensic proof.
- Upload user images or add runtime network calls.
- Hide a failure with defaults, skip a failing test, lower an assertion, or publish
  from a commit that did not pass the complete gate.
- Modify another repository or stage the outer `D:\我的\GitHub` worktree.

## Success criteria

### Product and local release

- Real images flow through decoding, color normalization, profile extraction,
  comparison, and four deterministic output formats.
- Success, boundary, and failure examples behave as documented.
- README contains problem, users, installation, 60-second quick start, I/O,
  limitations, and actionable troubleshooting.
- `scripts/check.py` proves format, lint, strict types, tests, coverage, examples,
  build, clean artifact install, installed entry point, and README commands.
- Final diff review finds no unresolved correctness, security, packaging, or
  documentation defect.

### Remote release

- Public `KanadeK/inkchroma` repository, final commit on default `main`, clean local
  tree, correct sole author/contributor, and passing GitHub CI.
- Annotated `v0.1.0` tag points to that exact commit.
- A non-draft, non-prerelease GitHub Release contains wheel, sdist, and example
  bundle assets.
- A fresh environment installs a newly downloaded remote wheel and runs the real
  example successfully.
- Repository and Release are reachable through unauthenticated public requests.
- Gmail self-notification is sent only after all preceding evidence is true.

## Open questions

None block v0.1.0. Real-world scanner variation remains an explicit limitation to
test with community samples after release.
