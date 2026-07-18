"""FastMCP entry point - Malaysia lom.agc.gov.my (Laws of Malaysia Online) tools.

Run:

    python -m my_eli_mcp.server

Configuration via env:

- ``MY_ELI_CACHE_DIR`` (default ``~/.matematic/cache/my-eli``)
- ``MY_ELI_AUDIT_DIR`` (default ``~/.matematic/audit``)
- ``MY_ELI_BASE_URL`` (default ``https://lom.agc.gov.my``)
"""

from __future__ import annotations

import os

import httpx
from fastmcp import FastMCP
from mcp.types import ToolAnnotations

from .audit import AuditLogger, hash_input, timer
from .citations import build_record, extract_pdf_text, resolve_pdf_url
from . import runtime
from .client import DEFAULT_BASE_URL, LomClient
from .models import Act, LawText

INSTRUCTIONS = """\
This MCP server exposes lom.agc.gov.my (Laws of Malaysia Online), the Attorney-General's Chambers' official portal for Malaysian federal legislation. Documents are addressed by a numeric act coordinate. Every response carries a stable `eli_uri`, a `human_readable_citation` and a `source_url` (the citation contract).

## Scope (MVP)

This MVP covers **principal Acts only** (e.g. `act-detail.php?act=883`), addressed by their numeric act coordinate. Amendments (`A1648`-style codes) and subsidiary legislation (P.U. (A)/(B) notices) are not yet covered - relay the `dataset_note`.

## Call order

1. `my_get_act` - metadata for a principal Act by its numeric `act_number` (e.g. `883`): title (derived from the official PDF's own filename - Malaysia's portal carries no separate metadata block), `eli_uri`, `source_url`.
2. `my_get_text` - the full text of an Act by `act_number`. Malaysian Acts are published only as PDF, so this downloads the official PDF and extracts the text.

## Hard constraints

- **Address by act number, not keywords** - there is no confirmed free-text search API on this portal; discovery is by coordinate.
- **No native ELI** - Malaysia has not deployed ELI. `eli_uri` is the lom.agc.gov.my act page URL, never invented; see `eli_note`.
- **Text comes from the PDF** - `my_get_text` extracts text from the official PDF; layout artefacts are possible. Relay the `text_note`.
- **Every response has `human_readable_citation` + `source_url`** - cite both to the user.
- **Audit log JSONL** - every tool call appends to `~/.matematic/audit/my-eli-mcp.jsonl`.

## Error iteration

Tools return a structured error with a `[code]` prefix:
- `invalid_arg` - `act_number` is missing, not a positive integer, or out of a plausible range.
- `not_found` - no Act page or PDF exists for that `act_number`.
- `upstream_error` - a lom.agc.gov.my error (HTTP, timeout, unreadable PDF). Retry once before surfacing.

## Response style

- Cite Acts as `human_readable_citation` with the act page URL: "RECORDS (DISPOSAL) (SARAWAK) ACT 1955, https://lom.agc.gov.my/act-detail.php?language=BI&act=883".
- NEVER invent an act number, a title or a URL - take each from the tool output.
"""


class ToolError(Exception):
    """Structured error for my-eli MCP tools - visible to the LLM with a [code] prefix."""

    VALID_CODES = frozenset({"invalid_arg", "not_found", "upstream_error"})

    def __init__(self, code: str, message: str):
        if code not in self.VALID_CODES:
            raise ValueError(f"Unknown ToolError code: {code}. Valid: {sorted(self.VALID_CODES)}")
        self.code = code
        super().__init__(f"[{code}] {message}")


READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    idempotentHint=True,
    destructiveHint=False,
    openWorldHint=True,
)

mcp: FastMCP = FastMCP(name="my-eli-mcp", instructions=INSTRUCTIONS)


def _base_url() -> str:
    return os.environ.get("MY_ELI_BASE_URL", runtime.base_url("eli", DEFAULT_BASE_URL)).rstrip("/")


def _audit() -> AuditLogger:
    return AuditLogger()


def _map_upstream(exc: Exception) -> Exception:
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 404:
        return ToolError("not_found", "No Act found on lom.agc.gov.my for that act_number.")
    if isinstance(exc, (httpx.HTTPStatusError, httpx.TransportError, httpx.TimeoutException)):
        return ToolError("upstream_error", f"lom.agc.gov.my error: {type(exc).__name__}: {exc}")
    return exc


def _validate(act_number: int) -> None:
    if act_number <= 0:
        raise ToolError("invalid_arg", f"act_number={act_number} must be a positive integer.")


# ---------------------------------------------------------------------------
# my_get_act
# ---------------------------------------------------------------------------


@mcp.tool(annotations=READ_ONLY)
async def my_get_act(act_number: int) -> Act:
    """Fetch metadata for a Malaysian principal Act by its numeric act coordinate.

    Args:
        act_number: e.g. ``883``.

    Returns:
        ``Act`` with ``eli_uri``, ``human_readable_citation``, ``source_url``.
    """
    audit = _audit()
    _validate(act_number)
    input_hash = hash_input({"act_number": act_number})

    with timer() as t:
        try:
            async with LomClient(base_url=_base_url()) as client:
                html = await client.get_act_page(act_number)
        except Exception as exc:
            audit.log(tool="my_get_act", input_hash=input_hash, output_count_or_size=0,
                      duration_ms=t.duration_ms if t.duration_ms else 0, status="error",
                      error=f"{type(exc).__name__}: {exc}")
            raise _map_upstream(exc) from exc

    rec = build_record(html, act_number)
    if not rec.get("pdf_path"):
        raise ToolError("not_found", f"No Act found for act_number={act_number} on lom.agc.gov.my.")
    act = Act.model_validate(rec)
    audit.log(tool="my_get_act", input_hash=input_hash, output_count_or_size=1,
              duration_ms=t.duration_ms, status="ok")
    return act


# ---------------------------------------------------------------------------
# my_get_text
# ---------------------------------------------------------------------------


@mcp.tool(annotations=READ_ONLY)
async def my_get_text(act_number: int) -> LawText:
    """Fetch the full text of a Malaysian principal Act (extracted from its official PDF).

    Args:
        act_number: e.g. ``883``.

    Returns:
        ``LawText`` with the citation contract and ``content`` (text extracted from the PDF).
    """
    audit = _audit()
    _validate(act_number)
    input_hash = hash_input({"act_number": act_number})

    with timer() as t:
        try:
            async with LomClient(base_url=_base_url()) as client:
                html = await client.get_act_page(act_number)
                rec = build_record(html, act_number)
                pdf_path = rec.get("pdf_path")
                if not pdf_path:
                    raise ToolError(
                        "not_found", f"No PDF found on the page for act_number={act_number}."
                    )
                pdf_bytes = await client.get_pdf(pdf_path)
        except ToolError:
            audit.log(tool="my_get_text", input_hash=input_hash, output_count_or_size=0,
                      duration_ms=t.duration_ms if t.duration_ms else 0, status="error",
                      error="not_found")
            raise
        except Exception as exc:
            audit.log(tool="my_get_text", input_hash=input_hash, output_count_or_size=0,
                      duration_ms=t.duration_ms if t.duration_ms else 0, status="error",
                      error=f"{type(exc).__name__}: {exc}")
            raise _map_upstream(exc) from exc

    try:
        text = extract_pdf_text(pdf_bytes)
    except Exception as exc:
        raise ToolError("upstream_error", f"Could not extract text from the PDF: {exc}") from exc
    if not text:
        raise ToolError("not_found", f"The PDF for act_number={act_number} yielded no extractable text.")

    result = LawText(
        act_number=act_number,
        title=rec.get("title"),
        eli_uri=rec.get("eli_uri"),
        human_readable_citation=rec.get("human_readable_citation"),
        source_url=rec.get("source_url"),
        pdf_url=resolve_pdf_url(pdf_path),
        content=text,
        byte_size=len(text.encode("utf-8")),
    )
    audit.log(tool="my_get_text", input_hash=input_hash, output_count_or_size=result.byte_size or 0,
              duration_ms=t.duration_ms, status="ok")
    return result


def main() -> None:
    """Run the MCP server over stdio (default for Claude Code)."""
    mcp.run()


if __name__ == "__main__":
    main()
