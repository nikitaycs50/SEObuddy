# Publishing to PyPI

End-user install instructions are in the [README](../README.md) and [USER_MANUAL.md](USER_MANUAL.md).

## First-time setup (maintainer)

1. Create an account at [pypi.org](https://pypi.org) and enable 2FA.
2. Create an API token: Account settings → API tokens → scope **Entire account** (first upload) or **Project: seobuddy** (later).
3. Store the token locally (never commit it). Options:
   - Copy `.env.example` → `.env` and paste your `pypi-...` token (`.env` is gitignored).
   - Or export `TWINE_USERNAME=__token__` and `TWINE_PASSWORD=<token>`.
   - Or run `./scripts/publish-to-pypi.sh` in a terminal — it prompts for the token if needed.

## Manual release

1. Bump `__version__` in `src/seobuddy/__init__.py`.
2. Build and upload:

```bash
cp .env.example .env   # edit .env once with your token
./scripts/publish-to-pypi.sh
```

Or with environment variables:

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-...
./scripts/publish-to-pypi.sh
```

Or step by step:

```bash
python3 -m pip install --upgrade build twine
python3 -m build
twine check dist/*
TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-... twine upload dist/*
```

3. Verify: `pipx install seobuddy` and `seobuddy --help`.

## Automated release (GitHub Actions)

Workflow: [.github/workflows/publish-pypi.yml](../.github/workflows/publish-pypi.yml)

1. On PyPI: project **seobuddy** → Publishing → add trusted publisher:
   - Owner: `nikitaycs50` (or your GitHub user/org)
   - Repository: `SEObuddy`
   - Workflow: `publish-pypi.yml`
   - Environment: (default)
2. Push a version tag after merging a release:

```bash
git tag v0.2.0
git push origin v0.2.0
```

The workflow builds with Hatch and publishes via OIDC (no long-lived PyPI token in GitHub secrets).
