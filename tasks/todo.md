# InkChroma v0.1.0 task checklist

## Task 1: Foundation and parser

- [x] Define package metadata, immutable records, JSON project parsing, and clear
  boundary validation.
- [x] Acceptance: a valid project resolves image paths; malformed schema,
  duplicate names, and impossible coordinates fail with the sample and repair.
- [x] Verify: focused parser tests failed first, then passed (6 tests).
- Files: `pyproject.toml`, `src/inkchroma/model.py`, `src/inkchroma/project.py`,
  `tests/test_project.py`.

## Task 2: Profile extraction

- [x] Implement real Pillow decoding, paper normalization, Lab conversion,
  resampling, smoothing, and minimum-signal rejection.
- [x] Acceptance: different image sizes normalize to the configured point count;
  a blank strip is rejected without fallback.
- [x] Verify: focused analysis tests failed first, then passed (6 tests; 12 total).
- Files: `src/inkchroma/analysis.py`, `tests/test_analysis.py`.

## Task 3: Bands and pair distances

- [x] Detect contiguous visible bands and calculate sorted small-shift RMS pair
  distances.
- [x] Acceptance: two related blues rank closer than blue versus green; ties have
  stable name ordering.
- [x] Verify: focused analysis tests failed first, then passed (10 tests; 16 total).
- Files: `src/inkchroma/analysis.py`, `src/inkchroma/model.py`,
  `tests/test_analysis.py`.

## Task 4: Reports and CLI

- [ ] Render JSON, CSV, standalone SVG, and script-free HTML only after successful
  analysis; expose the installed `inkchroma` command.
- [ ] Acceptance: all four files agree on sample/pair ordering; failures exit 2 and
  leave no output directory.
- [ ] Verify: CLI integration tests using real subprocesses and images.
- Files: `src/inkchroma/report.py`, `src/inkchroma/cli.py`,
  `src/inkchroma/__main__.py`, `tests/test_cli.py`.

## Task 5: Examples and user documentation

- [ ] Add success, boundary, and blank failure fixtures; document install, one-minute
  use, I/O, limitations, and troubleshooting.
- [ ] Acceptance: every README command is executable as written.
- [ ] Verify: source-entry example runs and documented failure message matches.
- Files: `examples/`, `README.md`.

## Task 6: Reproducible release gate

- [ ] Add uv lock, format/lint/type/test/coverage/audit/build/clean-install gate,
  CI, tag release assets, MIT license, and changelog.
- [ ] Acceptance: `uv run python scripts/check.py` is the single green gate and CI
  runs the same command.
- [ ] Verify: complete local gate from a synchronized locked environment.
- Files: `uv.lock`, `scripts/check.py`, `.github/workflows/ci.yml`,
  `.github/workflows/release.yml`, `LICENSE`, `CHANGELOG.md`.

## Task 7: Review and remote closure

- [ ] Review final diff, rerun the gate, commit only exact repository files, verify
  author/contributor hygiene, publish public main, tag, Release, and assets.
- [ ] Download the remote wheel into a fresh environment and run the real example.
- [ ] Verify unauthenticated repository/Release access, then send Gmail summary.
- [ ] Acceptance: every item in `docs/spec.md` remote-release criteria has a URL,
  commit, run, asset, command result, or message identifier as evidence.
