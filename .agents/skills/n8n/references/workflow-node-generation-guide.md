# n8n Workflow Node Generation Guide (Derived from `workflow/*.json`)

This guide is built from local repository analysis of `161` workflow JSON files.
Use it as a practical reference for generating valid n8n workflows and for building Codex skills that output workflow JSON.

## 1. Dataset Scope and Method

- Source: `workflow/*.json`
- Workflow files analyzed: `161`
- Total nodes analyzed: `2120`
- Unique node types observed: `97`
- Connection edges observed:
  - `main`: `1600`
  - `ai_languageModel`: `62`
  - `ai_tool`: `54`
  - `ai_embedding`: `23`
  - `ai_memory`: `22`
  - `ai_textSplitter`: `18`
  - `ai_document`: `16`
  - `ai_outputParser`: `6`
  - `ai_vectorStore`: `2`

## 2. Minimum Valid Workflow Shape

From `api-1.json` (`POST /workflows`), required fields are:

- `name`
- `nodes`
- `connections`
- `settings`

Minimal payload template:

```json
{
  "name": "Generated Workflow",
  "nodes": [
    {
      "id": "manual-trigger-1",
      "name": "Manual Trigger",
      "type": "n8n-nodes-base.manualTrigger",
      "typeVersion": 1,
      "position": [260, 300],
      "parameters": {}
    }
  ],
  "connections": {},
  "settings": {
    "executionOrder": "v1"
  }
}
```

Notes:

- Exported workflows contain many metadata fields (`id`, `createdAt`, `updatedAt`, `versionId`, `shared`, etc.). They are not required for generation.
- In this repo, `settings.executionOrder = "v1"` is used in almost all workflows.

## 3. Connection Model You Must Generate Correctly

### 3.1 Standard flow edges (`main`)

```json
{
  "Webhook": {
    "main": [
      [
        { "node": "Edit Fields", "type": "main", "index": 0 }
      ]
    ]
  }
}
```

### 3.2 AI port edges (`ai_*`)

`@n8n/n8n-nodes-langchain.*` workflows frequently use non-`main` channels. Example:

```json
{
  "Ollama": {
    "ai_languageModel": [
      [
        { "node": "Summarization", "type": "ai_languageModel", "index": 0 }
      ]
    ]
  },
  "Wikipedia": {
    "ai_tool": [
      [
        { "node": "research agent", "type": "ai_tool", "index": 0 }
      ]
    ]
  },
  "Simple Memory": {
    "ai_memory": [
      [
        { "node": "AI Agent", "type": "ai_memory", "index": 0 }
      ]
    ]
  }
}
```

If your generated AI workflow wires only `main`, it will often be structurally wrong.

## 4. Practical Wiring Patterns (Observed)

Most common trigger starters:

- `manualTrigger -> set`
- `chatTrigger -> agent`
- `scheduleTrigger -> executeWorkflow`
- `executeWorkflowTrigger -> httpRequest`
- `webhook -> splitOut` or `webhook -> set`

Frequent 3-node motifs:

- `httpRequest -> html -> splitOut`
- `set -> if -> merge`
- `set -> if -> telegram`
- `googleSheets -> compareDatasets -> merge`
- `supabase -> splitInBatches -> supabase`
- `scheduleTrigger -> rssFeedRead -> set`

Reliability settings patterns used in this repo:

- `onError: continueErrorOutput` or `continueRegularOutput`
- `retryOnFail: true`
- `maxTries: 2` (most common)
- `waitBetweenTries: 5000`
- `executeOnce: true` for side-effect nodes

## 5. High-Frequency Node Wiring Reference (`count >= 10`)

| Node type | Count | Key params | Typical upstream | Typical downstream | Channels |
|---|---:|---|---|---|---|
| `n8n-nodes-base.set` | 279 | `options, assignments, assignments.assignments` | manualTrigger, html | merge, httpRequest | `src:main:265; tgt:main:274` |
| `n8n-nodes-base.httpRequest` | 126 | `options, url, authentication` | set, executeWorkflowTrigger | html, splitOut | `src:main:100; tgt:main:131` |
| `n8n-nodes-base.merge` | 103 | `mode, options, combineBy` | set, summarize | set, merge | `src:main:103; tgt:main:250` |
| `n8n-nodes-base.manualTrigger` | 89 | `-` | - | set, httpRequest | `src:main:89` |
| `n8n-nodes-base.postgres` | 75 | `options, operation, schema` | set, executeWorkflowTrigger | merge, splitInBatches | `src:main:56; tgt:main:79` |
| `n8n-nodes-base.executeWorkflow` | 71 | `options, workflowId, workflowId.__rl` | scheduleTrigger, executeWorkflow | set, executeWorkflow | `src:main:49; tgt:main:78` |
| `n8n-nodes-base.supabase` | 69 | `tableId, operation, filters` | merge, splitInBatches | splitInBatches, merge | `src:main:55; tgt:main:72` |
| `n8n-nodes-base.if` | 66 | `conditions, conditions.combinator, conditions.conditions` | set, merge | merge, set | `src:main:66; tgt:main:74` |
| `n8n-nodes-base.googleSheets` | 65 | `documentId, documentId.__rl, documentId.mode` | scheduleTrigger, merge | compareDatasets, splitInBatches | `src:main:54; tgt:main:70` |
| `n8n-nodes-base.html` | 61 | `extractionValues, extractionValues.values, extractionValues.values[]` | httpRequest, splitOut | set, splitOut | `src:main:59; tgt:main:61` |
| `n8n-nodes-base.executeWorkflowTrigger` | 58 | `workflowInputs, workflowInputs.values, workflowInputs.values[]` | - | httpRequest, ssh | `src:main:58` |
| `n8n-nodes-base.filter` | 57 | `conditions, conditions.combinator, conditions.conditions` | googleSheets, splitOut | set, limit | `src:main:57; tgt:main:58` |
| `n8n-nodes-base.splitOut` | 55 | `fieldToSplitOut, options` | html, set | set, splitInBatches | `src:main:55; tgt:main:55` |
| `n8n-nodes-base.summarize` | 51 | `fieldsToSummarize, fieldsToSummarize.values, fieldsToSummarize.values[]` | compareDatasets, if | merge, executeWorkflow | `src:main:51; tgt:main:52` |
| `n8n-nodes-base.stickyNote` | 50 | `content, height, width` | - | - | `-` |
| `n8n-nodes-base.telegram` | 48 | `chatId, additionalFields, additionalFields.appendAttribution` | if, switch | merge, noOp | `src:main:14; tgt:main:49` |
| `n8n-nodes-base.scheduleTrigger` | 47 | `rule, rule.interval, rule.interval[]` | - | executeWorkflow, httpRequest | `src:main:46` |
| `n8n-nodes-base.code` | 46 | `jsCode, mode, language` | merge, html | httpRequest, switch | `src:main:39; tgt:main:47` |
| `n8n-nodes-base.github` | 36 | `owner, owner.__rl, owner.mode` | set, executeWorkflowTrigger | extractFromFile, github | `src:main:25; tgt:main:42` |
| `n8n-nodes-base.splitInBatches` | 34 | `options, batchSize` | supabase, wait | supabase, postgres | `src:main:34; tgt:main:87` |
| `@n8n/n8n-nodes-langchain.chatTrigger` | 28 | `options, options.responseMode` | - | agent, set | `src:main:28` |
| `@n8n/n8n-nodes-langchain.lmChatGoogleGemini` | 26 | `options, modelName` | - | - | `src:ai_languageModel:26` |
| `n8n-nodes-base.switch` | 23 | `options, rules, rules.values` | code, splitInBatches | executeWorkflow, noOp | `src:main:23; tgt:main:31` |
| `n8n-nodes-base.compareDatasets` | 22 | `mergeByFields, mergeByFields.values, mergeByFields.values[]` | googleSheets, supabase | summarize, merge | `src:main:22; tgt:main:45` |
| `@n8n/n8n-nodes-langchain.agent` | 22 | `options, options.systemMessage, promptType` | chatTrigger, set | switch, set | `src:main:5; tgt:ai_tool:39; main:25; ai_languageModel:22; ai_memory:15` |
| `n8n-nodes-base.noOp` | 21 | `-` | switch, if | googleSheets, splitInBatches | `src:main:10; tgt:main:24` |
| `n8n-nodes-base.ssh` | 21 | `command, cwd, authentication` | executeWorkflowTrigger, scheduleTrigger | merge, ssh | `src:main:14; tgt:main:26` |
| `@n8n/n8n-nodes-langchain.memoryBufferWindow` | 21 | `sessionIdType, sessionKey` | - | - | `src:ai_memory:21` |
| `@n8n/n8n-nodes-langchain.chainLlm` | 20 | `promptType, text, hasOutputParser` | aggregate, set | set, googleSheets | `src:main:19; tgt:main:20; ai_languageModel:20; ai_outputParser:6` |
| `n8n-nodes-base.wait` | 20 | `amount, path, unit` | supabase, switch | splitInBatches, supabase | `src:main:19; tgt:main:22` |
| `@n8n/n8n-nodes-langchain.lmChatOpenAi` | 19 | `options, model, model.__rl` | - | - | `src:ai_languageModel:19` |
| `n8n-nodes-base.aggregate` | 18 | `options, aggregate, destinationFieldName` | set, executeWorkflowTrigger | chainLlm, set | `src:main:16; tgt:main:17` |
| `n8n-nodes-base.googleDrive` | 18 | `options, operation, driveId` | if, compareDatasets | stopAndError, set | `src:main:12; tgt:main:18` |
| `n8n-nodes-base.extractFromFile` | 16 | `operation, options, options.encoding` | github, httpRequest | set, if | `src:main:16; tgt:main:16` |
| `@n8n/n8n-nodes-langchain.documentDefaultDataLoader` | 16 | `options, jsonData, jsonMode` | - | - | `src:ai_document:16; tgt:ai_textSplitter:14` |
| `n8n-nodes-base.markdown` | 15 | `options, destinationKey, html` | set, httpRequest | httpRequest, set | `src:main:14; tgt:main:15` |
| `@n8n/n8n-nodes-langchain.textSplitterRecursiveCharacterTextSplitter` | 14 | `options, chunkOverlap, options.splitCode` | - | - | `src:ai_textSplitter:13` |
| `n8n-nodes-base.gmail` | 14 | `operation, messageId, labelIds` | textClassifier, filter | filter, if | `src:main:2; tgt:main:16` |
| `n8n-nodes-base.rssFeedRead` | 13 | `options, url` | scheduleTrigger, executeWorkflowTrigger | set, filter | `src:main:12; tgt:main:13` |
| `n8n-nodes-base.limit` | 13 | `maxItems, keep` | filter, sort | merge, set | `src:main:13; tgt:main:13` |
| `@n8n/n8n-nodes-langchain.lmChatDeepSeek` | 13 | `options` | - | - | `src:ai_languageModel:13` |
| `@n8n/n8n-nodes-langchain.vectorStoreSupabase` | 13 | `options, tableName, tableName.__rl` | merge, set | aggregate, wait | `src:main:5; ai_tool:4; ai_vectorStore:2; tgt:ai_embedding:12; main:7; ai_document:6` |
| `n8n-nodes-base.webhook` | 12 | `options, path, httpMethod` | - | splitOut, googleSheets | `src:main:11` |
| `@n8n/n8n-nodes-langchain.vectorStorePGVector` | 12 | `mode, options, tableName` | set, googleDrive | merge, if | `src:main:6; ai_tool:4; tgt:ai_embedding:11; ai_document:8; main:8` |
| `n8n-nodes-base.editImage` | 11 | `operation, dataPropertyName, options` | editImage, executeWorkflowTrigger | editImage, executeWorkflow | `src:main:11; tgt:main:10` |
| `n8n-nodes-puppeteer.puppeteer` | 10 | `options, options.browserWSEndpoint, operation` | splitInBatches, manualTrigger | html, splitInBatches | `src:main:8; tgt:main:7` |
| `n8n-nodes-base.form` | 10 | `operation, completionTitle, options` | if, executeWorkflow | - | `tgt:main:9` |
| `n8n-nodes-base.formTrigger` | 10 | `formFields, formFields.values, formFields.values[]` | - | httpRequest, set | `src:main:10` |

## 6. Complete Node Index (All 97 Types)

| Node type | Count | Inferred role |
|---|---:|---|
| `n8n-nodes-base.set` | 279 | Map/add/overwrite fields in item JSON |
| `n8n-nodes-base.httpRequest` | 126 | Call REST/HTTP endpoints or fetch pages |
| `n8n-nodes-base.merge` | 103 | Join/merge multiple input branches |
| `n8n-nodes-base.manualTrigger` | 89 | Manual test trigger entrypoint |
| `n8n-nodes-base.postgres` | 75 | Query/write PostgreSQL data |
| `n8n-nodes-base.executeWorkflow` | 71 | Call a child workflow |
| `n8n-nodes-base.supabase` | 69 | Operate on Supabase tables |
| `n8n-nodes-base.if` | 66 | Binary conditional branch |
| `n8n-nodes-base.googleSheets` | 65 | Read/write Google Sheets |
| `n8n-nodes-base.html` | 61 | Extract fields from HTML using selectors |
| `n8n-nodes-base.executeWorkflowTrigger` | 58 | Entrypoint for called workflows |
| `n8n-nodes-base.filter` | 57 | Filter items by conditions |
| `n8n-nodes-base.splitOut` | 55 | Split array field into item stream |
| `n8n-nodes-base.summarize` | 51 | Summarize/aggregate text or fields |
| `n8n-nodes-base.stickyNote` | 50 | In-canvas documentation only |
| `n8n-nodes-base.telegram` | 48 | Send Telegram messages |
| `n8n-nodes-base.scheduleTrigger` | 47 | Cron/interval schedule trigger |
| `n8n-nodes-base.code` | 46 | Custom JS/Python transformation |
| `n8n-nodes-base.github` | 36 | GitHub API actions |
| `n8n-nodes-base.splitInBatches` | 34 | Loop items in batches |
| `@n8n/n8n-nodes-langchain.chatTrigger` | 28 | Chat trigger for AI agent workflows |
| `@n8n/n8n-nodes-langchain.lmChatGoogleGemini` | 26 | Gemini chat model node |
| `n8n-nodes-base.switch` | 23 | Multi-route conditional branch |
| `n8n-nodes-base.compareDatasets` | 22 | Compare old/new datasets |
| `@n8n/n8n-nodes-langchain.agent` | 22 | LangChain agent orchestrator |
| `n8n-nodes-base.noOp` | 21 | No-op terminator/placeholder |
| `n8n-nodes-base.ssh` | 21 | Execute remote shell commands |
| `@n8n/n8n-nodes-langchain.memoryBufferWindow` | 21 | Buffer memory for agent sessions |
| `@n8n/n8n-nodes-langchain.chainLlm` | 20 | Prompt-chain LLM call |
| `n8n-nodes-base.wait` | 20 | Delay/retry pacing |
| `@n8n/n8n-nodes-langchain.lmChatOpenAi` | 19 | OpenAI chat model node |
| `n8n-nodes-base.aggregate` | 18 | Aggregate items into one structure |
| `n8n-nodes-base.googleDrive` | 18 | Google Drive file operations |
| `n8n-nodes-base.extractFromFile` | 16 | Extract text from binary files |
| `@n8n/n8n-nodes-langchain.documentDefaultDataLoader` | 16 | Convert payload to Document objects |
| `n8n-nodes-base.markdown` | 15 | Markdown/HTML conversion |
| `@n8n/n8n-nodes-langchain.textSplitterRecursiveCharacterTextSplitter` | 14 | Recursive text chunking |
| `n8n-nodes-base.gmail` | 14 | Gmail read/update operations |
| `n8n-nodes-base.rssFeedRead` | 13 | Pull RSS feeds |
| `n8n-nodes-base.limit` | 13 | Cap item count |
| `@n8n/n8n-nodes-langchain.lmChatDeepSeek` | 13 | DeepSeek chat model node |
| `@n8n/n8n-nodes-langchain.vectorStoreSupabase` | 13 | Supabase vector store ingest/query |
| `n8n-nodes-base.webhook` | 12 | HTTP webhook trigger |
| `@n8n/n8n-nodes-langchain.vectorStorePGVector` | 12 | PGVector ingest/query node |
| `n8n-nodes-base.editImage` | 11 | Image editing pipeline |
| `n8n-nodes-puppeteer.puppeteer` | 10 | Browser automation/scraping |
| `n8n-nodes-base.form` | 10 | Serve/render form pages |
| `n8n-nodes-base.formTrigger` | 10 | Form submission trigger |
| `@n8n/n8n-nodes-langchain.embeddingsGoogleGemini` | 9 | Gemini embedding model |
| `n8n-nodes-base.googleCalendarTool` | 9 | Google Calendar tool for agents |
| `n8n-nodes-base.sort` | 8 | Sort incoming items |
| `@n8n/n8n-nodes-langchain.toolCalculator` | 7 | Calculator tool for agents |
| `@n8n/n8n-nodes-langchain.embeddingsOllama` | 7 | Ollama embedding model |
| `@n8n/n8n-nodes-langchain.embeddingsOpenAi` | 7 | OpenAI embedding model |
| `@n8n/n8n-nodes-langchain.agentTool` | 7 | Wrap external tool for agent |
| `n8n-nodes-base.convertToFile` | 6 | Convert JSON/text to binary file |
| `n8n-nodes-base.googleTasks` | 6 | Google Tasks API actions |
| `@n8n/n8n-nodes-langchain.outputParserStructured` | 6 | Parse LLM output to schema |
| `n8n-nodes-base.removeDuplicates` | 5 | Drop duplicate items |
| `@n8n/n8n-nodes-langchain.toolWorkflow` | 5 | Use workflow as callable tool |
| `n8n-nodes-base.respondToWebhook` | 5 | Return webhook HTTP response |
| `n8n-nodes-base.stopAndError` | 5 | Fail fast with custom error |
| `n8n-nodes-base.googleTasksTool` | 5 | Google Tasks tool for agents |
| `n8n-nodes-base.wordpress` | 5 | WordPress posts/media actions |
| `@n8n/n8n-nodes-langchain.textClassifier` | 4 | Classify text by categories |
| `@n8n/n8n-nodes-langchain.textSplitterCharacterTextSplitter` | 4 | Character-based text chunking |
| `n8n-nodes-base.telegramTrigger` | 4 | Telegram incoming update trigger |
| `n8n-nodes-base.gitlab` | 4 | GitLab API actions |
| `n8n-nodes-base.rssFeedReadTrigger` | 3 | RSS trigger on new entries |
| `@n8n/n8n-nodes-langchain.lmChatOpenRouter` | 3 | OpenRouter chat model node |
| `n8n-nodes-base.xml` | 3 | Parse/build XML |
| `n8n-nodes-docx-converter-html.docxToText` | 3 | DOCX to plain text conversion |
| `n8n-nodes-base.postgresTool` | 3 | Postgres tool for agents |
| `n8n-nodes-base.supabaseTool` | 2 | Supabase tool for agents |
| `n8n-nodes-mcp.mcpClientTool` | 2 | MCP client tool call |
| `n8n-nodes-base.googleBigQuery` | 2 | BigQuery query node |
| `n8n-nodes-base.ftp` | 2 | FTP/SFTP file operations |
| `@n8n/n8n-nodes-langchain.toolVectorStore` | 2 | Vector store retrieval tool |
| `@n8n/n8n-nodes-langchain.vectorStoreInMemory` | 2 | In-memory vector store |
| `n8n-nodes-base.emailReadImap` | 1 | Read IMAP inbox |
| `@n8n/n8n-nodes-langchain.toolWikipedia` | 1 | Wikipedia lookup tool |
| `n8n-nodes-base.dateTimeTool` | 1 | Date/time utility tool |
| `n8n-nodes-base.errorTrigger` | 1 | Workflow error trigger |
| `n8n-nodes-base.n8n` | 1 | n8n self-API node |
| `@n8n/n8n-nodes-langchain.openAi` | 1 | Legacy OpenAI completion/chat node |
| `@n8n/n8n-nodes-langchain.toolThink` | 1 | Reasoning helper tool |
| `@n8n/n8n-nodes-langchain.textSplitterTokenSplitter` | 1 | Token-based text chunking |
| `@n8n/n8n-nodes-langchain.informationExtractor` | 1 | Structured info extraction |
| `n8n-nodes-base.crypto` | 1 | Hash/encrypt/decrypt utilities |
| `n8n-nodes-base.googleDocs` | 1 | Google Docs API actions |
| `@n8n/n8n-nodes-langchain.chainSummarization` | 1 | Summarization chain node |
| `@n8n/n8n-nodes-langchain.mcpTrigger` | 1 | MCP trigger entrypoint |
| `@n8n/n8n-nodes-langchain.memoryPostgresChat` | 1 | Postgres-backed chat memory |
| `@n8n/n8n-nodes-langchain.lmChatOllama` | 1 | Ollama chat model node |
| `n8n-nodes-base.renameKeys` | 1 | Rename object keys |
| `@n8n/n8n-nodes-langchain.chat` | 1 | Send chat response message |
| `n8n-nodes-base.pushbullet` | 1 | Pushbullet notification node |

## 7. Skill Authoring Checklist (for auto-generation)

When Codex generates a workflow JSON, enforce this checklist:

1. Include required root keys: `name`, `nodes`, `connections`, `settings`.
2. Every node must have: `id`, `name`, `type`, `typeVersion`, `position`, `parameters`.
3. Use stable node names and make sure `connections` references node `name` exactly.
4. For AI workflows, wire `ai_*` channels explicitly (not only `main`).
5. Add error/retry behavior on external I/O nodes.
6. Prefer explicit transform nodes (`set`, `filter`, `splitOut`, `merge`) between fetch and write operations.
7. Validate with dry-run trigger (`manualTrigger`) before replacing with production trigger.

