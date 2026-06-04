# Publishing to PyPI

End-user install: `pip install seobuddy` or `pipx install seobuddy` — see [README](../README.md) and [USER_MANUAL.md](USER_MANUAL.md).

Package page: https://pypi.org/project/seobuddy/

---

## Recommended release flow (GitHub Actions + OIDC)

This is the normal path after trusted publishing is configured. **No PyPI API token in GitHub** is required.

### Each release

1. **Test locally**

   ```bash
   source .venv/bin/activate
   pip install -e ".[dev]"
   pytest -q
   ```

2. **Bump version** (single source of truth)

   Edit `__version__` in [`src/seobuddy/__init__.py`](../src/seobuddy/__init__.py), e.g. `0.2.0` → `0.2.1`.

   Hatch reads this at build time via `[tool.hatch.version]` in `pyproject.toml`.

3. **Commit and push to `main`**

   ```bash
   git add -A
   git commit -m "Release 0.2.1: short description of changes"
   git push origin main
   ```

4. **Watch GitHub Actions**

   Workflow: [.github/workflows/publish-pypi.yml](../.github/workflows/publish-pypi.yml) — **Publish to PyPI**

   - Runs on push to `main` when these paths change: `src/**`, `pyproject.toml`, `README.md`, `LICENSE`
   - Also runs on tags `v*` and on manual **Run workflow**
   - If that `__version__` is **already** on PyPI → job succeeds but **skips upload**
   - If the version is **new** → builds and uploads via OIDC

5. **Verify** (after 1–5 minutes)

   ```bash
   pip index versions seobuddy
   pip install -U seobuddy
   seobuddy --help
   ```

```text
pytest → bump __version__ → commit → push main → Actions → pip install -U seobuddy
```

### When the workflow does **not** run

Changes only under `docs/`, `tests/`, `plans/`, etc. do not match the `paths` filter. Either:

- Include a change under `src/**`, `pyproject.toml`, `README.md`, or `LICENSE`, or
- Push a tag `v*` (e.g. `v0.2.1`), or
- Actions → **Publish to PyPI** → **Run workflow**

---

## First-time setup (one-time)

### Trusted publisher (required for GitHub Actions)

On [pypi.org](https://pypi.org) → **Your account** → **Publishing** → add a **pending** or project publisher:

| Field | Value |
|-------|--------|
| PyPI project name | `seobuddy` |
| Owner | `nikitaycs50` |
| Repository | `SEObuddy` |
| Workflow name | `publish-pypi.yml` |
| Environment | *(leave empty — workflow does not use a named environment)* |

After the first successful workflow run, the project moves from **Pending publishers** to an active publisher on **seobuddy**.

### PyPI account

1. Register at [pypi.org](https://pypi.org) and enable **2FA**.
2. No API token is needed for CI if you only use trusted publishing.

---

## Manual release (fallback)

Use if you need to publish without GitHub Actions or OIDC is unavailable.

1. Bump `__version__` in `src/seobuddy/__init__.py`.
2. Create an API token: [pypi.org/manage/account/token/](https://pypi.org/manage/account/token/) — scope **Project: seobuddy** (or entire account for first upload).
3. Upload (never commit the token):

   ```bash
   cp .env.example .env   # edit .env with TWINE_PASSWORD=pypi-...
   ./scripts/publish-to-pypi.sh
   ```

   Or:

   ```bash
   export TWINE_USERNAME=__token__
   export TWINE_PASSWORD=pypi-...
   ./scripts/publish-to-pypi.sh
   ```

4. Verify: `pip index versions seobuddy` and `seobuddy --help`.

---

## Optional triggers

| Trigger | Command / action |
|---------|------------------|
| **Tag** | `git tag v0.2.1 && git push origin v0.2.1` |
| **Manual** | GitHub → Actions → **Publish to PyPI** → **Run workflow** |

Same version rules apply: PyPI rejects duplicate versions; bump `__version__` first.

---

## Notes

- **Version** lives only in `src/seobuddy/__init__.py` (not duplicated in `pyproject.toml`).
- **Build** uses Hatchling; workflow runs `python -m build`.
- Pushes to `main` without a version bump: workflow may run but will skip upload if that version already exists on PyPI.
