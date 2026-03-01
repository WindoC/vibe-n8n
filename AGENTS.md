# AGENTS Memory

## Project Conventions
- Use `uv` for Python management.
- Create environment with `uv venv`.
- Run Python commands with `uv run`.
- Prefer built-in file edit tools for file changes.

## Skill Location
- Repo-local skills live in `.agents/skills/`.
- Current skill name: `n8n`.
- Main skill file: `.agents/skills/n8n/SKILL.md`.

## n8n API Setup
- Keep runtime API config in `.env`.
- Required keys:
  - `N8N_BASE_URL`
  - `N8N_API_KEY`
- Do not commit secrets. `.env` are ignored in `.gitignore`.

## Main Script
- API helper script: `.agents/skills/n8n/scripts/n8n_api.py`
- Current implemented scopes:
  - Workflow: `view`, `download`, `create`, `edit`, `delete`
  - Execution: `list`, `get`, `delete`, `retry`, `stop`, `stop-many`

## API Specification File
- Repo root file: `api-1.json`
- Purpose: OpenAPI document used by the n8n API reference site (`https://docs.n8n.io/api/api-reference/`), stored in this repo for local use.
- Use this file as the source of truth when:
  - selecting endpoints and HTTP methods
  - validating request body shape and required fields
  - checking query/path parameters and constraints
  - confirming response/error schema details
- Skill guidance should prefer `api-1.json` over memory when exact payload or field support is uncertain.

## Workflow Template Corpus
- Primary template/example folder for vibe-coding n8n workflows: `workflow/`
- Treat `workflow/*.json` as the first reference corpus when asked to generate or revise workflows.
- Preferred process:
  1. Analyze existing `workflow/*.json` node patterns and connections.
  2. Reuse proven node wiring from these examples.
  3. Generate new workflow JSON into `workflow/` before upload/edit via API.
- If examples are insufficient, export workflows first with `uv run scripts/export_workflows.py`, then re-run analysis.

## Public repo checklist

Use this checklist before publishing or updating this repository on GitHub:

1. Add a license file (`LICENSE`) and mention it in the repo description.
2. Keep secrets out of git:
   - Never commit `.env`, API keys, tokens, or credential exports.
   - Verify `.gitignore` includes all local secret files.
3. Keep examples safe:
   - Remove or anonymize chat IDs, webhook URLs, internal hostnames, and user identifiers in shared workflow JSON files.
   - Avoid committing production credential IDs unless they are already invalid/sanitized.
4. Provide reproducible setup:
   - Keep `.env.example` minimal and non-sensitive.
   - Ensure all commands in `README.md` run with `uv run`.
5. Add validation checks in CI (recommended):
   - JSON validity check for `workflow/*.json`.
   - Optional lint/check for docs and scripts.
6. Document contribution rules:
   - Ask contributors to add new workflow references under `workflow/`.
   - Ask contributors to update docs when adding new generation patterns.
7. Tag repository scope clearly:
   - State this is a Codex-focused skill example and may require conversion for other assistants.
