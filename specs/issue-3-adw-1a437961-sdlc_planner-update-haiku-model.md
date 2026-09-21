# Chore: Update haiku model references

## Chore Description
The codebase hardcodes the deprecated/legacy Anthropic model ID `claude-3-haiku-20240307` in the server's LLM processor (used for both SQL generation and random natural-language query generation) and in the corresponding unit tests' assertions. This model ID should be updated to the currently available Haiku model. The codebase already establishes the correct current model ID elsewhere (`.claude/hooks/utils/llm/anth.py` and `adws/adw_tests/health_check.py` both use `claude-haiku-4-5`), so `claude-3-haiku-20240307` should be replaced with `claude-haiku-4-5` everywhere it appears, and the corresponding test assertions must be updated to match so no tests regress.

## Relevant Files
Use these files to resolve the chore:

- `app/server/core/llm_processor.py` - Contains two hardcoded occurrences of `claude-3-haiku-20240307`: in `generate_sql_with_anthropic()` (line ~103) and in `generate_random_query_with_anthropic()` (line ~257). Both must be updated to `claude-haiku-4-5`.
- `app/server/tests/core/test_llm_processor.py` - Contains a test assertion (line ~122) that asserts `call_args[1]['model'] == 'claude-3-haiku-20240307'` in `test_generate_sql_with_anthropic_success`. Must be updated to assert `claude-haiku-4-5` to match the production code change.
- `app/server/tests/core/test_llm_processor_random_query.py` - Contains a test assertion (line ~107) that asserts `call_args[1]['model'] == 'claude-3-haiku-20240307'` in `test_generate_random_query_with_anthropic_success`. Must be updated to assert `claude-haiku-4-5` to match the production code change.
- `.claude/hooks/utils/llm/anth.py` - Reference file (no change needed) showing the already-established, currently-correct model ID `claude-haiku-4-5` used elsewhere in this codebase for the fastest/cheapest Anthropic model.
- `adws/adw_tests/health_check.py` - Reference file (no change needed) showing `claude-haiku-4-5` used as the `--model` flag for Claude Code health checks, confirming this is the available model ID convention already adopted in this repo.

No new files need to be created for this chore.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Update the production model references in `llm_processor.py`
- Open `app/server/core/llm_processor.py`.
- In `generate_sql_with_anthropic()`, change `model="claude-3-haiku-20240307",` to `model="claude-haiku-4-5",`.
- In `generate_random_query_with_anthropic()`, change `model="claude-3-haiku-20240307",` to `model="claude-haiku-4-5",`.
- Confirm via `grep -rn "claude-3-haiku-20240307" app/server/core/llm_processor.py` that no occurrences remain.

### 2. Update the test assertions to match the new model ID
- Open `app/server/tests/core/test_llm_processor.py` and change the assertion `assert call_args[1]['model'] == 'claude-3-haiku-20240307'` to `assert call_args[1]['model'] == 'claude-haiku-4-5'`.
- Open `app/server/tests/core/test_llm_processor_random_query.py` and change the assertion `assert call_args[1]['model'] == 'claude-3-haiku-20240307'` to `assert call_args[1]['model'] == 'claude-haiku-4-5'`.

### 3. Verify no other references remain anywhere in the codebase
- Run `grep -rn "claude-3-haiku-20240307" .` from the repo root (excluding `.git/`) and confirm zero matches remain in `app/**`, `scripts/**`, `adws/**`, and `README.md`.

### 4. Run the Validation Commands
- Run all validation commands below and confirm they pass with zero regressions.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `grep -rn "claude-3-haiku-20240307" --include="*" . 2>/dev/null | grep -v node_modules | grep -v "\.git/"` - Confirm this returns no results (all references have been updated)
- `cd app/server && uv run pytest` - Run server tests to validate the chore is complete with zero regressions
- `cd app/server && uv run pytest tests/core/test_llm_processor.py tests/core/test_llm_processor_random_query.py -v` - Specifically confirm the two affected test files pass with the updated model assertions

## Notes
- `claude-haiku-4-5` is the model ID already used elsewhere in this repo (`.claude/hooks/utils/llm/anth.py` and `adws/adw_tests/health_check.py`) as the current/available fastest Anthropic Haiku model, so this chore aligns `llm_processor.py` with the existing convention rather than introducing a new naming pattern.
- No other files under `app/**`, `scripts/**`, or `adws/**` (besides the two identified test files and `llm_processor.py`) contain the string `claude-3-haiku-20240307`.
- This is a pure string-substitution chore with no API/behavior changes beyond which underlying Anthropic model is called; no new dependencies, environment variables, or endpoint changes are required.
