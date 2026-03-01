# vibe-n8n

Practical example repository for generating and managing n8n workflows with an OpenAI Codex skill plus a small n8n API helper script.

## What this repo is for

- Build a local reference corpus of real workflow JSON files.
- Let Codex analyze node usage and wiring patterns.
- Generate new workflows from that learned pattern.
- Upload, edit, and activate workflows through the n8n Public API.

## Example captures

<p align="center">
  <img src="./example_en.png" alt="Workflow generation example" width="32%" />
  <img src="./example_cn_1.png" alt="Workflow capture 1" width="32%" />
  <img src="./example_cn_2.png" alt="Workflow capture 2" width="32%" />
</p>

## Important: Do this first

Before asking Codex to generate workflows, collect real workflow examples.
Without reference examples, output quality will be much lower.

First choice (recommended):

1. Export workflows directly from your own n8n instance with:
```powershell
uv run scripts/export_workflows.py
```

Alternative:

1. Download template workflows from a public source, for example:
   `https://github.com/enescingoz/awesome-n8n-templates`

Then place JSON files in `workflow/` and ask Codex to analyze them first.

## Requirements

- `uv` installed
- Access to an n8n instance with a Public API key

## Setup

1. Create environment:
```powershell
uv venv
```

2. Create local config file:
```powershell
Copy-Item .env.example .env
```

3. Link this repo to your n8n API key:
   - In your n8n main page, go to:
     `Settings -> n8n API -> Create an API Key`
   - Use:
     - `Label`: `codex`
     - `Expiration`: `No Expiration`
   - Copy the generated key (you will paste it into `.env` in the next step).

4. Set API values in `.env`:
```env
N8N_BASE_URL=https://your-n8n-host/
N8N_API_KEY=replace-with-your-api-key
```

## Core files

- Skill: `.agents/skills/n8n/SKILL.md`
- API helper script: `.agents/skills/n8n/scripts/n8n_api.py`
- API reference notes: `.agents/skills/n8n/references/n8n-reference.md`
- Workflow generation guide from local analysis:
  `.agents/skills/n8n/references/workflow-node-generation-guide.md`

## Export and build your reference corpus

Export all workflows from your instance:
```powershell
uv run scripts/export_workflows.py
```

View one workflow:
```powershell
uv run .agents/skills/n8n/scripts/n8n_api.py workflow view --id <workflowId>
```

Download one workflow JSON:
```powershell
uv run .agents/skills/n8n/scripts/n8n_api.py workflow download --id <workflowId> --out workflow/<name>.json
```

## Recommended Codex workflow generation loop

1. Run `uv run scripts/export_workflows.py` to populate `workflow/*.json` from your n8n instance.
2. Optionally add extra examples from public template repositories.
3. Ask Codex to analyze node purposes and connection patterns.
4. Ask Codex to generate a new workflow JSON file in `workflow/`.
5. Validate and upload:
```powershell
uv run .agents/skills/n8n/scripts/n8n_api.py workflow create --file workflow/<generated>.json
```
6. Update an existing workflow:
```powershell
uv run .agents/skills/n8n/scripts/n8n_api.py workflow edit --id <workflowId> --file workflow/<generated>.json
```
7. Activate after validation:
`POST /workflows/{id}/activate` (Codex can run this for you).

## API helper quick commands

Show help:
```powershell
uv run .agents/skills/n8n/scripts/n8n_api.py --help
```

Workflow operations:
```powershell
uv run .agents/skills/n8n/scripts/n8n_api.py workflow view --id <workflowId>
uv run .agents/skills/n8n/scripts/n8n_api.py workflow create --file workflow.json
uv run .agents/skills/n8n/scripts/n8n_api.py workflow edit --id <workflowId> --file workflow-updated.json
uv run .agents/skills/n8n/scripts/n8n_api.py workflow delete --id <workflowId>
```

Execution operations:
```powershell
uv run .agents/skills/n8n/scripts/n8n_api.py execution list --limit 5
uv run .agents/skills/n8n/scripts/n8n_api.py execution get --id <executionId>
uv run .agents/skills/n8n/scripts/n8n_api.py execution retry --id <executionId> --load-workflow
uv run .agents/skills/n8n/scripts/n8n_api.py execution stop --id <executionId>
```

## Tool compatibility note

This repository is an **OpenAI Codex-oriented example**.
The skill layout and workflow may not work as-is in other coding assistants.

If you use another tool, ask that tool to:

1. Convert this skill structure into its own skill/agent format.
2. Preserve the same n8n API guardrails and workflow-generation rules.
3. Re-map file paths and command conventions as needed.

## Prompt example for Codex

Simple prompt:

`Create a workflow that summarizes important daily news and sends it to my Telegram, then upload it to n8n.`

Stronger prompt (recommended):

`Please analyze workflow/*.json first, then generate an n8n workflow that collects important daily news and sends one summary message to Telegram. Use multi-source RSS, keep only today's items, deduplicate by URL, and include both Schedule Trigger and Manual Trigger. Save JSON under workflow/, upload it to n8n using .agents/skills/n8n/scripts/n8n_api.py, and report the created workflow ID plus activation status.`

Why this works better:

- It forces analysis-first behavior using local references.
- It defines concrete functional requirements.
- It requires file output, upload, and verifiable completion details.
