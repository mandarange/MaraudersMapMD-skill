---
name: maraudersmapmd-skill
description: Rewrite Markdown documents to maximize readability and scan-ability and keep sharded Markdown packs in sync for fast lookup. Use this skill when the user asks to improve, rewrite, or optimize a Markdown document for readability, when asked to apply MaraudersMapMD readability formatting, or when sharded Markdown access is required.
metadata:
  version: "9.0.0"
  source: "MaraudersMapMD src/ai/aiService.ts buildReadabilityPrompt()"
  tags:
    - markdown
    - readability
    - formatting
    - maraudersmapmd
---

# MaraudersMapMD Skill

## When to Use

- User asks to improve readability, rewrite for clarity, or optimize a Markdown document for scanning
- User asks to apply MaraudersMapMD formatting or make a document AI-readable
- User provides a Markdown document and asks for editorial polish
- User asks to access content quickly via sharded Markdown or to keep shards synced with the rewritten document

## Canonical Prompt

The text below is copied verbatim from `buildReadabilityPrompt()` in `src/ai/aiService.ts` of the MaraudersMapMD extension. Apply it as-is. `${source}` stands for the user-provided Markdown.

You are an expert technical editor. Rewrite the Markdown to maximize readability and scan-ability while preserving meaning and intent.

Core requirements:
- Keep the final language the same as the original (do not translate). If mixed, use the dominant language.
- Preserve all facts, constraints, and technical details. Do not add new information.
- Keep Markdown semantics correct (headings, lists, tables, code fences, links).
- Use the project's AI hint block format where it helps: "> [AI RULE]", "> [AI DECISION]", "> [AI TODO]", "> [AI CONTEXT]".
- Prefer short paragraphs, clear headings, and consistent numbering.
- Use tables for settings, options, or structured comparisons when helpful.
- Keep code blocks and inline code exactly as-is.
- Convert ASCII art visuals to the appropriate Markdown-native format (see "ASCII visual content classification" below):
  - **Data tables** drawn with ASCII borders → proper Markdown pipe tables.
  - **Diagrams** (flowcharts, ER, architecture) → Mermaid code blocks.
  - **Charts** (bar charts, histograms, sparklines) → Markdown tables or Mermaid `xychart-beta` / `pie` blocks.
- Remove fluff and redundancy; keep only what's necessary.
- Output ONLY the final Markdown. No commentary.

Formatting guidance:
- Ensure headings follow a clean hierarchy.
- Convert dense prose into bullet lists where it improves readability.
- Keep a concise top summary if the document is long.

SOURCE MARKDOWN (do not omit any content):
<<<BEGIN MARKDOWN
${source}
END MARKDOWN>>>

## Procedure

Follow these five phases in order. Each phase uses a MaraudersMapMD artifact as its primary reference.

### Original file protection rule

- The original source file must remain completely untouched. Never generate shards, indexes, or any MaraudersMapMD artifacts from the original.
- All sharding, indexing, and artifact generation targets the rewritten file (`<filename>.rewritten.md`) exclusively.
- The original exists solely as a reference for fact-checking; it must never be modified, copied into artifact directories, or have artifacts derived from it.

Artifact paths (generated from the rewritten file only):
- AI Map: `docs/MaraudersMap/<docId>/ai-map.md`
- Section Pack: `docs/MaraudersMap/<docId>/sections/*.md`
- Search Index: `docs/MaraudersMap/<docId>/index.json`
- Shard JSON: `docs/MaraudersMap/<docId>/shards.json`

> [AI RULE] `<docId>` is derived from the rewritten filename (e.g. `guide.rewritten.md` → docId `guide`). Never create a separate `<docId>` for the original file.

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
| Full context validation | **Fallback** | Open `<filename>.rewritten.md` directly |

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
   → **Category: Chart** → convert to Markdown table (if simple) or Mermaid `xychart-beta` / `pie` (if complex) (see "ASCII-to-chart conversion rule").

3. **Does the ASCII block represent structural relationships?** (boxes connected by arrows or lines; flow direction; entity-relationship grouping; sequence lifelines; tree/hierarchy)
   → **Category: Diagram** → convert to Mermaid code block (see "ASCII-to-Mermaid conversion rule").

Ambiguity rules:
- If a block mixes data rows with structural arrows, split it: data rows → MD table, structural part → Mermaid.
- If a pipe-aligned block is clearly a diagram legend or label (no meaningful row data), treat it as part of the diagram.
- When in doubt, prefer the simpler format (MD table over Mermaid) to maximize portability.
- Add a one-line HTML comment `<!-- Converted from ASCII art: [original description] -->` above each converted block so reviewers can trace origin.

> [AI RULE] Never leave ASCII art unconverted. Every ASCII visual block must be classified and transformed to its target format.

### ASCII-to-Mermaid conversion rule

When the source Markdown contains ASCII art diagrams (box-drawing characters like `┌─┐│└─┘`, `+---+`, pipe-aligned tables used as diagrams, or any text-art layout representing structure), convert them to Mermaid code blocks during rewriting.

Conversion guidelines:
- Identify the diagram type and pick the best-fit Mermaid diagram:
  - DB schemas, ER diagrams → `erDiagram`
  - Architecture, system layout, grouping → `block-beta` or `flowchart`
  - Flows, pipelines → `flowchart LR` or `flowchart TD`
  - Sequences, timelines → `sequenceDiagram` or `timeline`
  - Class/object relationships → `classDiagram`
- Preserve every entity, relationship, label, and grouping from the original ASCII art. Do not omit items.
- Use Mermaid `subgraph` for grouped/boxed sections when the original uses visual grouping.
- Keep the Mermaid block inside a fenced code block: ` ```mermaid ... ``` `.
- If the ASCII art is ambiguous, add a one-line comment inside the Mermaid block noting the assumption.
- Do not keep the original ASCII art alongside the Mermaid block; replace it entirely.

### Mermaid validation rule (Pretty-mermaid-skills)

Mermaid syntax errors break rendering. After generating any Mermaid code block, validate and render it using [Pretty-mermaid-skills](https://github.com/imxv/Pretty-mermaid-skills).

Setup (one-time, if not already installed):
```bash
npx skills add https://github.com/imxv/pretty-mermaid-skills --skill pretty-mermaid
```

Validation flow:
1. After converting ASCII art to Mermaid, save each Mermaid block as a temporary `.mmd` file.
2. Render with Pretty-mermaid-skills to verify syntax:
   ```bash
   node scripts/render.mjs --input <file>.mmd --output <file>.svg --theme tokyo-night
   ```
3. If rendering fails, fix the Mermaid syntax and re-render until it succeeds.
4. Once validated, embed the corrected Mermaid code back into the Markdown as a fenced ` ```mermaid ``` ` block.
5. Delete the temporary `.mmd` and `.svg` files.

> [AI RULE] Never embed Mermaid code that has not passed Pretty-mermaid-skills rendering. Broken diagrams are worse than no diagrams.

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
- **Multi-series or complex chart** → Mermaid `xychart-beta` block.
- **Pie/donut chart** → Mermaid `pie` block.
- **Sparkline or trend** → Markdown table with rows for each data point; optionally a Mermaid `xychart-beta` line chart.

Conversion guidelines:
- Extract every data label and its corresponding value from the ASCII chart.
- Preserve the original data ordering (e.g., descending by value, chronological).
- Include units if present in the original (e.g., `%`, `ms`, `MB`).
- For Mermaid charts, add a `title` matching the original chart's caption or heading context.
- Validate Mermaid chart blocks using the same Pretty-mermaid-skills flow as diagrams.

> [AI RULE] Every numeric value visible in the ASCII chart must appear in the converted output. Missing data points are conversion failures.

### Repository safety rule

- Never modify `README.md` in this repository. All changes must be confined to skill artifacts and generated MaraudersMapMD outputs only.

### Artifact hygiene and structure rule

- Always delete outdated or superseded MaraudersMapMD artifacts (old shard packs, stale indexes, obsolete JSON packs) so the project folder never accumulates unused files.
- Enforce a single, stable folder structure: `docs/MaraudersMap/<docId>/{ai-map.md,index.json,shards.json,.manifest.json,sections/*.md}`. The cross-doc index lives at docs/MaraudersMap/shards.db.
- Only one `<docId>` directory per document. `<docId>` corresponds to the rewritten file, not the original.
- If artifacts derived from the original source file exist, delete them immediately.
- Do not create or keep alternative artifact directories or extra copies outside the structure above.

### Final honest review rule

- Always end the workflow with a brief self-audit: re-check completed work against all rules and verify nothing is missing.
- If any gap is found, fix it before completing the task.

### Phase 1 — Baseline capture (before any rewriting)

Read the original source file directly. If existing MaraudersMapMD artifacts already exist for a previous rewritten version, read the AI Map (`ai-map.md`) for section summaries and the Search Index (`index.json`) for keywords/links. These help understand structure but do not replace reading the original. Do not rewrite anything yet. Do not generate any artifacts from the original file.

### Phase 2 — Create working copy

Create a `temp/` folder next to the original file. Copy the original into it as the working copy: `temp/temp_<filename>.rewritten.md`. Example: `guide.md` → `temp/temp_guide.rewritten.md`. All intermediate files go inside this `temp/` folder. All subsequent edits happen ONLY on this copy. Never modify the original.

### Phase 3 — Skeleton

Using the AI Map table as a guide, write a flat heading list in the working copy. Next to each heading note its one-line purpose. Fix heading levels so they descend without skips (single `#`, then `##`, then `###`). If the document is long, place a concise summary after the title.

### Phase 4 — Section-by-section rewrite

Open each Section Pack file (`sections/*.md`) one at a time, in order. For each section:
1. Check the Search Index entry for that section's keywords, links, and AI Hint Blocks.
2. Apply the canonical prompt rules: shorten paragraphs, convert dense prose to bullets, use tables for settings/options, keep code blocks unchanged.
3. Preserve every keyword, link, and AI Hint Block listed in the index entry.
4. Make the section self-contained. Use brief cross-references ("see Section X") instead of repeating content.

### Phase 5 — Verification and cleanup

Compare the finished output against the original Search Index:
1. Every keyword in the index must appear in the output.
2. Every AI Hint Block in the index must appear in the output.
3. Every link in the index must appear in the output.
4. Token count of the output should not significantly exceed the original (check AI Map's total).
5. Run the checklist below.

After verification passes:
1. Move `temp/temp_<filename>.rewritten.md` to the original file's directory as `<filename>.rewritten.md`.
2. Generate MaraudersMapMD artifacts from `<filename>.rewritten.md` only (never from the original).
3. Verify each `sections/*.md` shard matches its corresponding content in `<filename>.rewritten.md` (no drift).
4. Regenerate `shards.json` from the freshly generated shards and index.
5. Delete the `temp/` folder entirely.
6. Delete any stale or original-file-derived MaraudersMapMD artifacts. Only artifacts derived from the rewritten file may remain.
7. Confirm the project contains: the original source file (untouched), `<filename>.rewritten.md`, and one set of MaraudersMapMD artifacts under `docs/MaraudersMap/<docId>/`. No `temp/` folder, no `temp_` files, no original-derived artifacts.

### Sync rule — rewritten changes must update shards

If the rewritten document is edited at any time:
1. Re-run the MaraudersMapMD generation on `<filename>.rewritten.md`.
2. Replace the Section Pack and Search Index with the newly generated versions.
3. Regenerate `shards.json` from the updated shards and index.
4. If a cross-doc SQLite index exists (`shards.db`), re-ingest the updated doc: `python shards_db.py --ingest docs/MaraudersMap/<docId> --map-root docs/MaraudersMap`.
5. Do not continue work until shards, index, and `shards.json` exactly match the rewritten document.

## Checklist

After rewriting, verify every item below. Each maps to a rule in the canonical prompt.

- [ ] Heading hierarchy is correct (single `#` title, levels descend without skips)
- [ ] Concise summary present at the top for long documents
- [ ] Paragraphs are short (2–4 lines); dense prose converted to bullets
- [ ] Tables used for settings, options, or structured comparisons
- [ ] No hard line breaks inside paragraphs
- [ ] No extra blank lines inside lists
- [ ] Typos fixed; product names, command names, and identifiers preserved exactly
- [ ] AI Hint Blocks (`> [AI RULE]`, `> [AI DECISION]`, `> [AI TODO]`, `> [AI CONTEXT]`) used only where the source content warrants them
- [ ] All facts, constraints, and technical details from the source are present in the output
- [ ] Code blocks and inline code unchanged (except ASCII art converted per classification rules)
- [ ] Every ASCII visual block classified (data table / chart / diagram) per the decision tree
- [ ] All ASCII data tables converted to Markdown pipe tables with identical row/column counts
- [ ] All ASCII diagrams converted to appropriate Mermaid code blocks with no data loss
- [ ] All ASCII charts converted to Markdown tables or Mermaid chart blocks with every data point preserved
- [ ] Every Mermaid code block (diagrams and charts) validated via Pretty-mermaid-skills rendering (no syntax errors)
- [ ] Converted blocks include an HTML comment tracing origin (`<!-- Converted from ASCII art: ... -->`)
- [ ] Output language matches the source's dominant language
- [ ] Output is only the final Markdown — no commentary or preamble
