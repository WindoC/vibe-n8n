#!/usr/bin/env python3
import argparse
import json
import os
import sys
from typing import Any, Dict, Optional
from urllib import error, parse, request


def _build_api_base(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/api/v1"):
        return base
    return f"{base}/api/v1"


def _read_json_file(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json_file(path: str, payload: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=True)
        f.write("\n")


def _load_dotenv(path: str = ".env") -> None:
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


class N8nClient:
    def __init__(self, base_url: str, api_key: str, timeout: int = 30) -> None:
        self.base_url = _build_api_base(base_url)
        self.api_key = api_key
        self.timeout = timeout

    def request_json(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Any:
        clean_path = path if path.startswith("/") else f"/{path}"
        url = f"{self.base_url}{clean_path}"
        if params:
            filtered = {k: self._normalize_query_value(v) for k, v in params.items() if v is not None}
            if filtered:
                url = f"{url}?{parse.urlencode(filtered, doseq=True)}"

        body = None
        headers = {"X-N8N-API-KEY": self.api_key, "Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(url=url, data=body, headers=headers, method=method.upper())
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
                if not raw:
                    return {}
                return json.loads(raw.decode("utf-8"))
        except error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                details = json.loads(raw)
            except json.JSONDecodeError:
                details = {"message": raw}
            raise RuntimeError(
                f"HTTP {exc.code} {exc.reason} for {method.upper()} {url}: {json.dumps(details, ensure_ascii=True)}"
            ) from exc
        except error.URLError as exc:
            raise RuntimeError(f"Request failed for {method.upper()} {url}: {exc.reason}") from exc

    @staticmethod
    def _normalize_query_value(value: Any) -> Any:
        if isinstance(value, bool):
            return "true" if value else "false"
        return value


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=True))


def _workflow_view(client: N8nClient, args: argparse.Namespace) -> None:
    result = client.request_json(
        "GET",
        f"/workflows/{args.id}",
        params={"excludePinnedData": args.exclude_pinned_data},
    )
    _print_json(result)


def _workflow_download(client: N8nClient, args: argparse.Namespace) -> None:
    result = client.request_json(
        "GET",
        f"/workflows/{args.id}",
        params={"excludePinnedData": args.exclude_pinned_data},
    )
    _write_json_file(args.out, result)
    print(f"Saved workflow {args.id} to {args.out}")


def _workflow_create(client: N8nClient, args: argparse.Namespace) -> None:
    payload = _read_json_file(args.file)
    result = client.request_json("POST", "/workflows", payload=payload)
    _print_json(result)


def _workflow_edit(client: N8nClient, args: argparse.Namespace) -> None:
    payload = _read_json_file(args.file)
    result = client.request_json("PUT", f"/workflows/{args.id}", payload=payload)
    _print_json(result)


def _workflow_delete(client: N8nClient, args: argparse.Namespace) -> None:
    result = client.request_json("DELETE", f"/workflows/{args.id}")
    _print_json(result)


def _execution_list(client: N8nClient, args: argparse.Namespace) -> None:
    params: Dict[str, Any] = {
        "includeData": args.include_data,
        "status": args.status,
        "workflowId": args.workflow_id,
        "projectId": args.project_id,
        "limit": args.limit,
        "cursor": args.cursor,
    }
    first = client.request_json("GET", "/executions", params=params)
    if not args.all_pages:
        _print_json(first)
        return

    data = list(first.get("data", []))
    next_cursor = first.get("nextCursor")
    while next_cursor:
        page = client.request_json(
            "GET",
            "/executions",
            params={
                "includeData": args.include_data,
                "status": args.status,
                "workflowId": args.workflow_id,
                "projectId": args.project_id,
                "limit": args.limit,
                "cursor": next_cursor,
            },
        )
        data.extend(page.get("data", []))
        next_cursor = page.get("nextCursor")

    _print_json({"data": data, "nextCursor": None})


def _execution_get(client: N8nClient, args: argparse.Namespace) -> None:
    result = client.request_json(
        "GET",
        f"/executions/{args.id}",
        params={"includeData": args.include_data},
    )
    _print_json(result)


def _execution_delete(client: N8nClient, args: argparse.Namespace) -> None:
    result = client.request_json("DELETE", f"/executions/{args.id}")
    _print_json(result)


def _execution_retry(client: N8nClient, args: argparse.Namespace) -> None:
    payload = {}
    if args.load_workflow:
        payload["loadWorkflow"] = True
    result = client.request_json("POST", f"/executions/{args.id}/retry", payload=payload or None)
    _print_json(result)


def _execution_stop(client: N8nClient, args: argparse.Namespace) -> None:
    result = client.request_json("POST", f"/executions/{args.id}/stop")
    _print_json(result)


def _execution_stop_many(client: N8nClient, args: argparse.Namespace) -> None:
    statuses = [x.strip() for x in args.status.split(",") if x.strip()]
    if not statuses:
        raise ValueError("At least one status is required for stop-many.")
    payload: Dict[str, Any] = {"status": statuses}
    if args.workflow_id:
        payload["workflowId"] = args.workflow_id
    if args.started_after:
        payload["startedAfter"] = args.started_after
    if args.started_before:
        payload["startedBefore"] = args.started_before

    result = client.request_json("POST", "/executions/stop", payload=payload)
    _print_json(result)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="n8n Workflow and Execution API helper.",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("N8N_BASE_URL") or os.getenv("base_url"),
        help="n8n instance base URL, e.g. https://n8n.example.com (or include /api/v1).",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("N8N_API_KEY") or os.getenv("key"),
        help="n8n API key. Falls back to N8N_API_KEY env var.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="HTTP timeout in seconds. Default: 30.",
    )

    resource = parser.add_subparsers(dest="resource", required=True)

    workflow = resource.add_parser("workflow", help="Workflow operations")
    wf_cmd = workflow.add_subparsers(dest="action", required=True)

    wf_view = wf_cmd.add_parser("view", help="View workflow JSON by ID")
    wf_view.add_argument("--id", required=True, help="Workflow ID")
    wf_view.add_argument(
        "--exclude-pinned-data",
        action="store_true",
        help="Exclude pinned data from workflow response.",
    )
    wf_view.set_defaults(func=_workflow_view)

    wf_download = wf_cmd.add_parser("download", help="Download workflow JSON to file")
    wf_download.add_argument("--id", required=True, help="Workflow ID")
    wf_download.add_argument("--out", required=True, help="Output JSON file path")
    wf_download.add_argument(
        "--exclude-pinned-data",
        action="store_true",
        help="Exclude pinned data from workflow response.",
    )
    wf_download.set_defaults(func=_workflow_download)

    wf_create = wf_cmd.add_parser("create", help="Create workflow from JSON file")
    wf_create.add_argument("--file", required=True, help="Input JSON file with workflow payload")
    wf_create.set_defaults(func=_workflow_create)

    wf_edit = wf_cmd.add_parser("edit", help="Edit workflow from JSON file")
    wf_edit.add_argument("--id", required=True, help="Workflow ID")
    wf_edit.add_argument("--file", required=True, help="Input JSON file with updated workflow payload")
    wf_edit.set_defaults(func=_workflow_edit)

    wf_delete = wf_cmd.add_parser("delete", help="Delete workflow by ID")
    wf_delete.add_argument("--id", required=True, help="Workflow ID")
    wf_delete.set_defaults(func=_workflow_delete)

    execution = resource.add_parser("execution", help="Execution operations")
    ex_cmd = execution.add_subparsers(dest="action", required=True)

    ex_list = ex_cmd.add_parser("list", help="List executions")
    ex_list.add_argument("--include-data", action="store_true", help="Include execution data")
    ex_list.add_argument(
        "--status",
        choices=["canceled", "error", "running", "success", "waiting"],
        help="Filter by status",
    )
    ex_list.add_argument("--workflow-id", help="Filter by workflow ID")
    ex_list.add_argument("--project-id", help="Filter by project ID")
    ex_list.add_argument("--limit", type=int, default=100, help="Items per page (max 250)")
    ex_list.add_argument("--cursor", help="Cursor for pagination")
    ex_list.add_argument("--all-pages", action="store_true", help="Auto-follow nextCursor")
    ex_list.set_defaults(func=_execution_list)

    ex_get = ex_cmd.add_parser("get", help="Get execution by ID")
    ex_get.add_argument("--id", required=True, type=int, help="Execution ID")
    ex_get.add_argument("--include-data", action="store_true", help="Include execution data")
    ex_get.set_defaults(func=_execution_get)

    ex_delete = ex_cmd.add_parser("delete", help="Delete execution by ID")
    ex_delete.add_argument("--id", required=True, type=int, help="Execution ID")
    ex_delete.set_defaults(func=_execution_delete)

    ex_retry = ex_cmd.add_parser("retry", help="Retry execution by ID")
    ex_retry.add_argument("--id", required=True, type=int, help="Execution ID")
    ex_retry.add_argument(
        "--load-workflow",
        action="store_true",
        help="Retry with latest saved workflow definition.",
    )
    ex_retry.set_defaults(func=_execution_retry)

    ex_stop = ex_cmd.add_parser("stop", help="Stop a running execution by ID")
    ex_stop.add_argument("--id", required=True, type=int, help="Execution ID")
    ex_stop.set_defaults(func=_execution_stop)

    ex_stop_many = ex_cmd.add_parser("stop-many", help="Stop multiple executions")
    ex_stop_many.add_argument(
        "--status",
        required=True,
        help="Comma-separated statuses: queued,running,waiting",
    )
    ex_stop_many.add_argument("--workflow-id", help="Optional workflow ID filter")
    ex_stop_many.add_argument("--started-after", help="ISO datetime filter")
    ex_stop_many.add_argument("--started-before", help="ISO datetime filter")
    ex_stop_many.set_defaults(func=_execution_stop_many)

    return parser


def main() -> int:
    _load_dotenv(".env")
    parser = build_parser()
    args = parser.parse_args()

    if not args.base_url:
        parser.error("Missing --base-url (or N8N_BASE_URL env var).")
    if not args.api_key:
        parser.error("Missing --api-key (or N8N_API_KEY env var).")

    if hasattr(args, "limit") and args.limit > 250:
        parser.error("--limit must be <= 250 for n8n API.")

    client = N8nClient(base_url=args.base_url, api_key=args.api_key, timeout=args.timeout)

    try:
        args.func(client, args)
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
