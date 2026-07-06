# my-eli-mcp

<!-- mcp-name: io.github.matematicsolutions/my-eli-mcp -->

An MCP server for **Laws of Malaysia Online** (`lom.agc.gov.my`), the Attorney-General's
Chambers' official portal for Malaysian federal legislation. It fetches and cites principal
Acts, with a verifiable citation on every response.

Part of the MateMatic `eu-legal-mcp` production line, extended into Asia alongside `jp-eli-mcp`
and `sg-eli-mcp`. Same citation contract (a stable identifier + a human-readable citation + a
source URL), adapted for a jurisdiction with no ELI, no confirmed search API, and a source that
publishes only PDF.

> **Scope.** This MVP covers principal Acts only, addressed by their numeric act coordinate
> (e.g. `883`). No free-text search API was found on this portal during discovery; amendments
> and subsidiary legislation (P.U. (A)/(B) notices) are not yet covered. Every response carries
> a `dataset_note`.
>
> **Licence.** lom.agc.gov.my legislation is official public information published by the
> Attorney-General's Chambers of Malaysia. This connector relays it with attribution and a
> `source_url`.

## The tools

| Tool | What it does |
|---|---|
| `my_get_act` | Metadata for a principal Act by its numeric act coordinate. |
| `my_get_text` | The full text of an Act, extracted from the official PDF. |

Every response carries the contract: `eli_uri` (Malaysia has no ELI - this is the durable
lom.agc.gov.my act page URL, e.g. `https://lom.agc.gov.my/act-detail.php?language=BI&act=883`,
see `eli_note`), `human_readable_citation` (derived from the official PDF's own filename, since
the portal carries no separate title metadata), and `source_url`.

## Install

Not yet on PyPI - install from source until the first release ships:

```bash
git clone https://github.com/matematicsolutions/my-eli-mcp
cd my-eli-mcp
pip install -e .
```

Once released, this will be `uvx my-eli-mcp`.

Configuration via env:

- `MY_ELI_BASE_URL` - default `https://lom.agc.gov.my`
- `MY_ELI_CACHE_DIR` - default `~/.matematic/cache/my-eli`
- `MY_ELI_AUDIT_DIR` - default `~/.matematic/audit`

No API key. lom.agc.gov.my is keyless.

### Configure (Claude Code / any MCP client)

```json
{
  "mcpServers": {
    "my-eli-mcp": { "command": "my-eli-mcp" }
  }
}
```

## Governance

- **Public data only** - read-only against lom.agc.gov.my; no client data leaves the machine.
- **Audit log** - every tool call appends one JSON line to `~/.matematic/audit/my-eli-mcp.jsonl`.
- **Vendor-neutral** - talks only to `lom.agc.gov.my`; no LLM provider, no telemetry.
- **Verifiable citations** - every response is independently checkable via `source_url`.

See `CONSTITUTION.md` and `DISCOVERY.md`.

## Tests

```bash
pip install -e ".[dev]"
pytest tests/test_instructions_drift.py -v   # offline
pytest tests/test_smoke.py -v                # hits live lom.agc.gov.my
```

## Licence

Apache-2.0. © Matematic Solutions / Wieslaw Mazur.
