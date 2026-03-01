# n8n API Reference (Condensed)

## Canonical docs
- Public API docs: https://docs.n8n.io/api/
- API playground pattern: `https://<your-n8n-host>/api/v1/docs`
- Repo `api-1.json`: OpenAPI document used to power the n8n API reference pages.

## Base URL and auth
- Base path: `/api/v1`
- Auth header: `X-N8N-API-KEY: <your-api-key>`
- OpenAPI server entry in this repo (`api-1.json`): `"/api/v1"`
- Local env defaults:
  - `N8N_BASE_URL`
  - `N8N_API_KEY`

## Pagination and limits
- List endpoints use cursor pagination.
- Query params:
  - `limit` default `100`, max `250`
  - `cursor` for next page
- Read `nextCursor` from response and continue until null.

## Common resource groups in `api-1.json`
- `Workflow`: CRUD and transfer
- `Execution`: list/get/delete/retry/stop (single and bulk stop)
- `Credential`: CRUD, schema lookup, transfer
- `User`: list and access user information
- `Projects`: list projects and members
- `Variables`: CRUD
- `Tags`: CRUD
- `DataTable`: tables and rows operations
- `Audit`: security audit generation
- `SourceControl`: source control operations

## Error handling defaults
- `400`: malformed request or validation issue
- `401`: missing/invalid API key
- `403`: permission denied
- `404`: resource not found
- `409`: conflict (for specific operations such as retries)

## Request construction checklist
1. Build URL as `{instance}/api/v1/<resource>`.
2. Set headers:
   - `X-N8N-API-KEY`
   - `Content-Type: application/json` when body is present
3. Validate required path/query/body parameters from `api-1.json`.
4. For mutations, optionally perform a preflight GET to verify target IDs.
5. Return status code and parsed error body on failure.

## Local helper script
- Use `.agents/skills/n8n/scripts/n8n_api.py` for initial implementation scope:
  - Workflow: `view`, `download`, `create`, `edit`, `delete`
  - Execution: `list`, `get`, `delete`, `retry`, `stop`, `stop-many`
