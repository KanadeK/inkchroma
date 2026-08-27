# Release and recovery contract

## Publish sequence

1. `main` must pass the `CI` workflow.
2. The local `uv run python scripts/check.py` result must be green on the exact
   commit to tag.
3. Create the annotated `v0.1.0` tag on that commit and push it.
4. The tag workflow reruns the same gate, then creates a non-draft GitHub Release
   with the wheel, source distribution, and example bundle produced by that run.
5. Download the public wheel and example bundle without repository credentials,
   install into a new environment, and run the bundled blue-family project.
6. Only after repository, CI, tag, Release, assets, public access, and clean-install
   checks pass may the Gmail release notice be sent.

## Recovery

- A failed pre-release workflow creates no Release. Fix the root cause on `main`,
  rerun the full gate, and create a new tag only from a green commit.
- Do not silently replace assets of an already published version. If a released
  v0.1.0 defect is found, describe it on that Release and publish a corrected patch
  version.
- Users can remove InkChroma with `python -m pip uninstall inkchroma`; it has no
  service, database, account, migration, or runtime network state to roll back.

For this local CLI, server health dashboards, staged traffic percentages, feature
flags, and database rollback do not apply. The public download plus clean installed
example is the post-launch health check.
