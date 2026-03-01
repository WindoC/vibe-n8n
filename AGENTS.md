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
- Do not commit secrets. `.env` and `auth.txt` are ignored in `.gitignore`.

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
