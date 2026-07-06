"""Pydantic v2 models for lom.agc.gov.my (Laws of Malaysia Online) + my-eli-mcp."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

DATASET_NOTE = (
    "lom.agc.gov.my (Laws of Malaysia Online) is the Attorney-General's Chambers' official "
    "portal for Malaysian federal legislation. This MVP covers principal Acts only, addressed "
    "by their numeric act coordinate (e.g. 883); amendments and subsidiary legislation "
    "(P.U. (A)/(B) notices) are not yet covered. Malaysia has no ELI scheme; eli_uri carries "
    "the durable lom.agc.gov.my act page URL (see eli_note)."
)

ELI_NOTE = (
    "Malaysia has not deployed ELI. eli_uri is the durable lom.agc.gov.my act page URL "
    "(https://lom.agc.gov.my/act-detail.php?language=BI&act={act_number}), keyed on the "
    "portal's own numeric act coordinate - never invented."
)


class _Tolerant(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Act(_Tolerant):
    """Result of ``my_get_act`` - metadata only, no body text."""

    act_number: int
    title: str | None = None
    pdf_path: str | None = None

    # Citation contract (Art. IV CONSTITUTION).
    eli_uri: str | None = None
    eli_note: str = ELI_NOTE
    human_readable_citation: str | None = None
    source_url: str | None = None
    dataset_note: str = DATASET_NOTE


class LawText(_Tolerant):
    """Result of ``my_get_text`` - the full text of an Act (extracted from its official PDF)."""

    act_number: int
    title: str | None = None
    eli_uri: str | None = None
    eli_note: str = ELI_NOTE
    human_readable_citation: str | None = None
    source_url: str | None = None
    pdf_url: str | None = None
    content: str | None = None
    byte_size: int | None = None
    text_note: str = (
        "Extracted from the official PDF with pypdf; minor layout artefacts (page numbers, "
        "column breaks) are possible."
    )
    dataset_note: str = DATASET_NOTE
