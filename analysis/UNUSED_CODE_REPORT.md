# Unused Code Forensics Report

## Summary
- **Scope**: `./run.sh` (`analyze -t basic --skip-validation`) on macOS (Darwin); repository-wide Python sources.
- **Timestamp (UTC)**: 2025-10-28 16:30:13.
- **Git SHA**: `afd2bf62ac6b69f5bd7abe2489bf5f8691b0f424`.
- **Execution details**: `PYTHONPROFILEIMPORTTIME=1 ./run.sh analyze -t basic --skip-validation` (strace unavailable on macOS; import-time profiling used instead).
- **Outcome**: Pipeline completed successfully; dynamic trace captured 23 project modules, static graph reached 52; nine files determined unused (dynamic + static agreement).

## Method
- **Dynamic footprint**: Enabled `PYTHONPROFILEIMPORTTIME` and ran the entrypoint to capture every module import touched during the run (`.forensics/python_profile_imports.log`). Filtered out virtualenv/site-packages noise and normalised to repo-relative modules.
- **Static reachability**: Built an AST-based import graph rooted at `analysis.pipeline.master_pipeline` to approximate all modules callable from the executed command. Included package parent linkage to catch `__init__` side effects.
- **Dead-symbol sweep**: Ran `python3 -m vulture analysis scripts save_metrics.py manage.py` to cross-check unused functions and variables (used qualitatively, not as final authority).
- **Filters/exclusions**: Ignored `venv/`, `.venv/`, `__pycache__`, tests, docs, and generated artefacts. Migrations called out separately due to deployment-dependency ambiguity.
- **Limitations**: No syscall-level tracing (strace not available on macOS); import-time profiling misses non-import file I/O and runtime-generated module names. Only the “basic” analysis path was executed—other modes may load additional modules not observed here.

## Unused Map (Authoritative)
| path | kind | reason | evidence | last_modified | confidence | suggested_action |
| --- | --- | --- | --- | --- | --- | --- |
| `database/migrations/env.py:1-75` | file | dynamic+static | No hits in `.forensics/python_profile_imports.log`; AST walk from `analysis.pipeline.master_pipeline` never references `database.*`. | 2025-10-28 | 0.5 | Confirm whether Alembic migrations are still required; archive or move under ops scripts if unused at runtime. |
| `database/migrations/2025_01_24_1500-add_session_relationships.py:1-36` | file | dynamic+static | Absent from import log; migration package not reachable from executed pipeline. | 2025-10-27 | 0.5 | If already applied, keep only in migration history outside production deploy bundle or document retention policy. |
| `manage.py:1-98` | file | dynamic+static | No `manage` entry in import log; static graph rooted at `analysis.pipeline` does not import CLI. | 2025-10-28 | 0.8 | Deprecate Django-style CLI or relocate to tooling/README; ensure docs don’t reference it. |
| `save_metrics.py:1-87` | file | dynamic+static | Not imported/executed during run; no static edge from master pipeline to standalone script. | 2025-10-28 | 0.8 | Fold into documented scripts directory or remove; avoids confusion with `scripts/save_metrics.py`. |
| `scripts/check_quality.py:1-86` | file | dynamic+static | No matches in import log; AST graph lacks any `scripts.*` usage. | 2025-10-28 | 0.8 | Either expose via dedicated CLI flag or move to docs/examples. |
| `scripts/cleanup_cache.py:1-107` | file | dynamic+static | Unreferenced in dynamic trace; static analysis shows no imports from runtime code. | 2025-10-28 | 0.8 | Consider dropping or relocating under ops tooling. |
| `scripts/find_duplicates.py:1-122` | file | dynamic+static | Zero dynamic touches; static pipeline graph cannot reach `scripts.*`. | 2025-10-28 | 0.8 | Promote to optional CLI (with tests) or remove to reduce maintenance drag. |
| `scripts/save_metrics.py:1-87` | file | dynamic+static | Missing from runtime imports; duplicates top-level `save_metrics.py` functionality. | 2025-10-28 | 0.8 | Consolidate with primary metrics writer to avoid drift. |
| `scripts/view_trends.py:1-182` | file | dynamic+static | Not observed at runtime; no static edge from executed entrypoint into `scripts.*`. | 2025-10-28 | 0.8 | Either wire into `run.sh` workflows or extract as documentation example. |

## Likely False Positives / Edge Cases
- **`analysis/summary_aggregator.py`**: Static graph reachable, but dynamic trace omitted because the run used `-t basic` and never triggered `generate_summary` (`analysis_type=all` would execute it). Keep.
- **`analysis/data_validator.py`**: Skipped dynamically due to `--skip-validation`. When validation is required, `run.sh` would execute it, so absence here is expected.
- **`analysis/processors.{batch_processor,sitemap_processor,url_processor}` and dependent helpers**: Imported indirectly via package initialisers but not exercised without database-backed workflows. Treat as dormant feature, not dead code.

## AI-ish / Robotic Code Signals
- **analysis/helpers/__init__.py:1-45**  
  - *Signals*: Marketing-toned docstring describing “Strategic Helper Function Library” with enumerated pillars; exports large surface area unused by runtime.  
  - *Risk*: Suggests boilerplate generated to satisfy prompt requirements; increases surface area without integration.  
  - *Recommendation*: Trim docstring to factual info and only export helpers that have callers; add tests before adoption.
- **analysis/helpers/semantic_clustering.py:1-84**  
  - *Signals*: Docstring references other files and line numbers (“Enhances semantic_path_analyzer.py (lines 15-250)”), weighted heuristics with hand-wavy comments, no callers in dynamic trace.  
  - *Risk*: High-maintenance analytical code with unverifiable metrics; likely promptware.  
  - *Recommendation*: Either integrate via targeted unit tests + documented consumers or quarantine until justified.
- **analysis/processors/url_processor.py:12-120**  
  - *Signals*: Workflow docstring enumerating six steps, references non-existent modules (`analysis.fetch_url`, `server.storage.save_url`), extensive logging scaffolding without error handling.  
  - *Risk*: Indicates cargo-cult pipeline stitched from prompts; missing dependencies (`analysis.fetch_url`) would crash immediately.  
  - *Recommendation*: Gate behind feature flag, add dependency checks, or refactor into minimal viable ingestion backed by real modules.

## Appendices

**Metrics**
- Python modules analysed: 61 total.
- Dynamic footprint: 23 project modules recorded in `.forensics/python_profile_imports.log`.
- Static reachability from `analysis.pipeline.master_pipeline`: 52 modules.
- Overlap resulting in unused files (dynamic ∩ static gap): 9.

**Top Unused Blobs (by lines)**
| path | lines |
| --- | --- |
| `scripts/view_trends.py` | 182 |
| `scripts/find_duplicates.py` | 122 |
| `scripts/cleanup_cache.py` | 107 |

**Key Commands (repro)**
```bash
PYTHONPROFILEIMPORTTIME=1 ./run.sh analyze -t basic --skip-validation 2> .forensics/python_profile_imports.log
python3 -m vulture analysis scripts save_metrics.py manage.py
python3 - <<'PY'  # AST reachability & metrics (see notebook)
...custom script emitted reachable modules...
PY
```
