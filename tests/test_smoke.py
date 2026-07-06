"""Smoke tests - require internet, hit the live lom.agc.gov.my site.

Run manually:

    pytest tests/test_smoke.py -v
"""

from __future__ import annotations

import pytest

from my_eli_mcp.server import my_get_act, my_get_text

# Records (Disposal) (Sarawak) Act 1955.
ACT_NUMBER = 883


@pytest.mark.asyncio
async def test_smoke_get_act() -> None:
    act = await my_get_act(ACT_NUMBER)
    assert act.eli_uri == f"https://lom.agc.gov.my/act-detail.php?language=BI&act={ACT_NUMBER}"
    assert act.title is not None and "RECORDS" in act.title.upper()
    assert act.source_url is not None and act.source_url.startswith("https://")


@pytest.mark.asyncio
async def test_smoke_get_text() -> None:
    text = await my_get_text(ACT_NUMBER)
    assert text.content is not None and len(text.content) > 0
    assert text.eli_uri is not None
    assert text.byte_size and text.byte_size > 0
    assert text.pdf_url is not None and text.pdf_url.endswith(".pdf")
