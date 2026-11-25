# Contributing to OmniEarth

Thank you for your interest in contributing to **OmniEarth**! Contributions of new dataset adapters, spectral indices, bug fixes, Colab notebooks, and documentation improvements are warmly welcomed.

---

## Quick Development Setup

OmniEarth maintains full feature parity across **Python (`omniearth/`)** and **Node.js / TypeScript (`src/`)**.

### Python Setup (with `uv`)
```bash
git clone https://github.com/lokeshsk/omniearth.git
cd omniearth
uv sync --all-extras
uv run --all-extras pytest --cov=omniearth --cov-report=term-missing tests/
```
> **Note:** OmniEarth enforces **100% statement test coverage** (`fail_under = 100` in `pyproject.toml`). Please make sure any new Python code includes unit tests using mocked HTTP responses (no live network dependencies in tests).

### Node.js / TypeScript Setup (with `pnpm`)
```bash
pnpm install
pnpm run build
pnpm test
```

---

## High-Impact Ways to Contribute

1. **Add a New Data Provider or STAC Collection**: Implement a provider adapter in `omniearth/providers/` and `src/providers/` (prefer zero-config public endpoints or optional env-var auth).
2. **Add Spectral / Remote Sensing Indices**: Extend `omniearth/indices.py` and `src/indices.ts` with well-documented radiometric formulas.
3. **Share Applied Workflows**: Contribute runnable Jupyter/Colab notebooks in `examples/` showcasing agricultural, hydrological, atmospheric, or GeoAI pipelines.
4. **Improve Provider Resilience**: Keep upstream STAC/REST endpoint routes up to date and surface clear `warn_upstream_issue()` diagnostics on HTTP 5xx/429/timeouts.

---

## Pull Request Checklist

- [ ] Target branch is `dev` (not `main`).
- [ ] Python test suite passes with **100.00% coverage**: `uv run --all-extras pytest --cov=omniearth tests/`
- [ ] TypeScript build & tests pass: `pnpm run build && pnpm test`
- [ ] Upstream API changes are mocked cleanly in unit tests.
- [ ] New dependencies are avoided unless strictly necessary.

By contributing, you agree that your contributions will be licensed under the **Apache License 2.0** ([LICENSE](LICENSE)).
