# Feature: Random Natural Language Query Button

## Feature Description
Add a "Random Query" button to the main query section of the Natural Language SQL Interface. When clicked, the button calls the backend, which uses the existing LLM routing (`core/llm_processor.py`) to inspect the current database schema (tables, columns, types, row counts) and generate an interesting, natural-language question a user could ask about that data. The generated question always overwrites whatever is currently in the query textarea, giving users a one-click way to discover what kinds of questions are worth asking about their uploaded data — especially useful for new users who don't yet know what's in their tables or how to phrase a query.

## User Story
As a user exploring a newly uploaded dataset
I want to click a button that suggests an interesting natural language query based on my data's actual tables and columns
So that I can quickly learn what questions I can ask and run them without having to think one up myself

## Problem Statement
Users who upload data (or load sample data) are presented with an empty query textarea and no guidance on what kinds of questions are answerable given the tables that exist. They must already know the schema and think of a reasonable natural-language question themselves, which is a barrier for first-time or exploratory use. There is currently no feature that inspects the live schema and suggests a query.

## Solution Statement
Introduce a new backend endpoint (`POST /api/random-query`) that fetches the current database schema via the existing `get_database_schema()` helper and passes it to a new schema-aware prompt in `core/llm_processor.py` that asks the already-configured LLM (OpenAI or Anthropic, using the same key-priority routing as `generate_sql`) to produce one interesting natural-language question (max two sentences) referencing the real tables/columns. On the client, add a new "🎲 Random Query" button styled like the existing "Upload Data" secondary button, visually separated from the primary Query/Upload Data button group via `justify-content: space-between`. Clicking it calls the new endpoint and always overwrites the query textarea's contents with the returned question (or shows an error if there are no tables yet or the call fails).

## Relevant Files
Use these files to implement the feature:

- `app/server/core/llm_processor.py` - Contains `generate_sql_with_openai`, `generate_sql_with_anthropic`, `format_schema_for_prompt`, and the `generate_sql` routing function. New `generate_random_query_with_openai`, `generate_random_query_with_anthropic`, and `generate_random_query` functions will follow the exact same patterns (env key priority, markdown cleanup, exception wrapping).
- `app/server/core/data_models.py` - Pydantic request/response models live here (e.g. `QueryRequest`/`QueryResponse`). Add `RandomQueryRequest` and `RandomQueryResponse` here following the same style.
- `app/server/core/sql_processor.py` - Contains `get_database_schema()`, which is reused unmodified to build the `schema_info` dict passed into the new LLM function.
- `app/server/server.py` - FastAPI route definitions (`/api/query`, `/api/schema`, etc.) with a consistent try/except + logging pattern. Add the new `POST /api/random-query` endpoint here, following the same structure as `process_natural_language_query`.
- `app/server/tests/core/test_llm_processor.py` - Existing unit test patterns (mocking `OpenAI`/`Anthropic` clients, env vars via `patch.dict`) to mirror for the new random-query functions.
- `app/client/index.html` - Contains the `.query-controls` div with the `query-button` and `upload-data-button`. Add the new `random-query-button` here, restructuring the controls so the new button is justified apart from the existing pair.
- `app/client/src/style.css` - Contains `.query-controls`, `.primary-button`, `.secondary-button` styles. Update `.query-controls` layout (justify-content: space-between) and add a wrapper class for the left-hand button group; reuse `.secondary-button` for the new button (per the issue: "Use Upload data button style").
- `app/client/src/main.ts` - Contains `initializeQueryInput()`, `initializeFileUpload()`, etc., wired up in the `DOMContentLoaded` listener. Add a new `initializeRandomQueryButton()` function following the same async/disabled-state/loading-spinner pattern used by the Query button.
- `app/client/src/api/client.ts` - Contains the `api` object with typed methods (`processQuery`, `uploadFile`, etc.) wrapping `apiRequest<T>`. Add a `generateRandomQuery` method here.
- `app/client/src/types.d.ts` - Contains TypeScript interfaces mirroring the Pydantic models exactly. Add `RandomQueryRequest` and `RandomQueryResponse` interfaces here.
- `.claude/commands/test_e2e.md` - Read this to understand how the E2E test runner executes an E2E test file (Playwright automation, screenshot conventions, output format).
- `.claude/commands/e2e/test_basic_query.md` - Read this as the reference example for the format/style of a new E2E test file (User Story, Test Steps, Success Criteria).

### New Files
- `app/server/tests/core/test_llm_processor_random_query.py` - New unit tests for `generate_random_query_with_openai`, `generate_random_query_with_anthropic`, and `generate_random_query` routing (alternatively these tests can be added directly to `test_llm_processor.py`; see Notes).
- `.claude/commands/e2e/test_random_query_button.md` - New E2E test file validating the Random Query button populates the input field, overwrites existing text, and works with an empty database.

## Implementation Plan
### Phase 1: Foundation
Add the new Pydantic request/response models (`RandomQueryRequest`, `RandomQueryResponse`) and matching TypeScript interfaces so both backend and frontend have a typed contract for the new endpoint before any logic is written.

### Phase 2: Core Implementation
Implement the schema-aware natural-language-question generation in `core/llm_processor.py` (OpenAI + Anthropic variants plus the routing function and a two-sentence enforcement helper), wire it into a new `POST /api/random-query` FastAPI endpoint in `server.py` that reuses `get_database_schema()`, and add unit tests covering success, markdown cleanup, no-tables, no-API-key, and provider-routing cases.

### Phase 3: Integration
Add the "Random Query" button to the client UI (HTML + CSS placement/style), wire up its click handler in `main.ts` to call the new API client method and always overwrite the query textarea, add the API client method + types, create the E2E test file, and run the full validation suite (backend tests, frontend typecheck/build, E2E test) to confirm zero regressions.

## Step by Step Tasks

### 1. Add backend data models
- In `app/server/core/data_models.py`, add:
  ```python
  class RandomQueryRequest(BaseModel):
      llm_provider: Literal["openai", "anthropic"] = "openai"

  class RandomQueryResponse(BaseModel):
      query: str
      error: Optional[str] = None
  ```
  Place these near the existing Query Models section for consistency.

### 2. Add matching TypeScript types
- In `app/client/src/types.d.ts`, add matching interfaces directly below the existing Query Types section:
  ```typescript
  interface RandomQueryRequest {
    llm_provider: "openai" | "anthropic";
  }

  interface RandomQueryResponse {
    query: string;
    error?: string;
  }
  ```

### 3. Implement schema-aware random query generation in `llm_processor.py`
- Add `generate_random_query_with_openai(schema_info: Dict[str, Any]) -> str`: reuses `format_schema_for_prompt(schema_info)`, builds a prompt asking the model to propose one interesting, specific natural-language question about the data (mention real table/column names, favor aggregations/filters/comparisons that are actually answerable given the schema), with explicit rules: "Return ONLY the natural language question, no explanations or quotes", "Do not include SQL syntax", "Limit your response to two sentences maximum". Call the OpenAI client the same way `generate_sql_with_openai` does (same model, low-ish temperature but slightly higher, e.g. `0.7`, to get varied/interesting suggestions — since this is not deterministic SQL generation).
- Add `generate_random_query_with_anthropic(schema_info: Dict[str, Any]) -> str`: mirror structure using the Anthropic client exactly like `generate_sql_with_anthropic`.
- Both functions must strip markdown fences the same way the existing `generate_sql_with_*` functions do, then pass the result through a new helper `truncate_to_two_sentences(text: str) -> str` as a safety net (split on `.`, `!`, `?` sentence terminators, keep at most the first two sentences, and reassemble) in case the LLM does not respect the two-sentence instruction. Raise a wrapped `Exception` on failure, matching the existing error-message conventions (e.g. `f"Error generating random query with OpenAI: {str(e)}"`).
- Add `generate_random_query(schema_info: Dict[str, Any], llm_provider: str = "openai") -> str`: identical routing priority to `generate_sql` (OpenAI key present → OpenAI; else Anthropic key present → Anthropic; else fall back to `llm_provider` preference).
- Raise a clear `ValueError`/`Exception` (e.g. `"No tables available to generate a query suggestion"`) when `schema_info.get('tables')` is empty, so the caller can surface a friendly error — this check can live in `generate_random_query` itself so both server and tests exercise the same guard.

### 4. Add backend unit tests
- Add tests (in `app/server/tests/core/test_llm_processor.py` or the new `test_llm_processor_random_query.py`) mirroring the structure of the existing `TestLLMProcessor` class:
  - `generate_random_query_with_openai` success case (mock client, assert prompt built from schema, assert result returned).
  - Markdown cleanup case for both providers.
  - No API key raises exception for both providers.
  - API error wraps exception message for both providers.
  - `truncate_to_two_sentences` correctly truncates a 3+ sentence string to 2, and leaves a 1-2 sentence string unchanged.
  - `generate_random_query` routing: OpenAI priority, Anthropic fallback, request-preference fallback when neither key set (mirrors `test_generate_sql_*` tests).
  - `generate_random_query` raises/returns an error when `schema_info['tables']` is empty.

### 5. Add the `/api/random-query` endpoint
- In `app/server/server.py`, import `RandomQueryRequest`, `RandomQueryResponse` from `core.data_models` and `generate_random_query` from `core.llm_processor`.
- Add:
  ```python
  @app.post("/api/random-query", response_model=RandomQueryResponse)
  async def generate_random_query_endpoint(request: RandomQueryRequest) -> RandomQueryResponse:
      """Generate a random natural language query suggestion based on the current schema"""
      try:
          schema_info = get_database_schema()
          if not schema_info.get('tables'):
              raise Exception("No tables available. Upload data first to generate a query suggestion.")

          query = generate_random_query(schema_info, request.llm_provider)

          response = RandomQueryResponse(query=query)
          logger.info(f"[SUCCESS] Random query generated: {query}")
          return response
      except Exception as e:
          logger.error(f"[ERROR] Random query generation failed: {str(e)}")
          logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
          return RandomQueryResponse(query="", error=str(e))
  ```
  Place it directly after `process_natural_language_query` for readability.

### 6. Add the frontend API client method
- In `app/client/src/api/client.ts`, add to the `api` object:
  ```typescript
  // Generate a random natural language query suggestion
  async generateRandomQuery(request: RandomQueryRequest = { llm_provider: 'openai' }): Promise<RandomQueryResponse> {
    return apiRequest<RandomQueryResponse>('/random-query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(request)
    });
  },
  ```

### 7. Add the button to the UI markup
- In `app/client/index.html`, restructure the `.query-controls` div so the existing Query + Upload Data buttons are grouped together and the new Random Query button is separated apart via flex justification:
  ```html
  <div class="query-controls">
    <div class="query-controls-primary">
      <button id="query-button" class="primary-button">Query</button>
      <button id="upload-data-button" class="secondary-button">Upload Data</button>
    </div>
    <button id="random-query-button" class="secondary-button" title="Generate a random natural language query based on your tables">
      🎲 Random Query
    </button>
  </div>
  ```

### 8. Update styles for the new layout
- In `app/client/src/style.css`, update `.query-controls` to justify its children apart (e.g. `justify-content: space-between;` — it already has `display: flex`), and add a `.query-controls-primary` rule that carries over the original grouping styles (`display: flex; gap: 1rem; align-items: center;`) so the Query/Upload Data buttons stay visually grouped on the left while Random Query sits on the right. No new button-look styles are needed since `.secondary-button` is reused as instructed by the issue.

### 9. Wire up the click handler in `main.ts`
- In `app/client/src/main.ts`, add a new function `initializeRandomQueryButton()` following the same pattern as `initializeQueryInput()`:
  ```typescript
  // Random Query Functionality
  function initializeRandomQueryButton() {
    const randomQueryButton = document.getElementById('random-query-button') as HTMLButtonElement;
    const queryInput = document.getElementById('query-input') as HTMLTextAreaElement;

    randomQueryButton.addEventListener('click', async () => {
      randomQueryButton.disabled = true;
      const originalContent = randomQueryButton.innerHTML;
      randomQueryButton.innerHTML = '<span class="loading"></span>';

      try {
        const response = await api.generateRandomQuery({ llm_provider: 'openai' });

        if (response.error) {
          displayError(response.error);
        } else {
          // Always overwrite whatever is currently in the field
          queryInput.value = response.query;
        }
      } catch (error) {
        displayError(error instanceof Error ? error.message : 'Failed to generate a random query');
      } finally {
        randomQueryButton.disabled = false;
        randomQueryButton.innerHTML = originalContent;
      }
    });
  }
  ```
- Register it in the `DOMContentLoaded` listener alongside the other `initialize*` calls:
  ```typescript
  document.addEventListener('DOMContentLoaded', () => {
    initializeQueryInput();
    initializeFileUpload();
    initializeModal();
    initializeRandomQueryButton();
    loadDatabaseSchema();
  });
  ```

### 10. Create the E2E test file
- Create `.claude/commands/e2e/test_random_query_button.md` modeled on `.claude/commands/e2e/test_basic_query.md`, covering:
  - Navigating to the app, verifying the "🎲 Random Query" button is visible next to (but visually separated from) the Query/Upload Data buttons.
  - Loading sample data (e.g. "Users Data") first so tables exist.
  - Typing some placeholder text into the query textarea, clicking "Random Query", and verifying the textarea's contents are fully replaced (no longer contains the placeholder text) with a new, non-empty natural-language question.
  - Clicking "Random Query" a second time and verifying the field is overwritten again (not appended).
  - Screenshots: initial state, after loading sample data, after first random query generation (showing populated field), after second generation (showing overwrite).
  - Success criteria: button is visible and enabled, textarea is always overwritten (never appended to), generated text is non-empty and reasonably short (consistent with a two-sentence limit).

### 11. Run full validation
- Execute every command in `Validation Commands` below and confirm all pass with zero regressions.

## Testing Strategy
### Unit Tests
- `generate_random_query_with_openai` / `generate_random_query_with_anthropic`: success, markdown-fence cleanup, missing API key, upstream API exception wrapping (mirrors existing `generate_sql_with_*` tests).
- `truncate_to_two_sentences`: input with 1, 2, and 4+ sentences produces correctly bounded output; input with no terminal punctuation is returned unchanged.
- `generate_random_query` routing: OpenAI-key priority, Anthropic-only fallback, request-preference fallback when neither key is set, and the "no tables" guard raising/returning an error.
- Server-level: a lightweight test (or manual curl) of `POST /api/random-query` confirming it returns `RandomQueryResponse` shape and populates `error` when no tables exist (can be added to an existing server test module if one exists, otherwise validated via the E2E test and manual curl).

### Edge Cases
- No tables in the database yet (fresh install / after deleting all tables) → endpoint returns a friendly `error` message instead of calling the LLM or crashing; frontend shows it via `displayError` and does not touch the textarea.
- Both `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` unset → existing `generate_sql`-style fallback logic surfaces a clear error from the underlying provider function; frontend displays it.
- LLM returns more than two sentences despite prompt instructions → `truncate_to_two_sentences` safety net enforces the limit.
- LLM wraps its answer in markdown/quotes → cleanup logic strips it the same way SQL generation does.
- User has existing text in the query textarea (typed manually or from a previous random query) → clicking "Random Query" always fully overwrites it, never appends.
- Rapid double-click on the button → button is `disabled` during the in-flight request, preventing duplicate calls.
- Very large schema (many tables/columns) → reuses the same `format_schema_for_prompt` used by SQL generation, so behavior is consistent with existing query generation at scale.

## Acceptance Criteria
- A new "🎲 Random Query" button appears in the query controls area, styled identically to the "Upload Data" secondary button, visually separated (justified apart) from the Query/Upload Data button group.
- Clicking the button calls `POST /api/random-query`, which uses `core/llm_processor.py` and the live database schema to generate a natural-language question referencing real tables/columns.
- The generated question always fully overwrites the query textarea's current contents (never appends).
- The generated question is limited to a maximum of two sentences.
- When no tables exist, the button surfaces a clear error instead of crashing or silently doing nothing.
- All existing backend and frontend tests continue to pass with zero regressions.
- New unit tests for the random-query generation and routing logic pass.
- New E2E test `test_random_query_button.md` passes, demonstrating the button populates and overwrites the query field, with supporting screenshots.

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd app/server && uv run pytest` - Run server tests to validate the feature works with zero regressions
- `cd app/server && uv run pytest tests/core/test_llm_processor.py -v` (or the new test file, if created separately) - Validate the new random-query generation logic specifically
- `cd app/client && bun tsc --noEmit` - Run frontend typecheck to validate the feature works with zero regressions
- `cd app/client && bun run build` - Run frontend build to validate the feature works with zero regressions
- Read `.claude/commands/test_e2e.md`, then read and execute the new `.claude/commands/e2e/test_random_query_button.md` test file to validate this functionality works end-to-end, including screenshots proving the button populates and overwrites the query field.

## Notes
- Reuses the existing `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` env-based provider priority already established by `generate_sql`, so no new environment variables or libraries are required (no `uv add` needed).
- The random-query prompt should explicitly instruct the LLM not to emit SQL — this feature is about suggesting a *natural language* question, not a SQL query, to populate the textarea that the user still submits via the existing "Query" button.
- The two-sentence limit is enforced both via the prompt instructions and defensively via a `truncate_to_two_sentences` helper, matching the existing defensive-cleanup pattern already used for markdown fences in `generate_sql_with_openai`/`generate_sql_with_anthropic`.
- Consider (future enhancement, out of scope here) letting users pick which table the random query should focus on; for v1, the LLM sees the full schema (all tables) and picks what it finds most interesting, consistent with how `generate_sql` already receives the full schema for every query.
