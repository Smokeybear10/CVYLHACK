# Report Visual Style + PDF Generation Spec (for "Sonder")

**Goal:** Programmatically generate a PDF, from structured JSON, for a screened curbside EV‑charging site that looks indistinguishable from a real professional engineering / site‑assessment / consulting report.

**TL;DR recommendation:** Generate **HTML + CSS from a Jinja2 template and render with WeasyPrint** (pure‑Python, no headless browser). It fully supports CSS Paged Media — `@page`, margin boxes for running headers/footers, `counter(page)`/`counter(pages)`, page breaks, `@font-face` font embedding with glyph subsetting, and PDF bookmarks/outlines. This is the single highest‑leverage path to "looks like a real consulting report" with the least code. Use Playwright/headless Chrome only if you must render JS charts (Chart.js/Plotly/Mermaid); otherwise pre‑render charts to SVG/PNG and stay on WeasyPrint.

---

## (a) Typography Spec

### What real firms actually use

Two clear camps, both valid; pick **one** and execute it cleanly (2–3 fonts max is the universal rule across every style guide reviewed).

| Firm / domain | Body font | Heading font | Notes |
|---|---|---|---|
| **AECOM** | "AECOM Sans"; **Arial** fallback (their official MS Word template font) | AECOM Sans Bold/XBold | Sans-serif throughout. Source: AECOM Brand Identity Guidelines. |
| **WSP** | **Helvetica Neue** (signature typeface, "clean, highly readable") | Helvetica Neue | All-sans identity. |
| **Arup** | Times New Roman retained in rebrand; Trajan (serif) in logo | — | Serif heritage. |
| **McKinsey / BCG / Bain** | **Arial / Helvetica / Calibri** (sans); body ~16–18 pt on slides, chart labels 12–14 pt | Same family, bold weight, 24–28 pt headlines | No italics, no underlines; bold for emphasis only; 2–3 colors + grays; solid white backgrounds. |
| **Phase I ESA report (real sample, GAEA/CSA Z768)** | **Calibri** (regular/bold/italic) body | **Arial** bold headings | Letter-size (612×792 pt = 8.5"×11"). Tahoma/Courier New for special elements. |
| **Gov't engineering reports (PEO Ontario, university standards)** | **Times New Roman 11 pt** common; serif for print readability | Larger bold sans or serif | 1" margins, letter or A4. |

**Convention takeaways:**
- **Sans-serif is the modern default** for engineering/consulting deliverables (Arial, Helvetica/Helvetica Neue, Calibri). Serif (Times New Roman, Georgia, Garamond) reads as more "traditional/government/legal" and is also fully acceptable for body in print.
- Common, safe, *credible* combo: **sans-serif headings + serif OR sans body.** A clean all-sans (Helvetica/Arial body + Helvetica/Arial bold headings) reads as McKinsey/WSP/AECOM. A serif body (Georgia/Times) + sans headings reads as a classic technical/government report.
- Stick to **2–3 fonts max**; use weight (regular/bold) and size for hierarchy, not new typefaces. Avoid italics/underline for emphasis (consulting convention).

### Sizes, spacing, hierarchy (print — points)

Synthesized from technical-writing and typography guides (SmartTechSavvy, adoc-studio, MV3, Ithy):

| Element | Size (pt) | Line-height | Weight | Notes |
|---|---|---|---|---|
| **Body** | **10–11 pt** (11 pt is the sweet spot for letter-size) | **1.4–1.5×** (≈15–16 pt leading) | Regular | Line length 50–75 chars (~65ch ideal). |
| **H1 / report title** | 24–28 pt | 1.1–1.2 | Bold | On cover can go larger (32–44 pt). |
| **H2 / section** | 16–18 pt | 1.2 | Bold | ~1.5–2× body. |
| **H3 / subsection** | 13–14 pt | 1.3 | Bold/Semibold | ~1.25–1.5× body. |
| **H4 / minor** | 11–12 pt | 1.3 | Bold or bold-italic | |
| **Captions (figure/table)** | 8–9 pt | 1.2 | Regular/Italic | Often gray. |
| **Header/footer running text** | 8–9 pt | — | Regular | |
| **Table body** | 9–10 pt | 1.2 | Regular | |
| **Code/monospace** | 9–10 pt | 1.2 | Regular | Consolas/Monaco/Courier. |

- **Leading rule:** body line-height 1.4–1.65× font size; headings 1.0–1.3×.
- **Heading scale:** roughly H1≈2.4×, H2≈1.6×, H3≈1.25× body (a modular scale of ~1.25–1.33).
- **Paragraph spacing:** 0.5–1× the line height between paragraphs (≈6–8 pt). Prefer space-after over first-line indent in modern reports.

---

## (b) Layout + Color Spec

### Page geometry
- **Page size:** US **Letter 8.5"×11"** (the real ESA sample = 612×792 pt). Offer **A4** as a config flag for non-US.
- **Margins:** **1 inch (25.4 mm) all sides** is the dominant standard (gov't engineering, ESA). Bump the **binding/left margin to 1.25–1.5"** if printed/bound. Keep header/footer content inside a band ~0.5" from the edge.
- **Columns:** **Single column** for engineering/site-assessment narrative reports (this is the norm). Two-column is for academic/journal papers, not consulting deliverables — avoid it.

### Cover page
Professional covers contain, top-to-bottom: client/firm logo; **report title** (large, bold); **subtitle / site address**; **report type** ("Curbside EV Charging Site Assessment"); **project / report ID**; **prepared for** (client) + **prepared by** (firm); **date**; optional site photo or location map filling lower half; a thin **brand accent rule** or color band. A full-bleed accent header band or a single bold accent line is the cheapest way to look "designed."

### Running header / footer (repeat on every body page via `@page` margin boxes)
- **Header (top):** short project/report name on the left; section title or firm name on the right; thin bottom rule. (Real ESA reports repeat project name + report number in the header.)
- **Footer (bottom):** confidentiality line (e.g., "Confidential — Prepared for [Client]") left; **report ID / project number** center or left; **"Page X of Y"** right (`counter(page) " of " counter(pages)`); date.
- **Page numbering:** front matter in lower-case roman (i, ii, iii); main body Arabic starting at 1; title page unnumbered. (Standard formal-report convention.)

### Section + figure/table numbering
- **Section numbering:** Arabic, decimal-nested — `1`, `1.1`, `1.1.1`. Do **not** use alpha-numeric (A.1) mixing. Left-justified headings. Avoid "stacked headings" (two headings with no text between).
- **Tables:** caption/number **above** the table ("Table 2.4: …"). **Figures/photos/maps:** caption **below** ("Figure 3.1: …"). Number sequentially or per-section (Table 2.4 = 4th table of section 2). Always reference by number in text ("see Figure 9"), never "the figure below." Include source attribution in caption when not original.
- **Photos/maps:** placed inline near first reference or grouped in an appendix "Site Photographs" / "Figures" section; each gets a numbered caption, often with date/direction ("Photo 4 — North curb, facing east, 2026-06-13").

### Color palette
Consulting/engineering reports are **restrained**: white background, near-black text, one dark "brand" color (almost always a navy/blue), grays for structure, **one** accent for highlights/links/key data. McKinsey/BCG/Bain use 2–3 colors + grays on solid white.

**Recommended professional palette (hex):**

| Role | Hex | Use |
|---|---|---|
| Ink / body text | `#1A1A1A` (or `#212529`) | Body, near-black not pure black. |
| Primary brand (navy) | `#14213D` (Oxford Blue) or `#0B2545` | H1/H2, header band, table header fill, rules. |
| Secondary blue | `#1D3557` / `#2C5282` | Subheads, links. |
| Accent (pick ONE) | Orange `#E76F00` / `#FCA311`, or teal `#2A9D8F` | Key callouts, the score chip, recommendation highlight. |
| Rule / border gray | `#D0D5DD` | Table borders, hairlines. |
| Zebra / fill gray | `#F2F4F7` (very light) | Alternate table rows, callout boxes. |
| Muted text / captions | `#667085` | Captions, footnotes, header/footer. |
| Page background | `#FFFFFF` | Always white. |

Corporate-blue reference values if matching a "tech" feel: IBM `#0043CE`, Navy `#000080`, Royal `#4169E1`, PayPal navy `#00457C`, LinkedIn `#0A66C2`.

### Tables
- **Header row:** filled with the dark brand navy, **white bold text**, slightly larger padding. (Header row should be visibly darker than data rows.)
- **Zebra striping:** optional; if used, **low-saturation light gray** (`#F2F4F7`) on alternate rows — and then you can **drop most row borders** (the fill does the row-tracking job). If not striped, use light horizontal hairline borders. Avoid heavy full grids and high-contrast stripes.
- **Borders:** prefer horizontal rules only (top/bottom of header, bottom of last row) for a clean "financial table" look; keep vertical lines minimal or absent.
- Repeat the header row across page breaks (`thead { display: table-header-group; }`).

### Callout / box styles
- **Info/finding box:** light gray fill `#F2F4F7`, 3–4 pt left border in brand navy or accent, padding ~10 pt, slightly smaller bold label.
- **Key recommendation / warning:** tinted background in the relevant RAG color at ~8–12% opacity with a solid left bar in the full color.

---

## (c) Scorecard / Rating Visual Conventions

Use the universally-understood **RAG (Red–Amber–Green) traffic-light system** for the per-site go/no-go verdict and sub-criteria.

- **Green = Go / on-track / suitable.** **Amber/Yellow = caution / marginal / needs review.** **Red = No-go / critical issue / do not proceed.** (Some add **Blue = complete/done**, "BRAG".)
- **Accessibility (do this):** never rely on color alone. Pair every chip with a **letter or word** ("G / GO", "A / CAUTION", "R / NO-GO") and/or an icon (check / warning-triangle / cross). This is the documented RAG accessibility convention for color-blind readers.
- **Concrete chip colors (hex):**

| Status | Fill | Text/border | Label |
|---|---|---|---|
| GO | `#2E7D32` (or softer `#38A169`) | white | "GO" / ✓ |
| CAUTION | `#F2A900` / `#D69E2E` (amber) | dark `#1A1A1A` | "CAUTION" / ! |
| NO-GO | `#C62828` (or `#E53E3E`) | white | "NO-GO" / ✕ |
| N/A / info | `#667085` gray | white | "N/A" |

- **Patterns:** a big rounded **verdict badge/pill** in the executive summary and on the cover; a **scorecard table** of criteria (e.g., curb geometry, power availability, ADA clearance, traffic, permitting) each with a RAG chip + short note; optional **overall numeric score** (e.g., 0–100 or A–F) shown as a colored gauge/donut. Keep it one accent + the three RAG colors only.

---

## (d) PDF Generation: Tool Recommendation + Rationale

### The candidates

| Tool | Model | Strengths | Weaknesses |
|---|---|---|---|
| **WeasyPrint** | Pure-Python HTML/CSS → PDF (Pango text shaping + Cairo). | Best-in-class **CSS Paged Media** (@page, margin boxes, running headers/footers, counters, breaks); **@font-face fully supported with glyph subsetting**; smallest output files; PDF bookmarks from headings; no browser. ~30–50 MB deps (Pango/Cairo). | **No JavaScript** (charts must be pre-rendered SVG/PNG); partial CSS Grid; cold render ~227 ms simple / ~629 ms complex (fine for a hackathon, <4 PDFs/s). |
| **Playwright (headless Chrome)** | Renders real Chromium, `page.pdf()`. | Full modern CSS (Grid/Flex/container queries), **executes JS** (Chart.js/Plotly/Mermaid), very fast warm (~3–13 ms). | ~300 MB Chromium + ~150 MB RAM/instance; harder to deploy serverless; larger PDFs (embeds extra resources); print fidelity of `@page` is decent but less precise than WeasyPrint for paged-media niceties. |
| **ReportLab (Platypus)** | Programmatic, draw/flowables in Python. | Total low-level control; battle-tested; great table splitting (`repeatRows`), Pandas→Table. | **Not HTML/CSS** — you hand-build layout in code; far slower to iterate on "looks like a designed report"; styling is verbose. Best when you need pixel-exact custom drawing or no system deps. |
| **LaTeX** | Typesetting. | Gorgeous typography. | Heavy toolchain, awkward from JSON, slow to template a *branded consulting* look, hard to match arbitrary brand styling. Overkill here. |

### Recommendation for Sonder (Python backend, JSON → templated report)

**Use WeasyPrint + Jinja2.** Rationale:
1. The deliverable is a **fixed, branded, paginated document** — exactly WeasyPrint's wheelhouse. Running headers/footers, "Page X of Y", cover page, section numbering, repeating table headers, and embedded brand fonts are all native CSS Paged Media features it implements well.
2. **Iteration speed:** you design the look in HTML/CSS (preview in a browser), then render the identical thing to PDF. This is dramatically faster than hand-coding ReportLab flowables to chase a "professional" aesthetic.
3. **Font fidelity:** `@font-face` is fully supported, so you can ship exact brand fonts (e.g., a Helvetica/Arial-class sans + optional serif) and WeasyPrint subsets them into the PDF — this is what makes it look genuinely typeset rather than "default-PDF".
4. **No browser dependency / smaller, cleaner PDFs** — easier to run in a hackathon container.
5. **Charts/gauges:** render score gauges, RAG donuts, and maps to **SVG** (pure markup WeasyPrint draws natively) or PNG, then embed — no JS needed. (If you truly need live JS charts, switch the render step to Playwright while keeping the same HTML/CSS template.)

**Print-quality checklist (how to actually hit it in WeasyPrint):**
- Define **`@page`** with `size: Letter;` + `margin: 1in;` and margin boxes (`@top-left`, `@bottom-right`) for running header/footer.
- Page numbers via `content: "Page " counter(page) " of " counter(pages);`.
- **Embed fonts** with `@font-face { src: url(font.woff2) }` (local file URLs work; pass `base_url` so relative paths resolve).
- Control pagination: `break-inside: avoid` on figures/tables/callouts, `break-before: page` for new sections, `thead { display: table-header-group; }` to repeat headers.
- Use **`position: running(name)` + `content: element(name)`** to put a styled HTML header block into the page margin.
- Set DPI/image quality for embedded photos; supply 150–300 dpi raster images for crisp print.
- Generate **PDF bookmarks** automatically from `h1–h6` (built-in) for a navigable TOC.

---

## (e) Ready-to-Use CSS Skeleton

Pair with a Jinja2 HTML template; render via `weasyprint.HTML(string=html, base_url=".").write_pdf("out.pdf")`.

```css
/* ---------- Fonts (ship these files; WeasyPrint subsets them) ---------- */
@font-face {
  font-family: "ReportSans";
  src: url("fonts/Inter-Regular.woff2") format("woff2");
  font-weight: 400; font-style: normal;
}
@font-face {
  font-family: "ReportSans";
  src: url("fonts/Inter-Bold.woff2") format("woff2");
  font-weight: 700; font-style: normal;
}
/* Optional serif body alternative: Georgia/Source Serif. */

/* ---------- Design tokens ---------- */
:root {
  --ink:        #1A1A1A;
  --navy:       #14213D;   /* primary brand */
  --blue:       #2C5282;   /* secondary */
  --accent:     #E76F00;   /* single accent */
  --rule:       #D0D5DD;
  --fill:       #F2F4F7;   /* zebra / callout bg */
  --muted:      #667085;
  --go:         #2E7D32;
  --caution:    #D69E2E;
  --nogo:       #C62828;
}

/* ---------- Page geometry + running header/footer ---------- */
@page {
  size: Letter;            /* 8.5in x 11in; use A4 for non-US */
  margin: 1in 1in 1in 1in;

  @top-left {
    content: "Curbside EV Charging — Site Assessment";
    font: 8pt "ReportSans"; color: var(--muted);
  }
  @top-right {
    content: string(doc-section);  /* current section via string-set */
    font: 8pt "ReportSans"; color: var(--muted);
  }
  @bottom-left {
    content: "Confidential — Prepared for Client";
    font: 8pt "ReportSans"; color: var(--muted);
  }
  @bottom-right {
    content: "Page " counter(page) " of " counter(pages);
    font: 8pt "ReportSans"; color: var(--muted);
  }
}
@page :first { /* cover: suppress running header/footer */
  @top-left { content: none; } @top-right { content: none; }
  @bottom-left { content: none; } @bottom-right { content: none; }
}

/* ---------- Base type ---------- */
html { font-family: "ReportSans", Arial, Helvetica, sans-serif; }
body {
  color: var(--ink);
  font-size: 11pt;
  line-height: 1.5;
  font-weight: 400;
}
p { margin: 0 0 8pt; }

/* ---------- Headings + auto section numbering ---------- */
body { counter-reset: h2; }
h1 { font-size: 26pt; font-weight: 700; color: var(--navy); line-height: 1.15;
     margin: 0 0 12pt; }
h2 { font-size: 17pt; font-weight: 700; color: var(--navy); line-height: 1.2;
     margin: 18pt 0 6pt; break-after: avoid;
     counter-reset: h3; counter-increment: h2;
     string-set: doc-section content(); }
h2::before { content: counter(h2) "  "; color: var(--accent); }
h3 { font-size: 13pt; font-weight: 700; color: var(--blue); line-height: 1.3;
     margin: 12pt 0 4pt; break-after: avoid; counter-increment: h3; }
h3::before { content: counter(h2) "." counter(h3) "  "; color: var(--accent); }
h4 { font-size: 11pt; font-weight: 700; margin: 10pt 0 3pt; }

/* ---------- Cover ---------- */
.cover { break-after: page; text-align: left; }
.cover .band { height: 14pt; background: var(--navy); margin-bottom: 28pt; }
.cover .accent-rule { height: 4pt; width: 120pt; background: var(--accent);
                      margin: 10pt 0 24pt; }
.cover .meta { font-size: 10pt; color: var(--muted); line-height: 1.6; }

/* ---------- Tables (clean "financial" look) ---------- */
table { width: 100%; border-collapse: collapse; font-size: 9.5pt;
        margin: 8pt 0 4pt; }
thead { display: table-header-group; }           /* repeat header on break */
th { background: var(--navy); color: #fff; font-weight: 700; text-align: left;
     padding: 6pt 8pt; }
td { padding: 5pt 8pt; border-bottom: 0.5pt solid var(--rule); vertical-align: top; }
tbody tr:nth-child(even) td { background: var(--fill); }  /* zebra (optional) */
caption { caption-side: top; text-align: left; font-size: 8.5pt;
          font-weight: 700; color: var(--ink); margin-bottom: 3pt; }

/* ---------- Figures / photos ---------- */
figure { break-inside: avoid; margin: 10pt 0; }
figure img { width: 100%; height: auto; }
figcaption { font-size: 8.5pt; font-style: italic; color: var(--muted);
             margin-top: 4pt; }  /* caption BELOW figure */

/* ---------- Callout box ---------- */
.callout { background: var(--fill); border-left: 4pt solid var(--navy);
           padding: 10pt 12pt; margin: 10pt 0; break-inside: avoid; }
.callout.warn { border-left-color: var(--nogo); }

/* ---------- RAG scorecard chips (color + LETTER, a11y) ---------- */
.chip { display: inline-block; padding: 2pt 9pt; border-radius: 10pt;
        font: 700 9pt "ReportSans"; color: #fff; }
.chip.go      { background: var(--go); }
.chip.caution { background: var(--caution); color: #1A1A1A; }
.chip.nogo    { background: var(--nogo); }
/* usage: <span class="chip go">GO ✓</span> */

/* ---------- Big verdict badge (exec summary / cover) ---------- */
.verdict { display:inline-block; padding: 10pt 18pt; border-radius: 8pt;
           font: 700 16pt "ReportSans"; color:#fff; letter-spacing: .5pt; }
.verdict.go { background: var(--go); } .verdict.nogo { background: var(--nogo); }
.verdict.caution { background: var(--caution); color:#1A1A1A; }

/* ---------- Pagination control ---------- */
.section { break-before: page; }
.keep-together, h1, h2, h3, .callout, figure, tr { break-inside: avoid; }
```

**Python render (minimal):**
```python
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

html = Environment(loader=FileSystemLoader("templates")) \
        .get_template("report.html").render(**report_json)
HTML(string=html, base_url="assets/").write_pdf("site_report.pdf")
```

**To make it indistinguishable from a real firm's report:** ship a real brand-class font (Inter/Source Sans/Arial-class sans, or a Georgia/Source Serif body), use exactly ONE accent color, keep tables hairline-clean, put a numbered TOC + section numbers, repeat the header/footer with project ID + "Page X of Y", give every figure/photo a numbered caption, and lead with an executive summary + RAG verdict badge.

---

## (f) Sources

- AECOM Brand Identity Guidelines (primary typeface AECOM Sans, Arial fallback): https://docplayer.net/93929805-aecom-brand-identity-guidelines-june-2016.html and https://deltafonts.com/aecom-font/
- WSP brand identity (Helvetica Neue signature typeface): https://www.wsp.com/en-gl/legal/the-wsp-logo and https://www.scribd.com/document/706155072/WSP
- Arup brand/typeface (Trajan logo, Times New Roman): https://deltafonts.com/arup-font/ and https://logotyp.us/logo/arup/
- McKinsey/BCG/Bain typography, palette, slide standards: https://slideuplift.com/blog/mckinsey-style-presentation/ , https://deckary.com/blog/consulting-slide-standards , https://deckary.com/blog/bcg-presentation-style
- Corporate consulting color palette (hex): https://www.color-hex.com/color-palette/1060466
- Corporate/tech blue hex reference: https://coloruxlab.com/colors/blue
- Navy/Oxford-blue professional palette (#14213d + orange accent): https://venngage.com/blog/blue-color-palettes/ , https://icolorpalette.com/navy-and-blue/
- Technical report typography (fonts, 10–12 pt body, serif vs sans): https://smarttechsavvy.com/what-font-do-technical-reports-use/
- Typography best practices (sizes, leading 1.2–1.5x, 50–75ch line length): https://www.adoc-studio.app/blog/typography-guide and https://ithy.com/article/typography-font-size-spacing-lc0m3kwv
- Typography hierarchy (heading multipliers 1.5–2x body): https://www.mv3marketing.com/glossary/typography-hierarchy/
- Formal technical report formatting (page numbering, headings, figure/table captions): https://pressbooks.senecapolytechnic.ca/formaltechnicalreports/part/overall-format/
- Formal report layout/headers/footers/cover: https://pressbooks.senecapolytechnic.ca/busreportguide/part/format/ and https://www.boisestate.edu/cobe/cobe-writing-style-guide/guidelines-for-reports/
- Figures/tables conventions: https://pressbooks.bccampus.ca/technicalwriting/chapter/figurestables/
- Government engineering report standards (1" margins, 11pt Times, letter/A4): https://www.peo.on.ca/sites/default/files/2019-11/Engineering-Report-Guide.pdf
- Phase I ESA report sample (real layout, Calibri/Arial, letter size): https://www.gaeatech.com/public/CSA_Z768-01_Phase_I_ESA_Example.pdf
- Phase I ESA structure/sections: https://www.partneresi.com/resources/articles/what-is-a-phase-i-environmental-site-assessment/ and https://aeiconsultants.com/phase-i-environmental-site-assessment-checklist/
- Traffic light / RAG rating system (colors, accessibility R/A/G letters): https://en.wikipedia.org/wiki/Traffic_light_rating_system and https://citoolkit.com/articles/traffic-light-assessment/
- Go/No-Go + traffic-light scorecard visual design: https://www.slideteam.net/top-10-traffic-light-scorecard-powerpoint-presentation-templates and https://www.performancemagazine.org/red-yellow-and-green-signaling-in-performance-scorecards-%E2%80%93-part-2-%E2%80%93-meaning-of-colors/
- Table design / zebra striping best practices: https://uxmovement.com/content/9-design-techniques-for-user-friendly-tables/ , https://alistapart.com/article/zebrastripingmoredataforthecase/ , https://en.wikipedia.org/wiki/Zebra_striping
- WeasyPrint feature support (@page, margin boxes, running elements, counters, @font-face, bookmarks): https://doc.courtbouillon.org/weasyprint/stable/api_reference.html and https://doc.courtbouillon.org/weasyprint/stable/
- WeasyPrint CSS recipes (running headers/footers, page numbers, breaks): https://www.naveenmk.me/blog/weasyprint/ and https://medium.com/@engineering_holistic_ai/using-weasyprint-and-jinja2-to-create-pdfs-from-html-and-css-267127454dbd
- WeasyPrint vs Playwright comparison (JS, perf, deploy, file size): https://pdf4.dev/blog/playwright-vs-weasyprint and https://pdf4.dev/blog/html-to-pdf-benchmark-2026
- ReportLab Platypus (programmatic, table splitting/repeatRows): https://docs.reportlab.com/reportlab/userguide/ch5_platypus/ and https://woteq.com/using-reportlab-platypus-for-automated-document-layout-in-python
- Python HTML-to-PDF library overview: https://pdfbolt.com/blog/python-html-to-pdf-library and https://templated.io/blog/generate-pdfs-in-python-with-libraries/
