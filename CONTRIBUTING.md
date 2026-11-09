# Contributing

Thanks for your interest in the Smart Home Simulator. Bug reports, ideas and pull requests
are welcome. Read the [product objective](docs/PRODUCT_OBJECTIVE.md) first: the project helps
decide on Wi-Fi coverage before buying smart-home devices, and features outside that goal
(automations, cloud, shops) are out of scope.

## Setting up

You need Python 3.11+ and Node.js 22. From the repository root:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r services/simulator/requirements-dev.lock.txt
.venv/bin/python -m pip install --no-deps --no-build-isolation -e services/simulator
npm --prefix apps/web ci
.venv/bin/python scripts/dev.py      # API on 127.0.0.1:8000, interface on 127.0.0.1:5174
```

On Windows use `.venv\Scripts\python.exe` and `npm.cmd`. More detail in
[LOCAL_DEVELOPMENT.md](docs/migration/LOCAL_DEVELOPMENT.md).

## Code layout

- `services/simulator/src/smart_environment`: Pydantic models (`models.py`), the estimator
  (`engines.py`), coverage maps, scenarios, placement, reports and the FastAPI app (`api.py`).
- `apps/web/src`: React components; pure editor logic lives in `src/editor` with its tests.
- `contracts/` and `apps/web/src/generated/` are **generated**: never edit them by hand.

## Changing a model or the API

The Pydantic models are the single source of truth. After changing them:

```bash
.venv/bin/python scripts/export_contracts.py   # JSON Schema and OpenAPI
npm --prefix apps/web run contracts             # TypeScript types
```

Prefer additive, optional fields so existing projects stay valid and keep their hash.

## Rules for results

- Keep units explicit (m, Hz, dBm, dBi, degrees).
- Never invent RSSI, sensitivities, probabilities or measurements: an unknown value must
  produce a partial or unverified result, not a favourable one.
- Do not add a silent fallback when a requested engine is not available.
- Physics changes need a test against a reference value, not only against the current output.

## Pull requests

1. Create a branch from `main` and keep the change focused.
2. Run the checks:

   ```bash
   .venv/bin/python -m pytest services/simulator/tests -q
   .venv/bin/python scripts/export_contracts.py --check
   npm --prefix apps/web test
   npm --prefix apps/web run build
   ```

3. Check interface changes in the browser, not only with the build.
4. Write commit messages in the imperative mood, prefixed with the kind of change
   (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `build:`, `ci:`).
5. Open the pull request; CI runs everything on Linux, Windows and macOS.

## Reporting a bug

Open an issue with the steps to reproduce it and, if possible, the project file
(**Guardar JSON**) that shows the problem. Remove anything private from the plan first.
