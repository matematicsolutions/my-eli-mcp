# Discovery: Laws of Malaysia Online (lom.agc.gov.my)

Date: 2026-07-06. **Status: CLOSED** for a fetch+cite MVP (confirmed by live probing).

## Context: this was found while widening the search beyond the original candidate list

Japan, Singapore, South Korea (blocked - needs registration), Thailand (blocked - WAF-protected
SPA) and India (deferred - real but heavy, see `_ref/DISCOVERY-IN-2026-07-06.md`) were the
original candidates. Hong Kong and Taiwan were also probed and **ruled out on `robots.txt`
grounds alone**: Hong Kong's `robots.txt` disallows `/` for the generic `User-agent: *` and
only allows named crawlers (Googlebot, Bingbot, Slurp, Baiduspider); Taiwan's disallows `/` for
every user-agent with no exceptions. Building against either would mean impersonating a named
search-engine crawler, which this fleet does not do - both were dropped without further probing.

## Base properties (CONFIRMED live 2026-07-06)

- **Base URL:** `https://lom.agc.gov.my`
- **Authentication:** none (public portal).
- **Format:** server-rendered HTML (PHP, `act-detail.php`), no JSON/XML API, no JSON-LD
  metadata block (unlike Malta). The full text is only in a PDF, embedded via a pdf.js viewer
  iframe whose `data-src` attribute carries the (relative, URL-encoded) PDF path.
- **`robots.txt`**: returned HTTP 500 on every probe in this session (a server-side error, not
  an explicit disallow). There is no crawl policy to violate; this connector still uses
  conservative retry/backoff and aggressive caching.
- **Identifier:** Malaysia has no ELI. The stable coordinate is the portal's own numeric `act`
  query parameter (e.g. `883` for the Records (Disposal) (Sarawak) Act 1955).

## Endpoint (CONFIRMED)

| Endpoint | Notes |
|---|---|
| `GET /act-detail.php?language=BI&act={n}` | one principal Act; HTML page with a pdf.js viewer pointing at the official PDF |

Verified live: `act-detail.php?language=BI&act=883` returned a 200 HTML page whose viewer
`data-src` resolved (after collapsing the relative `../../../` prefix against the site root -
confirmed this matches how a browser would resolve it) to
`https://lom.agc.gov.my/ilims/upload/portal/akta/outputaktap/3552389_BI/RECORDS (DISPOSAL)
(SARAWAK) ACT 1955 (Revised-2026).pdf`, a real 369 KB `application/pdf` response.

## What was NOT found

- **No REST/JSON API, no OAI-PMH.** Only server-rendered HTML pages.
- **No confirmed listing or search endpoint.** The homepage links to a handful of Acts
  directly and to `principal-act.php`, `search-legislation.php`, and per-type listing pages
  (`principal.php?type=original`, etc.), but none of these was confirmed in this session to
  return a parseable list of act coordinates - `principal-act.php` returned a page with no
  `act-detail.php` links in its HTML (likely a search form rendered client-side, or requiring
  form parameters not yet identified). Discovery in this MVP is therefore by coordinate only,
  the same pattern as `ie-eli-mcp` and `lu-eli-mcp` in this fleet.

## Citation contract (Article IV) - CLOSED for MY

- `eli_uri` = the lom.agc.gov.my act page URL, keyed on the portal's own numeric act
  coordinate (no native ELI; documented via `eli_note`).
- `human_readable_citation` = derived from the official PDF's own filename (the government's
  own naming, not invented), with a trailing "(Revised-YYYY)"/"(Reprint-YYYY)" suffix stripped.
- `source_url` = the same lom.agc.gov.my act page URL.

## Tool mapping - fetch+cite MVP

| Tool | Endpoint |
|---|---|
| `my_get_act` | `/act-detail.php?act={n}` (metadata: title from PDF filename, no PDF download) |
| `my_get_text` | `/act-detail.php?act={n}` + the linked PDF (downloaded and extracted with pypdf, the same pattern as `mt-eli-mcp`) |

**Deferred:** amendments (`A{n}`-style coordinates), subsidiary legislation (P.U. (A)/(B)
notices), a confirmed listing/search mechanism.

## Decision: BUILD

Keyless, no explicit crawl restriction, and a real (if PDF-only) official source with a
government-assigned, honestly-derivable title - the same fragility class as `mt-eli-mcp`
(server-rendered coordinate page + PDF extraction), already proven workable in this fleet.
