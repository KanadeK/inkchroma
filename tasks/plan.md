# Implementation plan: InkChroma v0.1.0

## Overview

Build the smallest complete CLI that extracts comparable color profiles from
marked paper-chromatography images, proves its failure contract, packages cleanly,
and closes the public GitHub release and notification loop.

## Architecture decisions

- Require explicit lane/origin/front coordinates; transparent user input is more
  reliable than automatic detection in this release.
- Keep one runtime dependency (Pillow); implement the small color and comparison
  math directly and test it.
- Analyze before writing output so failures are atomic.
- Publish through immutable GitHub Release assets, not PyPI.

## Dependency order

`project contract -> profile extraction -> pair comparison -> report/CLI -> examples/docs -> gate/CI -> remote release`

## Phases

### Phase 1: Foundation and core risk

- Task 1: package skeleton and project parser.
- Task 2: real-image profile extraction and signal failure.
- Task 3: band summaries and pair comparison.

Checkpoint: focused tests pass and three in-memory profiles rank as intended.

### Phase 2: Complete user flow

- Task 4: atomic report rendering and CLI exit contract.
- Task 5: committed success, boundary, and failure examples plus README.

Checkpoint: a source checkout produces the documented four outputs, while the
blank example fails without an output directory.

### Phase 3: Release gate and publication

- Task 6: single gate, lockfile, CI, release workflow, license, and changelog.
- Task 7: final review, clean commits, public repository, CI/tag/Release/assets,
  remote clean install, unauthenticated checks, and Gmail notification.

Checkpoint: every Definition of Done item has current evidence.

## Risks and mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Consumer scans differ by paper, light, or device | High | Row-local paper normalization, comparable-scan guidance, raw profiles, no identity claim |
| Similarity number looks authoritative | High | Call it a distance, expose the formula/shift, rank only within the run |
| Example images accidentally encode expected output | Medium | Generate only pixels; tests run the real decoder and algorithm |
| Output is partly written before an error | Medium | Complete analysis in memory, then create and populate the directory |
| Release succeeds but artifact is unusable | High | Download the remote wheel into a fresh directory and run its installed entry point |

## Open questions

None for v0.1.0.
