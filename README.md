# Data Visualizer

## Analysis Programs

- `analysis/__init__.py`
- `analysis/fetch_content.py`
- `analysis/load_urls.py`

### Classifiers
- `analysis/classifiers/__init__.py`
- `analysis/classifiers/content.py`

### Extractors
- `analysis/extractors/__init__.py`
- `analysis/extractors/features.py`
- `analysis/extractors/metadata.py`
- `analysis/extractors/text.py`

### Processors
- `analysis/processors/__init__.py`
- `analysis/processors/batch_processor.py`
- `analysis/processors/patterns.py`
- `analysis/processors/sitemap_processor.py`
- `analysis/processors/url_processor.py`

## Tooling

- Run analyses via `./run.sh analyze --input Site.jsonl --type all`
- Use `./manage.py` for command-line management (validate, summarize, flush, server)
- Launch server components with `./server.sh api|worker|flower|all`

## Output Structure

Generated artefacts are stored under `analysis/output` with the following layout:

- `basic/` – master pipeline outputs (`analysis_results.json`, reports)
- `enhanced/` – enhanced pipeline outputs with URL component analysis
- `mlx/` – MLX pipeline outputs and reports
- `SUMMARY/` – aggregated cross-analysis `summary.json` and `summary.md`
- `logs/` and `cache/` – reserved for runtime traces and cached models

Run `./manage.py summary` to regenerate the unified summary after analyses complete.

## Data Quality Validation

`analysis/data_validator.py` validates JSONL inputs using `pandera` and `jsonschema`.
The validator runs automatically inside `run.sh`, or manually via:

```bash
./manage.py validate Site.jsonl
```

## Developer Experience

- Pre-commit hooks configured in `.pre-commit-config.yaml`
- GitHub Actions workflow `.github/workflows/ci.yml` runs linting and pytest
