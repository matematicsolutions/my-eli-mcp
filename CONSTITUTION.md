# Constitution of my-eli-mcp

Version: 0.1.0
Date: 2026-07-06
Licence: Apache-2.0

`my-eli-mcp` is an MCP server for Laws of Malaysia Online (`lom.agc.gov.my`). It fetches and
cites Malaysian principal Acts, addressed by their numeric act coordinate. Amendments,
subsidiary legislation, and case law are out of scope for this MVP.

The 4 principles below are inherited from the `eu-legal-mcp` line Constitution (Article IV),
adapted for a jurisdiction without ELI and without a confirmed search API.

---

## Art. 1. Public data only

lom.agc.gov.my is the official, public source of Malaysian federal legislation, published by
the Attorney-General's Chambers. The server is read-only against lom.agc.gov.my and sends
nothing beyond the requested act coordinate.

## Art. 2. Mandatory audit log

Every tool call MUST append one JSON line to `~/.matematic/audit/my-eli-mcp.jsonl`
(ts / tool / input_hash SHA-256 / output_count_or_size / duration_ms / status). Inability to
write = the tool returns an error, it does not silently skip.

## Art. 3. Vendor neutrality

No tool hardcodes an LLM provider, assumes a model, or adds commercial telemetry. The server
talks only to `lom.agc.gov.my` and the local filesystem. Authentication: none; own backoff +
cache.

## Art. 4. A durable identifier and a human-readable citation are mandatory

Every response MUST carry three fields:
- `eli_uri`: Malaysia has no ELI. This is the durable lom.agc.gov.my act page URL
  (`https://lom.agc.gov.my/act-detail.php?language=BI&act={act_number}`), keyed on the
  portal's own numeric act coordinate - never invented. `eli_note` on every response says so
  explicitly.
- `human_readable_citation`: derived from the official PDF's own filename (the portal has no
  separate metadata block), e.g. "RECORDS (DISPOSAL) (SARAWAK) ACT 1955".
- `source_url`: the same lom.agc.gov.my act page URL (the fetchable original).

---

## Open points

1. **No confirmed search API** - `robots.txt` returned a server error (HTTP 500) on every
   probe in this session, and no listing or search endpoint was confirmed live; discovery is
   currently by coordinate only. A future revision could revisit this once `robots.txt` is
   reachable and a listing mechanism is confirmed.
2. **Amendments and subsidiary legislation** - the portal exposes separate coordinate schemes
   for amendments (e.g. `A1648`) and P.U. (A)/(B) notices; neither is covered by this MVP.
3. **Title provenance** - the human-readable title comes from the official PDF's filename,
   which is a real, government-assigned name but not a structured metadata field (unlike
   Malta's JSON-LD). Titles with unusual punctuation may need cleanup in a future revision.

## Ewolucja konstytucji

Changes to art. 1-4 follow SEMVER + an entry in `CHANGELOG.md` + a `pyproject.toml` bump.

First version: 2026-07-06. Author: Wieslaw Mazur / MateMatic.
