<!-- Section from: /Users/choi-dong-won/Desktop/devs/MaraudersMapMD-skill/SKILL.md | Lines: 48-676 -->

## Procedure

Follow these five phases in order. Each phase uses a MaraudersMapMD artifact as its primary reference.

### Original file protection rule

- The original source file must remain completely untouched. Never generate shards, indexes, or any MaraudersMapMD artifacts from the original.
- All sharding, indexing, and artifact generation targets the rewritten version file (`<base>.rewritten_v{N}.md`) exclusively.
- The original exists solely as a reference for fact-checking; it must never be modified, copied into artifact directories, or have artifacts derived from it.

Artifact paths (generated from the rewritten file only):
- AI Map: `docs/MaraudersMap/<docId>/ai-map.md`
- Section Pack: `docs/MaraudersMap/<docId>/sections/*.md`
- Search Index: `docs/MaraudersMap/<docId>/index.json`
- Shard JSON: `docs/MaraudersMap/<docId>/shards.json`
- Diagram Images: `docs/MaraudersMap/<docId>/images/*.png`

> [AI RULE] `<docId>` is derived from the rewritten version filename (e.g. `guide.rewritten_v2.md` → docId `guide_v2`). Never create a separate `<docId>` for the original file.

### Language lock rule (highest priority)

- The rewritten output must preserve the source language exactly; translation is prohibited unless the user explicitly asks for translation.
- If source content is Korean, keep Korean narrative text, headings, and list items in Korean.
- Keep existing English technical literals as-is (commands, code, identifiers, API names, file paths, env vars).
- If mixed-language content exists, preserve each segment's original language unless the user requests normalization.
- If a generated section accidentally changes language, treat it as a blocking error and rewrite that section before finalizing.

> [AI RULE] Language drift (for example Korean source rewritten in English) is a hard failure. Fix before completion.

### Sharded access rule (always-on)

- For fast lookup and reading, use the Section Pack (`sections/*.md`) as the primary source instead of the rewritten full document.
- Only open the rewritten file when you need full-context validation or to resolve cross-section ambiguity.
- The Section Pack must always be an exact shard-by-shard reflection of the rewritten document.
- Shards and indexes exist only for rewritten documents. If artifacts for the original file are found, delete them immediately.

### Retrieval order for accuracy

When answering or extracting facts, use this order to minimize drift:
1. Section Pack (`sections/*.md`) for the specific section.
2. Search Index (`index.json`) for keywords/links/AI Hint Blocks validation.
3. AI Map (`ai-map.md`) for section boundaries and summaries.
4. Rewritten full document only if cross-section context is required.

### Retrieval routing

Choose the fastest retrieval path based on the query scope:

| Query Scope | Route | Tool |
|---|---|---|
| Single section by keyword | **Fast-path** | `shards_search.py --shards ... --keyword "<kw>"` |
| Relevance-ranked results | **BM25 JSON** | `shards_search.py --shards ... --query "<text>" --top 5` |
| Cross-doc keyword search | **SQLite keyword** | `shards_search.py --db docs/MaraudersMap/shards.db --keyword "<kw>"` |
| Cross-doc relevance search | **SQLite FTS5** | `shards_search.py --db docs/MaraudersMap/shards.db --query "<text>"` |
| Regex pattern match | **Regex** | `shards_search.py --shards ... --regex "<pattern>"` or `--db ... --regex "<pattern>"` |
| Full context validation | **Fallback** | Open `<base>.rewritten_v{N}.md` directly |

> [AI RULE] Always attempt fast-path or BM25 before opening the full rewritten document. Only fall back to the full document when cross-section context is needed and shard results are insufficient.

### Doc-type awareness

Different document types benefit from different retrieval strategies:

| Doc Type | Signal | Strategy |
|---|---|---|
| API Reference | Many short sections, code-heavy | Keyword search → exact section |
| Tutorial/Guide | Sequential sections, prose-heavy | BM25 → top 3, read in order |
| Configuration | Tables, key-value pairs | Keyword → single section |
| Architecture | Diagrams, cross-references | Cross-doc search → multiple sections |
| Mixed | No dominant pattern | BM25 → top 5, scan titles first |

> [AI CONTEXT] Doc-type is inferred from AI Map structure and section content. No explicit tagging required.

### Parallel execution rule

When working with multiple documents or many sections, maximize throughput by running independent operations in parallel.

Parallelizable operations (no ordering dependency):

| Operation | Parallel Unit | Constraint |
|---|---|---|
| Multi-document rewrite | Each document is independent | Different `<docId>` → safe to parallelize |
| Section-by-section rewrite (Phase 4) | Sections that do NOT cross-reference each other | If section B references section A, rewrite A first |
| Shard + index generation (Phase 5) | Per-document artifact generation | Each `<docId>` writes to its own directory |
| `shards_to_json.py` runs | One run per `<docId>` | Each writes to `docs/MaraudersMap/<docId>/shards.json` — no conflict |
| `shards_db.py --ingest` runs | One ingest per `<docId>` | SQLite handles concurrent reads; run ingests sequentially or use `--ingest-all` |
| Verification (Phase 5 checks 1–4) | Per-document | Each document's checklist is independent |

Must remain sequential (ordering dependency exists):

| Operation | Reason |
|---|---|
| Phase 1 → 2 → 3 within a single document | Each phase depends on the previous |
| Skeleton (Phase 3) before section rewrite (Phase 4) | Heading structure must exist before filling content |
| Section rewrite → shard generation | Shards must reflect the final rewritten content |
| `shards_to_json.py` → `shards_db.py --ingest` for the same doc | DB ingests from `shards.json`, so JSON must exist first |

Execution strategy by scale:

| Scale | Strategy |
|---|---|
| 1 document, ≤5 sections | Sequential is fine |
| 1 document, >5 sections | Parallel-rewrite independent sections, then sequential for cross-referencing ones |
| 2–5 documents | Parallel-rewrite all documents simultaneously |
| >5 documents | Batch: parallel-rewrite up to 5 at a time, then `shards_db.py --ingest-all` once at the end |

> [AI RULE] When the AI agent supports parallel tool calls or background tasks, it MUST use them for independent operations listed above. Sequential processing of independent documents is a performance bug.

### Accuracy guardrails

- Do not infer facts that are not present in the shards or index.
- If a fact appears in a shard but is missing from the index, treat the shard as the source of truth and regenerate the index.
- If shards disagree with the rewritten document, regenerate shards and index from the rewritten document immediately.

### JSON shard pack rule (Python-first)

- Generate `shards.json` from the Section Pack and Search Index to enable fast, accurate Python lookup.
- Treat `shards.json` as a read-optimized mirror. The source of truth remains the shards and rewritten document.
- Any time shards or index change, regenerate `shards.json` before answering questions.
- Use `python shards_to_json.py --doc-root docs/MaraudersMap/<docId>` to rebuild the JSON pack.
- For quick lookup, use `python shards_search.py --shards docs/MaraudersMap/<docId>/shards.json --keyword "<keyword>"`.
- For fastest relevance ranking, use `python shards_search.py --shards docs/MaraudersMap/<docId>/shards.json --query "<free text>" --top 5` (BM25).
- For incremental rebuilds: `python shards_to_json.py --doc-root docs/MaraudersMap/<docId> --changed` (skips rebuild if no content changes detected).
- To preview changes without writing: `python shards_to_json.py --doc-root docs/MaraudersMap/<docId> --dry-run --report`.
- To build and ingest into the cross-doc SQLite index: `python shards_db.py --ingest docs/MaraudersMap/<docId> --map-root docs/MaraudersMap`.
- To initialize the cross-doc index for the first time: `python shards_db.py --init --map-root docs/MaraudersMap`.
- To search across all documents: `python shards_search.py --db docs/MaraudersMap/shards.db --query "<text>" --top 5`.

### ASCII visual content classification

Before converting any ASCII art, classify it into one of three categories. The category determines the target format.

Decision tree:

1. **Does the ASCII block contain rows of data with column alignment?** (column headers, separator rows like `+---+---+` or `├───┼───┤`, and cells holding data values such as names, numbers, or settings)
   → **Category: Data Table** → convert to Markdown pipe table (see "ASCII-to-Markdown-table conversion rule").

2. **Does the ASCII block represent a quantitative visualization?** (bar lengths made of repeated characters like `█`, `▓`, `#`, `=`, `*`; axis labels with numeric values; histogram bins; sparkline-style rows)
   → **Category: Chart** → convert to Markdown table (if simple) or HTML rendering → screenshot PNG image (if complex) (see "ASCII-to-chart conversion rule").

3. **Does the ASCII block represent structural relationships?** (boxes connected by arrows or lines; flow direction; entity-relationship grouping; sequence lifelines; tree/hierarchy)
   → **Category: Diagram** → convert to HTML diagram, render as screenshot PNG, embed as image (see "ASCII-to-HTML-diagram conversion rule").

Ambiguity rules:
- If a block mixes data rows with structural arrows, split it: data rows → MD table, structural part → HTML diagram screenshot.
- If a pipe-aligned block is clearly a diagram legend or label (no meaningful row data), treat it as part of the diagram.
- When in doubt, prefer the simpler format (MD table over HTML screenshot) to maximize portability.
- Add a one-line HTML comment `<!-- Converted from ASCII art: [original description] -->` above each converted block so reviewers can trace origin.

> [AI RULE] Never leave ASCII art unconverted. Every ASCII visual block must be classified and transformed to its target format.

### ASCII-to-HTML-diagram conversion rule

When the source Markdown contains ASCII art diagrams (box-drawing characters like `┌─┐│└─┘`, `+---+`, pipe-aligned tables used as diagrams, or any text-art layout representing structure), convert them to high-quality PNG images via HTML rendering and screenshot capture.

Conversion pipeline:
1. **Analyze** the ASCII diagram — identify entities, relationships, groupings, flow direction, and labels.
2. **Generate** a self-contained HTML file with inline CSS that visually reproduces the diagram as a clean, professional graphic.
3. **Render** the HTML in a headless browser (Playwright or equivalent browser tool).
4. **Screenshot** the rendered diagram as a PNG image.
5. **Save** the PNG to `docs/MaraudersMap/<docId>/images/<diagram-name>.png`.
6. **Embed** the image in the Markdown output: `![<diagram description>](images/<diagram-name>.png)`.
7. **Delete** the temporary HTML file. Do not keep it in the output.

Conversion guidelines:
- Identify the diagram type and apply the matching HTML/CSS pattern (see "Diagram type HTML/CSS templates" below):
  - DB schemas, ER diagrams → entity-box layout with relationship lines
  - Architecture, system layout, grouping → nested container layout with labeled connections
  - Flows, pipelines → node-and-arrow horizontal or vertical layout
  - Sequences, timelines → lifeline-based column layout
  - Class/object relationships → box layout with typed connectors
  - Tree/hierarchy → indented or layered box layout
- Preserve every entity, relationship, label, and grouping from the original ASCII art. Do not omit items.
- Use nested `<div>` containers for grouped/boxed sections when the original uses visual grouping.
- If the ASCII art is ambiguous, add a one-line HTML comment in the generated HTML noting the assumption.
- Do not keep the original ASCII art alongside the embedded image; replace it entirely.

Naming convention for diagram images:
- Use a descriptive kebab-case name derived from the diagram's context: `architecture-overview.png`, `auth-flow.png`, `er-schema.png`.
- If multiple diagrams exist in the same document, suffix with a zero-padded index in document order: `data-flow-01.png`, `data-flow-02.png`.
- Naming must be deterministic: for the same input, produce the same filenames every run.
- If a filename collision occurs in the same `<docId>`, append a short stable suffix: `data-flow-01-a3f2.png`.

### Diagram rendering and capture rule

Every diagram image must be visually verified. A broken or mis-rendered diagram is worse than no diagram.

Rendering flow:
1. Write the self-contained HTML file to `temp/diagram-<name>.html`.
2. Create `docs/MaraudersMap/<docId>/images/` if it does not exist.
3. Navigate the browser tool to `file://<absolute-path>/temp/diagram-<name>.html`.
4. Wait at least 400 ms for rendering to stabilize.
5. Call the browser tool's screenshot function with the output file path explicitly set to the absolute path of `docs/MaraudersMap/<docId>/images/<diagram-name>.png`. Do not rely on a default save location.
6. **Always regenerate on this run**: do not depend on pre-existing PNG files. For each converted diagram, create or overwrite `docs/MaraudersMap/<docId>/images/<diagram-name>.png` in the current run.
7. **Hard gate**: Check that the PNG file exists on disk and has non-zero size. If it is missing or empty, retry from step 3 with 800 ms wait. If it still fails, delete any partial output, fix the HTML/CSS, and retry until capture succeeds. Never finish with a missing PNG for a converted diagram.
8. Visually verify: all labels readable, no overlapping elements, layout matches original. If broken, fix the HTML/CSS and redo from step 3.
9. Keep `temp/diagram-<name>.html` until the PNG is confirmed on disk and the Markdown image tag has been inserted.
10. Compute the relative path from the rewritten Markdown file's directory to the saved PNG. Example: if the Markdown is at `docs/FORM_EVENT.rewritten_v1.md` and the PNG is at `docs/MaraudersMap/FORM_EVENT/images/campaign-lifecycle.png`, the relative path is `./MaraudersMap/FORM_EVENT/images/campaign-lifecycle.png`.
11. In the rewritten Markdown, locate the exact lines of the original ASCII block (start line to end line). Delete those lines entirely — do not touch any surrounding text, headings, or links. Insert the following two lines in their place, and nothing else:
    ```
    <!-- Converted from ASCII art: [original description] -->
    ![<diagram description>](<relative-path-to-png>)
    ```
    The result must be exactly one comment line followed by exactly one image tag line. No extra text, no duplicate alt, no wrapping in a link.
12. Re-check that the referenced PNG path in the inserted image tag exists on disk. Only then delete `temp/diagram-<name>.html`.

Failure handling:
- If capture fails, keep the temp HTML for retry and delete only broken PNG output. Retry capture from step 3 using the same HTML.
- If an expected image file is missing (including user-deleted files), treat it as a required regeneration task and recreate it in the current run.
- Never keep partial or invalid outputs.
- Keep captured PNGs on local disk; Markdown image links depend on them.

Regression guard (required):
- Reproduce this case before finalizing any diagram conversion: Markdown references `./MaraudersMap/FORM_EVENT_INTRODUCTION/images/campaign-lifecycle.png` but the PNG file is missing on disk.
- Expected behavior: regenerate `docs/MaraudersMap/FORM_EVENT_INTRODUCTION/images/campaign-lifecycle.png` in the same run, then keep exactly one valid Markdown image tag pointing to the relative path.
- Forbidden behavior: leaving a dangling image path, deleting the temp HTML before successful capture, producing malformed Markdown such as `![a]![a](...)` or `[text](/![a](...))`.

Screenshot quality:
- Viewport: 600–1200 px wide. Device pixel ratio: 2.
- Background: white (`#ffffff`). No browser chrome or scrollbars.
- All text legible at final embedded size.

> [AI RULE] Never embed a diagram image that has not been visually verified. If the rendering looks wrong, fix and re-render.

### Diagram type HTML/CSS templates

Use these patterns as a starting point when generating HTML for each diagram type. Adapt layout, colors, and sizing to match the specific diagram's content. All templates share these base styles:

**Base styles (shared across all diagram types):**

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #ffffff;
    padding: 16px;
    width: fit-content;
    color: #1e293b;
  }
  .diagram { display: inline-block; }
  .box {
    border: 1.5px solid #64748b;
    border-radius: 8px;
    padding: 10px 16px;
    background: #f8fafc;
    font-size: 13px;
    font-weight: 500;
    text-align: center;
    white-space: nowrap;
  }
  .box-title {
    font-size: 11px;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
  }
  .container {
    border: 2px solid #334155;
    border-radius: 12px;
    padding: 20px;
    background: #ffffff;
    position: relative;
  }
  .container-label {
    font-size: 15px;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 16px;
  }
  .row {
    display: flex;
    gap: 16px;
    justify-content: center;
    align-items: flex-start;
  }
  .col {
    display: flex;
    flex-direction: column;
    gap: 12px;
    align-items: center;
  }
  .arrow-down {
    width: 2px;
    height: 24px;
    background: #94a3b8;
    position: relative;
    margin: 0 auto;
  }
  .arrow-down::after {
    content: '';
    position: absolute;
    bottom: -4px;
    left: 50%;
    transform: translateX(-50%);
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #94a3b8;
  }
  .arrow-right {
    width: 24px;
    height: 2px;
    background: #94a3b8;
    position: relative;
    align-self: center;
  }
  .arrow-right::after {
    content: '';
    position: absolute;
    right: -4px;
    top: 50%;
    transform: translateY(-50%);
    border-top: 5px solid transparent;
    border-bottom: 5px solid transparent;
    border-left: 6px solid #94a3b8;
  }
  .badge {
    display: inline-block;
    font-size: 11px;
    font-weight: 500;
    color: #475569;
    background: #e2e8f0;
    border-radius: 4px;
    padding: 2px 8px;
    margin-top: 4px;
  }
  .separator {
    width: 100%;
    height: 1px;
    background: #e2e8f0;
    margin: 16px 0;
  }
</style>
</head>
<body>
<div class="diagram">
  <!-- Diagram content here -->
</div>
</body>
</html>
```

**Architecture / system layout diagram:**

Use nested `.container` elements for system boundaries and `.box` for components. Connect with `.arrow-down` or `.arrow-right`. Example structure:

```html
<div class="container">
  <div class="container-label">System Name</div>
  <div class="row">
    <div class="box">Component A</div>
    <div class="arrow-right"></div>
    <div class="box">Component B</div>
    <div class="arrow-right"></div>
    <div class="box">Component C</div>
  </div>
  <div class="arrow-down"></div>
  <div class="container" style="border-color: #94a3b8;">
    <div class="container-label" style="font-size: 13px;">Data Layer</div>
    <div class="row">
      <div class="box">
        <div class="box-title">table</div>
        cache
      </div>
      <div class="box">
        <div class="box-title">table</div>
        queue_jobs
      </div>
    </div>
  </div>
</div>
```

**Flowchart / pipeline diagram:**

Use horizontal (`.row`) or vertical (`.col`) layouts with arrows between steps. For decision nodes, use a rotated diamond shape:

```html
<div class="col">
  <div class="box" style="background: #dbeafe; border-color: #3b82f6;">Start</div>
  <div class="arrow-down"></div>
  <div class="box">Process A</div>
  <div class="arrow-down"></div>
  <div class="box" style="transform: rotate(45deg); width: 80px; height: 80px; display: flex; align-items: center; justify-content: center; border-radius: 4px;">
    <span style="transform: rotate(-45deg); font-size: 12px;">Condition?</span>
  </div>
  <div class="row" style="margin-top: 16px;">
    <div class="col">
      <div class="badge">Yes</div>
      <div class="arrow-down"></div>
      <div class="box">Action X</div>
    </div>
    <div style="width: 48px;"></div>
    <div class="col">
      <div class="badge">No</div>
      <div class="arrow-down"></div>
      <div class="box">Action Y</div>
    </div>
  </div>
</div>
```

**ER / database schema diagram:**

Use table-like boxes with attribute lists. Connect entities with labeled lines using SVG or CSS pseudo-elements:

```html
<div class="row" style="gap: 64px; align-items: flex-start;">
  <div class="box" style="text-align: left; padding: 0; overflow: hidden;">
    <div style="background: #334155; color: #fff; padding: 8px 16px; font-weight: 600; font-size: 14px;">users</div>
    <div style="padding: 8px 16px; font-size: 13px; line-height: 1.8;">
      <strong>id</strong> : uuid (PK)<br>
      name : varchar<br>
      email : varchar (UQ)<br>
      created_at : timestamp
    </div>
  </div>
  <div style="align-self: center; font-size: 12px; color: #64748b;">1 ──── N</div>
  <div class="box" style="text-align: left; padding: 0; overflow: hidden;">
    <div style="background: #334155; color: #fff; padding: 8px 16px; font-weight: 600; font-size: 14px;">orders</div>
    <div style="padding: 8px 16px; font-size: 13px; line-height: 1.8;">
      <strong>id</strong> : uuid (PK)<br>
      user_id : uuid (FK)<br>
      total : decimal<br>
      status : enum
    </div>
  </div>
</div>
```

**Sequence diagram:**

Use column-based layout with vertical lifelines and horizontal message arrows. Lifelines are vertical dashed borders; messages are styled horizontal connectors:

```html
<div style="display: flex; gap: 0; position: relative; min-height: 300px;">
  <!-- Participant headers -->
  <div style="flex: 1; text-align: center;">
    <div class="box" style="display: inline-block; margin-bottom: 8px;">Client</div>
    <div style="width: 2px; height: 250px; border-left: 2px dashed #cbd5e1; margin: 0 auto;"></div>
  </div>
  <div style="flex: 1; text-align: center;">
    <div class="box" style="display: inline-block; margin-bottom: 8px;">Server</div>
    <div style="width: 2px; height: 250px; border-left: 2px dashed #cbd5e1; margin: 0 auto;"></div>
  </div>
  <!-- Messages (absolutely positioned over lifelines) -->
  <div style="position: absolute; top: 60px; left: 15%; right: 15%;">
    <div style="display: flex; align-items: center; margin-bottom: 24px;">
      <span style="font-size: 12px; flex: 1; text-align: center;">POST /login</span>
    </div>
    <div style="height: 2px; background: #475569; position: relative;">
      <div style="position: absolute; right: -4px; top: -4px; border-left: 6px solid #475569; border-top: 5px solid transparent; border-bottom: 5px solid transparent;"></div>
    </div>
  </div>
</div>
```

**Tree / hierarchy diagram:**

Use a recursive nested structure with indented containers:

```html
<div class="col" style="align-items: flex-start;">
  <div class="box" style="background: #dbeafe; border-color: #3b82f6; font-weight: 600;">Root Node</div>
  <div style="display: flex; gap: 32px; margin-left: 24px; margin-top: 12px;">
    <div class="col" style="align-items: flex-start;">
      <div style="display: flex; align-items: center; gap: 8px;">
        <div style="width: 16px; height: 2px; background: #94a3b8;"></div>
        <div class="box">Child A</div>
      </div>
      <div style="margin-left: 24px; margin-top: 8px;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <div style="width: 16px; height: 2px; background: #94a3b8;"></div>
          <div class="box" style="font-size: 12px;">Leaf A-1</div>
        </div>
      </div>
    </div>
    <div class="col" style="align-items: flex-start;">
      <div style="display: flex; align-items: center; gap: 8px;">
        <div style="width: 16px; height: 2px; background: #94a3b8;"></div>
        <div class="box">Child B</div>
      </div>
    </div>
  </div>
</div>
```

Adaptation guidelines:
- These templates are starting points. Adjust colors, sizes, gaps, and nesting to match the specific diagram's complexity.
- For very complex diagrams with many connections, consider using inline SVG for precise line routing instead of CSS-only arrows.
- Use `position: absolute` sparingly — prefer flexbox/grid layout for maintainability.
- Keep font sizes between 11px–15px for readability in the final screenshot.
- Test that the diagram fits within the 600–1200px viewport width before capturing.

### ASCII-to-Markdown-table conversion rule

When the source Markdown contains data tables drawn with ASCII art (box-drawing characters, `+---+` borders, or space/tab-aligned columns), convert them to standard Markdown pipe tables.

Detection patterns — any of these signals a data table:
- Rows delimited by `+---+---+` or `├───┼───┤` or `|---|---|` style separators.
- Cells bounded by `|` or `│` containing data values (not arrows or flow labels).
- Space-aligned columns with a clear header row followed by a separator row of dashes or `=`.
- Box-drawing grids (`┌┬┐`, `├┼┤`, `└┴┘`) where cells hold scalar data (names, numbers, settings, status).

Conversion guidelines:
- Detect columns by splitting each row on the delimiter character (`|`, `│`, or consistent whitespace).
- Trim leading/trailing whitespace in each cell.
- Identify the header row (first data row, or the row directly above the first separator) and emit it as the Markdown table header.
- Emit a separator row `|---|---|...` immediately after the header. Use `:---`, `:---:`, or `---:` to preserve original alignment if detectable.
- Emit each subsequent data row as a pipe-delimited row.
- If the original table has merged/spanned cells, approximate with repeated values or add a footnote explaining the merge.
- If the original table has row-group separators (thicker lines, double borders), insert a blank row or a bold label row in the Markdown output to maintain grouping.
- Preserve every data value exactly. Do not summarize, round, or omit any cell.

> [AI RULE] A converted Markdown table must contain the exact same number of data rows and columns as the ASCII original. Any mismatch is a data-loss bug.

### ASCII-to-chart conversion rule

When the source Markdown contains ASCII art representing quantitative data visualization (bar charts, histograms, sparklines, pie-chart text), convert it to the most readable Markdown-native format.

Detection patterns — any of these signals a chart:
- Rows with repeated fill characters (`█`, `▓`, `▒`, `░`, `#`, `=`, `*`, `■`) whose length encodes a numeric value.
- An axis label column on the left and a bar on the right (horizontal bar chart).
- Vertical columns of fill characters with labels at the bottom (vertical bar chart).
- Percentage labels next to segments (pie-chart text representation).
- Numeric scale markers along an edge (axis ticks).

Conversion decision:
- **Simple bar chart (≤10 items, single series)** → Markdown table with a `Bar` column using repeated `█` in inline code for visual reference, plus a numeric `Value` column.
- **Multi-series or complex chart** → HTML rendering → screenshot PNG image (use CSS bar/chart layout with inline styles).
- **Pie/donut chart** → HTML rendering → screenshot PNG image (use SVG `<circle>` with `stroke-dasharray` for segments).
- **Sparkline or trend** → Markdown table with rows for each data point; optionally HTML rendering → screenshot PNG image (use SVG `<polyline>` for line charts).

Conversion guidelines:
- Extract every data label and its corresponding value from the ASCII chart.
- Preserve the original data ordering (e.g., descending by value, chronological).
- Include units if present in the original (e.g., `%`, `ms`, `MB`).
- For HTML chart images, add a `title` matching the original chart's caption or heading context.
- Validate HTML chart images using the same rendering and capture flow as diagrams (see "Diagram rendering and capture rule").

> [AI RULE] Every numeric value visible in the ASCII chart must appear in the converted output. Missing data points are conversion failures.

### Repository safety rule

- Never modify `README.md` in this repository. All changes must be confined to skill artifacts and generated MaraudersMapMD outputs only.

### Artifact hygiene and structure rule

- Always delete outdated or superseded MaraudersMapMD artifacts (old shard packs, stale indexes, obsolete JSON packs) so the project folder never accumulates unused files.
- Enforce a single, stable folder structure: `docs/MaraudersMap/<docId>/{ai-map.md,index.json,shards.json,.manifest.json,sections/*.md,images/*.png}`. The cross-doc index lives at docs/MaraudersMap/shards.db.
- One `<docId>` directory per rewritten version. `<docId>` corresponds to the rewritten version file, not the original.
- If artifacts derived from the original source file exist, delete them immediately.
- Do not create or keep alternative artifact directories or extra copies outside the structure above.
- Delete orphaned images in `docs/MaraudersMap/<docId>/images/` that are not referenced by the rewritten Markdown, but only after all converted ASCII blocks have been embedded and verified. Do not run orphan cleanup during capture.
- Never delete PNG files that are referenced by the active rewritten Markdown.
- Before finalizing, ensure no `temp/diagram-*.html` files remain.

### Final honest review rule

- Always end the workflow with a brief self-audit: re-check completed work against all rules and verify nothing is missing.
- If any gap is found, fix it before completing the task.

### Phase 1 — Baseline capture (before any rewriting)

Read the original source file directly. If existing MaraudersMapMD artifacts already exist for a previous rewritten version, read the AI Map (`ai-map.md`) for section summaries and the Search Index (`index.json`) for keywords/links. These help understand structure but do not replace reading the original. Do not rewrite anything yet. Do not generate any artifacts from the original file.

### Phase 2 — Create working copy

Determine the base name and next version before creating any file:

- **Base name**: Strip any `.rewritten_v{n}` suffix from the source filename. `guide.md` → base `guide`. `guide.rewritten_v1.md` → base `guide`. Never include `.rewritten_v{n}` in the base.
- **Next version**: If no prior rewritten file exists, use `v1`. If `<base>.rewritten_v{n}.md` already exists, use `v{n+1}`.
- **Working copy path**: `temp/temp_<base>.rewritten_v{N}.md` where `N` is the next version.
- **Filename normalization gate (required)**: Before writing output, normalize the target name to `<base>.rewritten_v{N}.md`. Remove any chained segments such as `.rewritten.rewritten`, `.rewritten_v1.rewritten_v2`, or repeated `.rewritten` tokens. These names are invalid and must be corrected before saving.

Examples: `guide.md` (first run) → `temp/temp_guide.rewritten_v1.md`. `guide.rewritten_v1.md` (re-run) → `temp/temp_guide.rewritten_v2.md`. `guide.rewritten.rewritten.md` (invalid source name) still normalizes to base `guide` and must output `temp/temp_guide.rewritten_v{N}.md`.

All intermediate files go inside `temp/`. All edits happen ONLY on the working copy. Never modify the source.

### Phase 3 — Skeleton

Using the AI Map table as a guide, write a flat heading list in the working copy. Next to each heading note its one-line purpose. Fix heading levels so they descend without skips (single `#`, then `##`, then `###`). If the document is long, place a concise summary after the title.

### Phase 4 — Section-by-section rewrite

Open each Section Pack file (`sections/*.md`). For each section:
1. Check the Search Index entry for that section's keywords, links, and AI Hint Blocks.
2. Apply the canonical prompt rules: shorten paragraphs, convert dense prose to bullets, use tables for settings/options, keep code blocks unchanged.
3. Preserve every keyword, link, and AI Hint Block listed in the index entry.
4. Make the section self-contained. Use brief cross-references ("see Section X") instead of repeating content.

Parallel rewrite guidance: Sections that do not reference each other may be rewritten in parallel (see "Parallel execution rule"). When unsure about cross-references, rewrite sequentially to preserve consistency.

### Phase 5 — Verification and cleanup

Compare the finished output against the original Search Index:
1. Every keyword in the index must appear in the output.
2. Every AI Hint Block in the index must appear in the output.
3. Every link in the index must appear in the output.
4. Token count of the output should not significantly exceed the original (check AI Map's total).
5. Run the checklist below.

After verification passes:
1. Move `temp/temp_<base>.rewritten_v{N}.md` to the original file's directory as `<base>.rewritten_v{N}.md`.
2. Generate MaraudersMapMD artifacts from `<base>.rewritten_v{N}.md` only (never from the original).
3. Verify each `sections/*.md` shard matches its corresponding content in `<base>.rewritten_v{N}.md` (no drift).
4. Regenerate `shards.json` from the freshly generated shards and index.
5. If processing multiple documents, run steps 2–4 in parallel for each `<docId>` (see "Parallel execution rule"). Then run `python shards_db.py --ingest-all --map-root docs/MaraudersMap` once to batch-update the cross-doc index.
6. Delete the `temp/` folder entirely.
7. Delete any stale or original-file-derived MaraudersMapMD artifacts. Only artifacts derived from the rewritten file may remain.
8. Confirm the project contains: the original source file (untouched), `<base>.rewritten_v{N}.md`, and one set of MaraudersMapMD artifacts under `docs/MaraudersMap/<docId>/` (including `images/*.png` if any diagrams were converted). PNG files referenced by Markdown must remain on local disk. If any referenced PNG is missing (including manual deletion), regenerate it before completion. No `temp/` folder, no `temp_` files, no original-derived artifacts, no temporary HTML files.
9. Confirm there are no invalid rewritten filenames in the working set (for example `*.rewritten.rewritten.md` or `*.rewritten_v*.rewritten_v*.md`). If found, rename to the normalized `<base>.rewritten_v{N}.md` form before completion.

### Sync rule — rewritten changes must update shards

If the rewritten document is edited at any time:
1. Re-run the MaraudersMapMD generation on the current rewritten version file (`<base>.rewritten_v{N}.md`).
2. Replace the Section Pack and Search Index with the newly generated versions.
3. Regenerate `shards.json` from the updated shards and index.
4. If a cross-doc SQLite index exists (`shards.db`), re-ingest the updated doc: `python shards_db.py --ingest docs/MaraudersMap/<docId> --map-root docs/MaraudersMap`.
5. Do not continue work until shards, index, and `shards.json` exactly match the rewritten document.
