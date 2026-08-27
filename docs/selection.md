# Project selection: InkChroma

## Search boundary

This is a differentiation study, not a claim that no similar project exists anywhere.
The inventory was taken on 2026-08-27 before this repository was created.

- Local inventory: 227 existing top-level Git repositories under `D:\我的\GitHub`.
- Prior work excluded from reuse: BalloonOrder, SofaPilot, MeshReady, TeachGraph,
  ReapCheck, Syncuisine, Query Quilt, Data XRay Local, README Flightcheck,
  ManualCare, JuiceBench, and the other locally inventoried tools.
- Dense local clusters included developer preflights, release evidence, physical
  packing and cutting optimizers, image QA, game tooling, data-export audits,
  accessibility checks, and Codex pets.
- Public research used several keyword families and then opened the closest
  projects' own README pages. Search results and star counts are time-specific.

## Three finalists

| Candidate | User and problem | Real input -> processing -> output | Main concern | Decision |
| --- | --- | --- | --- | --- |
| **InkChroma** | Fountain-pen ink hobbyists comparing paper chromatography strips | Marked strip scans -> paper-normalized color profiles, band summaries, aligned pair distances -> JSON, CSV, SVG, offline HTML | Image capture varies, so claims must stay relative and non-forensic | **Selected** |
| **WheelPass** | Wheel builders checking whether repeated spoke-tension passes converge | Multi-pass spoke readings -> side-aware deltas, oscillation and plateau checks -> workshop receipt | Current tools already provide tension conversion, radar charts, tuning plans, and pass logs | Rejected as too close |
| **FoldStock** | Home bookbinders choosing signatures before PDF imposition | Page count, stock size, grain and caliper -> feasible cuts and section-thickness search -> cutting/folding plan | Imposition is crowded and local work already contains several print/paper tools | Rejected as locally crowded |

Earlier probes were also rejected: germination analysis already has complete
research tools, embroidery palette matching has mature image-to-thread pipelines,
and laser kerf calibration has many generators and full fabrication suites.

## Why InkChroma won

InkChroma has the cleanest one-minute demonstration: analyze three supplied strip
scans, then see that two related blue inks are closer to one another than either is
to a green ink. The input is a real image, the output comes from image and color
processing rather than a hard-coded lookup, and a blank or unusable strip fails
with a specific repair instruction.

Its scope is also materially different from the local inventory. It is not a
general image diff, scientific instrument parser, chromatography laboratory suite,
or ink swatch database. The distinctive job is reproducible *relative comparison*
of hobby paper-chromatography lanes across scans.

## Closest projects and concrete differences

1. [quanTLC](https://github.com/OfficeChromatography/quanTLC) takes a planar
   chromatogram image plus experiment dimensions, extracts videodensitograms, then
   performs baseline correction, peak integration, calibration-model fitting, and
   quantitative prediction. InkChroma takes multiple visible-color paper strips,
   compares their background-normalized Lab profiles, and explicitly does not
   estimate concentration, LOD, or LOQ.
2. [OpenChrom](https://github.com/OpenChrom/openchrom) is a large desktop platform
   for mass-spectrometric and chromatographic instrument data. InkChroma accepts
   ordinary PNG/JPEG scans and emits a small, shareable hobby report; it has no
   vendor converters or instrument workflow.
3. [hplc-py](https://github.com/cremerlab/hplc-py) loads time/signal CSV data from
   high-performance liquid chromatography and fits quantitative peaks. InkChroma's
   source is spatial RGB image data, and its reported distance is relative visual
   evidence rather than chemical quantification.
4. [Advanced Chromatogram Analyzer](https://github.com/Anindya-Karmaker/Advanced_chromatogram_analyzer)
   imports ÄKTA, CSV, and Excel signals for lab plotting, peak integration, and
   protein calculations. InkChroma has no lab-instrument schema or concentration
   calculator; it normalizes paper color and compares several hobby strips.
5. [WBGelDensitometryTool](https://github.com/cernekj/WBGelDensitometryTool)
   uses ImageJ densitometry for western-blot-like grayscale bands with constrained
   geometry. InkChroma preserves three-channel color migration, normalizes each row
   against its local paper, uses normalized travel coordinates, and produces
   pairwise color-profile distances.
6. [TLCKiasV2](https://github.com/Sanam597/TLCKiasV2) is an adjacent smartphone
   assay project described in its published workflow: it selects TLC spots and uses
   a calibration curve to estimate metformin concentration. InkChroma avoids assay
   and identity claims and targets side-by-side fountain-pen ink exploration.

## Assumptions to validate in v0.1.0

- Users can provide a straight strip image and mark the lane, origin, and solvent
  front in a small JSON file.
- Local paper-color normalization makes scans from the same session meaningfully
  comparable without pretending to remove all camera, paper, or lighting effects.
- A transparent distance plus the underlying profiles is more trustworthy than an
  unexplained "same ink" score.

## Not doing in v0.1.0

- Automatic perspective correction or lane detection: it would dominate the MVP
  and hide failure behind guesses.
- Ink-name lookup or a hosted swatch database: comparison works on the user's own
  evidence and remains local.
- Chemical identity, authenticity, forensic, safety, or concentration claims:
  consumer scans do not support them.
- Accounts, cloud upload, GUI, camera control, or AI classification: none is needed
  to prove the core data flow.
