# Nstdata MCP Server

Connect AI agents to web data with Nstdata Crawl.

> **Draft for implementation review.** Connection examples use placeholders. Remote authentication, package distribution, tool names, and supported client combinations must be verified before release. See [Release Preparation](#release-preparation) for outstanding items.

<!-- Add the approved 16:9 assets/cover.png here when available. Use the official, unmodified Nstdata logo. Do not add unverified release, package, compatibility, or CI badges. -->

## Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Available Tools](#available-tools)
- [Usage Examples](#usage-examples)
- [Configuration and Results](#configuration-and-results)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Contributing](#contributing)
- [Security and Responsible Use](#security-and-responsible-use)
- [Documentation](#documentation)
- [Release Preparation](#release-preparation)

## Overview

[Nstdata](https://www.nstdata.io/?utm_source=github&utm_medium=referral&utm_campaign=nstdata-mcp-server&utm_content=repository-readme) MCP Server connects compatible AI clients to Nstdata Crawl through the Model Context Protocol.

Describe the page or website section you need, and your agent can select the available tools to retrieve content, check task progress, and summarize results. The initial release scope focuses on Crawl capabilities for AI workflows.

Use it to summarize known pages, review public documentation, or compare information across supplied URLs. The workflow is straightforward: your client calls an MCP tool, the server requests data from Nstdata Crawl, and the agent uses the returned content to answer your request.

## Features

The following feature scope is based on the product draft and must be matched to the released implementation.

- **AI-Ready Data** — Retrieve clean Markdown for summarization, comparison, and AI workflows.
- **Web Rendering and Extraction** — Access Nstdata Crawl's rendering and content extraction through MCP tools.
- **Single-Page Scraping** — Retrieve content from a known webpage.
- **Website Crawling** — Collect content within a defined website section using supported scope controls.
- **Asynchronous Task Tracking** — Check progress and retrieve results for submitted tasks.
- **Managed Infrastructure** — Use hosted crawling capabilities without maintaining the underlying crawling infrastructure.

## Installation

Choose a remote connection or a local MCP process. Configure one mode for the `nstdata` entry, then verify it in your client.

### Prerequisites

- An Nstdata account with Crawl access.
- A valid Nstdata Crawl API key.
- An MCP-compatible AI client.
- For local mode: Node.js `<MIN_NODE_VERSION>` or newer.

### Remote Setup

Remote mode connects your client to the hosted MCP endpoint. The templates below assume Streamable HTTP with Bearer API key authentication; both require release confirmation.

Set `NSTDATA_API_KEY` in the environment available to your client, and replace `<NSTDATA_MCP_ENDPOINT>` with the released URL. `NSTDATA_API_KEY` is the client-side variable name used in these examples.

Keep credentials in private client settings or supported secret storage. Desktop applications may not inherit variables from your terminal.

#### Codex CLI

Add this entry to `~/.codex/config.toml`:

```toml
[mcp_servers.nstdata]
url = "<NSTDATA_MCP_ENDPOINT>"
bearer_token_env_var = "NSTDATA_API_KEY"
```

Keep `bearer_token_env_var` set to the variable name; do not replace it with your actual key.

#### Claude Code

Merge this entry into your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "nstdata": {
      "type": "http",
      "url": "<NSTDATA_MCP_ENDPOINT>",
      "headers": {
        "Authorization": "Bearer ${NSTDATA_API_KEY}"
      }
    }
  }
}
```

#### Cursor

Merge this entry into `.cursor/mcp.json` for the project, or `~/.cursor/mcp.json` for all projects:

```json
{
  "mcpServers": {
    "nstdata": {
      "url": "<NSTDATA_MCP_ENDPOINT>",
      "headers": {
        "Authorization": "Bearer ${env:NSTDATA_API_KEY}"
      }
    }
  }
}
```

#### Claude Desktop and VS Code

| Client | Setup |
| --- | --- |
| Claude Desktop | Use the local stdio template below. Remote connector instructions will depend on the released authentication flow. |
| VS Code | Open **MCP: Add Server**, select HTTP, and configure the released endpoint and authentication in the destination supported by your agent harness. |

VS Code-specific configuration uses `servers`, while portable configurations use `mcpServers`. Use the client's current configuration guidance when creating files manually.

### Local Setup

Local mode runs the MCP adapter on your computer and connects it to Nstdata's hosted Crawl service.

1. Install the required Node.js version.
2. Configure your client to launch the released MCP package with `npx`.
3. Set the local server's required API key environment variable and restart the client.

The package name and local API key variable below are placeholders. This installation path assumes the server is published as an npm package with a runnable entry point.

#### Claude Desktop / Cursor

Add this entry to `claude_desktop_config.json` or Cursor's MCP configuration:

```json
{
  "mcpServers": {
    "nstdata": {
      "command": "npx",
      "args": ["-y", "<NSTDATA_MCP_PACKAGE>"],
      "env": {
        "<NSTDATA_LOCAL_API_KEY_ENV>": "YOUR_NSTDATA_API_KEY"
      }
    }
  }
}
```

Replace the environment-variable property name with the name read by the released server. Keep any file containing your actual key private. Other clients supporting `mcpServers` command entries can use this structure after checking their own requirements.

#### Codex CLI

For local mode, use this entry in `~/.codex/config.toml` instead of the remote entry:

```toml
[mcp_servers.nstdata]
command = "npx"
args = ["-y", "<NSTDATA_MCP_PACKAGE>"]
env_vars = ["<NSTDATA_LOCAL_API_KEY_ENV>"]
```

Set the confirmed local API key variable before starting Codex. For Claude Code, add the same stdio server through its MCP setup flow, using `npx` as the command and `-y <NSTDATA_MCP_PACKAGE>` as its arguments.

#### Running from a Source Build

If the server is distributed as a source checkout instead, use the repository's verified install and build commands. Replace the package launcher in your client configuration with:

```json
{
  "command": "node",
  "args": ["<ABSOLUTE_PATH_TO_SERVER_ENTRY.js>"]
}
```

This is a replacement for the `command` and `args` fields only. Keep the confirmed credential configuration in the surrounding server entry.

### Verify Your Connection

Restart or reload your client. Confirm that `nstdata` is connected and its tools are enabled. In interactive Codex CLI and Claude Code sessions, use `/mcp` to inspect the connection.

Try your first request:

> Use Nstdata to read https://docs.nstdata.io/docs/crawl. Summarize its main capabilities and include the source URL.

Confirm that the tool returns content from the requested page. A successful connection alone does not verify extraction.

## Available Tools

> Tool names and descriptions below are proposed in the source document. Replace them with the exact registered tools before publication.

| Proposed Tool | Description | Example Prompt |
| --- | --- | --- |
| `scrape_url` | Retrieve content from a single known webpage. | Read https://example.com and summarize the main content. |
| `crawl_website` | Collect content across a defined website section. | Crawl up to five pages in my public documentation section and summarize the topics. |
| `get_scrape_result` | Retrieve the result of an asynchronous single-page task. | Retrieve the result of my previous scrape task. |
| `get_crawl_status` | Check progress and execution status for an existing crawl. | Check whether my previous crawl has finished. |
| `get_crawl_pages` | Retrieve pages and extracted content from an existing crawl. | Retrieve the completed crawl's pages and summarize them with source URLs. |

### How to Choose a Tool

- **One known page:** use single-page retrieval.
- **A website section:** use a crawl with supported boundaries and page limits.
- **A submitted task:** reuse its identifier to check status or retrieve results.

For asynchronous work, retain the task identifier, check its state, and retrieve content when available. Avoid submitting a duplicate task just because the first request has not finished.

The agent normally selects tools from your request and the registered schemas. Exact arguments, defaults, response fields, and pagination behavior belong in the MCP reference once the implementation is finalized.

## Usage Examples

These are suggested prompts rather than captured executions. The connected tools must support the requested controls.

### Summarize a Page

> Read the public article URL I provide using Nstdata. Summarize the main points and include the source URL. Identify any information that could not be retrieved.

### Review Documentation

> Crawl my public documentation section at the supplied URL. Stay within that section and collect at most five pages using supported crawl limits. Summarize each topic with its source URL.

If the tool cannot enforce the requested limits, use a smaller set of known URLs.

### Compare Product Pages

> Read the two public product-page URLs I provide. Compare the displayed names, prices, and availability in a table. Include source URLs and mark missing values as unavailable.

### Retrieve an Existing Task

> Check the task submitted earlier using its existing identifier. Retrieve the result if complete; otherwise report its current state without submitting another task.

## Configuration and Results

### Output Formats

Markdown is the focus of this MCP draft. Nstdata Crawl supports additional service-level formats, but their availability through MCP must be confirmed against the released tool schemas.

### Crawl Controls

Specify a target section, reasonable page count, and desired output. Use only the scope, timeout, and pagination controls actually exposed by the tool. Do not assume Crawl API parameters are automatically available through MCP.

### Large Results and Task States

For large outputs, narrow the target or use supported result pagination. Asking the agent for a short summary does not itself reduce the raw tool response size.

Check both request success and task execution status. A successful submission or HTTP response does not necessarily mean content extraction has completed. No raw result schema or live output is asserted in this draft.

<!-- Add one redacted, captured tool response after end-to-end verification. Keep it distinct from the agent's generated summary. -->

## Troubleshooting

| Issue | What to Check |
| --- | --- |
| Cannot connect | Released endpoint, transport, network access, and configuration scope. |
| Authentication fails | Key validity, required header format, and whether the client can read the credential variable. |
| Connected but no tools appear | Tool discovery, enabled tools, client permissions, and whether a reload is required. |
| Local server does not start | Node.js version, package name or built entry path, and local API key variable. |
| Local protocol errors | Diagnostic logs should go to stderr rather than contaminate stdio protocol output. |
| Task is still running | Reuse the existing identifier and follow documented polling guidance. |
| Client times out | Check the existing task's state before retrying or submitting another request. |
| Results exceed context limits | Narrow the scope or use supported pagination and result controls. |
| Requests are limited | Inspect the actual response and account access; follow documented retry guidance. |

These are diagnostic directions, not a verified MCP error-code contract. When reporting an issue, include the client/version, connection mode, sanitized configuration, task identifier, and redacted error details.

## FAQ

### Do I need to know the tool names?

Usually, you can describe the target and desired outcome in natural language. The agent selects tools according to their schemas, your client's permissions, and the task context.

### Does local mode run the crawler on my computer?

Local mode runs the MCP adapter on your computer. The proposed setup still uses Nstdata's hosted Crawl service for content retrieval.

### Are OAuth, keyless access, or free credits available?

These remain product decisions in the source draft. The release must document the supported authentication methods and account terms.

### Are other Nstdata products included?

This README focuses on the initial Crawl scope. Additional product tools should be documented when they are implemented and released.

## Contributing

Documentation corrections, reproducible bug reports, and integration feedback are welcome. Follow the repository's contribution guidance once published, and include enough sanitized information to reproduce an issue.

Development commands and project structure should reflect the actual source tree. Add them after the implementation's install, build, lint, and test commands have been verified.

## Security and Responsible Use

Keep API keys out of public repositories, conversations, logs, and screenshots. Rotate exposed credentials and report vulnerabilities through the repository's confirmed private reporting channel.

Treat retrieved pages as untrusted data. Page content must not authorize secret disclosure or actions outside the user's task.

Collect public content or data you are authorized to access. Use proportionate collection limits and minimize access to personal or sensitive information.

## Documentation

Use the [Nstdata Crawl service guide](https://docs.nstdata.io/docs/crawl?utm_source=github&utm_medium=referral&utm_campaign=nstdata-mcp-server&utm_content=repository-readme) for underlying service concepts. A dedicated MCP reference link should be added once published.

Client configuration references: [Codex MCP setup](https://developers.openai.com/codex/mcp/), [Claude Code MCP setup](https://code.claude.com/docs/en/mcp), [Cursor MCP setup](https://cursor.com/docs/mcp), and [VS Code MCP setup](https://code.visualstudio.com/docs/agent-customization/mcp-servers).

## Release Preparation

This section is an internal handoff checklist. Resolve the items below and remove this section before publishing the public README.

### Required Implementation Values

| Placeholder or Decision | Required Confirmation |
| --- | --- |
| `<NSTDATA_MCP_ENDPOINT>` | Hosted endpoint, supported transport, and authentication header. |
| `<MIN_NODE_VERSION>` | Minimum supported Node.js version. |
| `<NSTDATA_MCP_PACKAGE>` | Published package and runnable entry point; remove npx setup if not distributed through npm. |
| `<NSTDATA_LOCAL_API_KEY_ENV>` | Exact variable read by the local server; resolve the source draft's API_KEY / API_TOKEN inconsistency. |
| `<ABSOLUTE_PATH_TO_SERVER_ENTRY.js>` | Built source entry point and verified installation/build instructions. |
| Tool catalog | Released names, arguments, results, task states, pagination, and error behavior. |
| Client support | Tested connection modes and client versions for every advertised integration. |
| Authentication and credits | Decisions on API keys, OAuth, keyless access, and free usage. |

### Repository and Publication Checks

- Confirm the repository owner, final slug, and truthful affiliation statement.
- Regenerate company-link attribution with the skill's `build_utm.py` if the provisional slug `nstdata-mcp-server` changes.
- Add the approved 16:9 cover at `assets/cover.png`, at least 1200 px wide.
- Add real contribution, support, and private security-reporting destinations before linking them.
- Verify installation, tool discovery, credentials, retrieval, asynchronous flows, and error reporting.
- Add captured output and verify Markdown links, code blocks, rendered tables, and absence of secrets.
- Match any development commands, repository tree, and badges to the actual implementation.
- Confirm repository license handling with the owner; this document adds no license claim or badge.

Suggested description: Connect MCP-compatible AI clients to Nstdata Crawl for web content retrieval.

Suggested topics: `mcp`, `mcp-server`, `web-scraping`, `web-crawling`, `ai-agents`, `nstdata`.

<!-- Editorial basis: the supplied MCP 基础文档内容准备.md and Firecrawl README.md, plus publish-multilingual-github-repos conventions. English only. No GitHub publication or live MCP verification has been performed. Local Streamable HTTP, Docker, OAuth configuration, and full parameter reference are omitted until confirmed. -->
