# InkChroma v0.1.0

InkChroma turns marked fountain-pen paper-chromatography scans into inspectable,
paper-normalized color profiles and ranked relative distances, entirely offline.

## Included

- `inkchroma-0.1.0-py3-none-any.whl`
- `inkchroma-0.1.0.tar.gz`
- `inkchroma-examples-v0.1.0.zip`

Install the wheel, extract the examples, and run:

```console
inkchroma compare inkchroma-examples-v0.1.0/blue-family/project.json --out inkchroma-report
```

## Limits

This is a relative visual comparison tool, not chemical identification. Comparable
paper, lighting, and scan settings matter. v0.1.0 uses manual coordinates, assumes
sRGB-like images, applies no ICC calibration or perspective correction, and limits
alignment to two profile points.
