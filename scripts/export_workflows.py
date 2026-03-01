#!/usr/bin/env python3
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional
from urllib import error, parse, request


def load_dotenv(path: Path) -> Dict[str, str]:
    env: Dict[str, str] = {}
    if not path.exists():
        return env
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            env[key] = value
    return env


def normalize_api_base(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/api/v1"):
        return base
    return f"{base}/api/v1"


def api_get_json(url: str, api_key: str) -> Dict:
    headers = {
        "X-N8N-API-KEY": api_key,
        "Accept": "application/json",
    }
    req = request.Request(url=url, headers=headers, method="GET")
    try:
        with request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            return json.loads(raw.decode("utf-8")) if raw else {}
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} {exc.reason} for GET {url}: {details}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Request failed for GET {url}: {exc.reason}") from exc


def sanitize_name(name: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", name).strip("_")
    return safe or "workflow"


def fetch_all_workflows(api_base: str, api_key: str, limit: int = 100) -> List[Dict]:
    workflows: List[Dict] = []
    cursor: Optional[str] = None

    while True:
        params = {"limit": str(limit)}
        if cursor:
            params["cursor"] = cursor
        qs = parse.urlencode(params)
        url = f"{api_base}/workflows?{qs}"
        payload = api_get_json(url, api_key)
        items = payload.get("data") or []
        workflows.extend(items)
        cursor = payload.get("nextCursor")
        if not cursor:
            break
    return workflows


def export_workflows(workflows: List[Dict], out_dir: Path) -> int:
    if out_dir.exists():
        for p in out_dir.glob("*.json"):
            p.unlink()
    else:
        out_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for idx, wf in enumerate(workflows, start=1):
        wf_id = str(wf.get("id") or "").strip()
        if not wf_id:
            continue
        name = str(wf.get("name") or "workflow")
        filename = f"{idx:04d}_{sanitize_name(name)}_{wf_id}.json"
        out_path = out_dir / filename
        out_path.write_text(json.dumps(wf, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        count += 1
    return count


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    os.chdir(repo_root)

    env_path = repo_root / ".env"
    env_file = load_dotenv(env_path)
    for k, v in env_file.items():
        os.environ.setdefault(k, v)

    base_url = os.getenv("N8N_BASE_URL")
    api_key = os.getenv("N8N_API_KEY")
    if not base_url or not api_key:
        print("Error: N8N_BASE_URL or N8N_API_KEY missing (.env or environment).", file=sys.stderr)
        return 1

    api_base = normalize_api_base(base_url)
    workflows = fetch_all_workflows(api_base=api_base, api_key=api_key, limit=100)
    out_dir = repo_root / "workflow"
    downloaded = export_workflows(workflows, out_dir)

    print(f"Listed workflows: {len(workflows)}")
    print(f"Downloaded workflows: {downloaded}")
    print("Output folder: ./workflow")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
