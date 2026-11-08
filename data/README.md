# Bundled Site Data

`sites.json` is a 481-site snapshot from Sherlock Project's
`sherlock_project/resources/data.json`.

- Upstream repository: <https://github.com/sherlock-project/sherlock>
- Upstream package version: `0.16.2`
- Snapshot date: 2026-11-08
- Upstream license: MIT, reproduced in
  [`LICENSES/SHERLOCK-MIT.txt`](../LICENSES/SHERLOCK-MIT.txt)

The bundled snapshot makes scans reproducible and removes the runtime
external-package dependency. It also means new or changed upstream sites are
not picked up automatically.

Validate the snapshot:

```bash
python scripts/sherlock_scan.py validate-data
```

To update it later, review the upstream data schema and license, replace this
file, then run:

```bash
python scripts/sherlock_scan.py validate-data
python -m unittest discover -s tests -v
```
