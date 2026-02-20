---
name: maraudersmapmd-skill
description: Rewrite Markdown documents to maximize readability and scan-ability and keep sharded Markdown packs in sync for fast lookup. Use this skill when the user asks to improve, rewrite, or optimize a Markdown document for readability, when asked to apply MaraudersMapMD readability formatting, or when sharded Markdown access is required.
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
- Never translate user-authored prose, headings, labels, or explanatory sentences into another language.
- If the source is Korean, output must remain Korean except for literals that are already in English (for example code, API names, CLI flags, product names, or quoted identifiers).
- Preserve all facts, constraints, and technical details. Do not add new information.
- Keep Markdown semantics correct (headings, lists, tables, code fences, links).
- Use the project's AI hint block format where it helps: "> [AI RULE]", "> [AI DECISION]", "> [AI TODO]", "> [AI CONTEXT]".
- Prefer short paragraphs, clear headings, and consistent numbering.
- Use tables for settings, options, or structured comparisons when helpful.
- Keep code blocks and inline code exactly as-is.
- Convert ASCII art visuals to the appropriate visual format (see "ASCII visual content classification" below):
  - **Data tables** drawn with ASCII borders → proper Markdown pipe tables.
  - **Diagrams / Charts** (flowcharts, ER, architecture, bar charts) → Leave ASCII art exactly as-is. Notify the user to run the `Marauders_ASCII2Chart_Skill` or prompt the other skill if supported by the environment.
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
- All sharding, indexing, and artifact generation targets the rewritten version file (`<base>.rewritten_v{N}.md`) exclusively.
- The original exists solely as a reference for fact-checking; it must never be modified, copied into artifact directories, or have artifacts derived from it.

Artifact paths (generated from the rewritten file only):
- Rewritten Markdown (single active version): `<base>.rewritten_v{N}.md`

> [AI RULE] `<docId>` is derived from the normalized base name, not the versioned filename (e.g. `guide.rewritten_v1.md` and `guide.rewritten_v2.md` both use docId `guide`). Use one stable `<docId>` per logical document. Never create version-suffixed docIds like `guide_v2`.

### Language lock rule (highest priority)

- The rewritten output must preserve the source language exactly; translation is prohibited unless the user explicitly asks for translation.
- If source content is Korean, keep Korean narrative text, headings, and list items in Korean.
- Keep existing English technical literals as-is (commands, code, identifiers, API names, file paths, env vars).
- If mixed-language content exists, preserve each segment's original language unless the user requests normalization.
- If a generated section accidentally changes language, treat it as a blocking error and rewrite that section before finalizing.

> [AI RULE] Language drift (for example Korean source rewritten in English) is a hard failure. Fix before completion.

### SQLite-first access rule (always-on)

- For fast lookup and reading, use the SQLite index (`docs/MaraudersMap/shards.db`) as the primary retrieval source.
- Section pack files (`sections/*.md`, `index.json`, `ai-map.md`) are optional implementation artifacts, not the primary retrieval path. Legacy `shards.json` retrieval paths are disabled.
- On cache miss or low-confidence retrieval from SQLite, fall back to the rewritten Markdown file first, then the original source file only when needed for fact verification.
- If artifacts derived from the original file are found, delete them immediately.

### Retrieval order for accuracy

When answering or extracting facts, use this order to minimize drift:
1. SQLite index (`docs/MaraudersMap/shards.db`) via keyword/BM25/regex.
2. Rewritten full document (`<base>.rewritten_v{N}.md`) for local context recovery.
3. Original source document only when cache miss persists or rewritten content is incomplete.

### Retrieval routing

92: Choose the fastest retrieval path based on the query scope:
93: 
94: 1. **SQLite keyword**: Exact sections (`python shards_search.py --db docs/MaraudersMap/shards.db --keyword "<kw>" --doc "<docId>"`)
95: 2. **SQLite FTS5**: Ranked results (`python shards_search.py --db docs/MaraudersMap/shards.db --query "<text>" --doc "<docId>" --top 5`)
96: 3. **Fallback**: Read `<base>.rewritten_v{N}.md` directly.
97: 
98: > [AI RULE] Always query SQLite first. Only fall back when SQLite returns no relevant hits. When rewriting multiple documents, you MUST use parallel tool execution to simultaneously process them. Sequential processing of independent documents is a performance bug.

### Accuracy guardrails

- Do not infer facts that are not present in SQLite hits, rewritten Markdown, or the original source.
- If SQLite hits disagree with rewritten Markdown, treat rewritten Markdown as source of truth and re-ingest the document.
- If rewritten Markdown is ambiguous or incomplete, validate against the original source before answering.

### SQLite cache-aside rule (Python-first)

- Use SQLite (`docs/MaraudersMap/shards.db`) as the default retrieval cache.
- On every rewritten update, re-ingest the doc into SQLite before answering queries.
- Query SQLite first. On miss/low-confidence, fall back to rewritten Markdown; if still unresolved, fall back to original source.
- Use `python shards_db.py --init --map-root docs/MaraudersMap` once per project.
- Use `python shards_db.py --ingest docs/MaraudersMap/<docId> --map-root docs/MaraudersMap` after each rewrite update.
- Use `python shards_search.py --db docs/MaraudersMap/shards.db --doc "<docId>" --query "<text>" --top 5` for per-doc relevance retrieval.
- Use `python shards_search.py --db docs/MaraudersMap/shards.db --query "<text>" --top 5` for cross-doc retrieval.
- Optional: `sections/*.md`, `index.json`, and `ai-map.md` may exist as debug artifacts, but retrieval must not depend on them. Legacy `shards.json` retrieval paths are disabled.

### ASCII diagram handling rule

If the source Markdown contains complex ASCII art diagrams (flowcharts, sequences, ER layouts) or visual charts composed of characters, **DO NOT** attempt to convert them into images or HTML.

- Keep the ASCII art block exactly as-is wrapped in a code fence.
- A separate dedicated skill named `Marauders_ASCII2Chart_Skill` will handle all visual conversion into premium Mermaid.js images.
- Point the user to this skill if they want to render the text diagrams.

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
- **Multi-series, complex chart, Pie/donut chart, Sparklines** → Leave ASCII art exactly as-is. Point the user to `Marauders_ASCII2Chart_Skill` for rendering.

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
- Enforce a single, stable folder structure: `docs/MaraudersMap/<docId>/images/*.png` for visuals, plus cross-doc SQLite index at `docs/MaraudersMap/shards.db`.
- Store diagram render sources only under `docs/MaraudersMap/<docId>/render-html/` using versioned names (`<diagram-name>.render_v{N}.html`).
- One stable `<docId>` directory per logical document (base name). New rewritten versions must overwrite artifacts in the same `docs/MaraudersMap/<docId>/` directory, not create new versioned docId directories.
- If artifacts derived from the original source file exist, delete them immediately.
- Do not create or keep alternative artifact directories or extra copies outside the structure above.
- Delete orphaned images in `docs/MaraudersMap/<docId>/images/` that are not referenced by the rewritten Markdown, but only after all converted ASCII blocks have been embedded and verified. Do not run orphan cleanup during capture.
- Never delete PNG files that are referenced by the active rewritten Markdown.
- For each diagram, keep exactly one active render HTML version file (highest `render_v{N}`) and remove older versions after successful capture.
- Never store diagram render HTML files in `temp/`; use `docs/MaraudersMap/<docId>/render-html/` only.
- Never delete the current highest-version render HTML file for a diagram.

### Final honest review rule

- Always end the workflow with a brief self-audit: re-check completed work against all rules and verify nothing is missing.
- If any gap is found, fix it before completing the task.

### Phase 1 — Baseline capture (before any rewriting)

Read the original source file directly. If a rewritten version already exists, read that rewritten file as immediate context. Do not rewrite anything yet. Do not generate any artifacts from the original file.

### Phase 2 — Create working copy

Determine the base name and next version before creating any file:

- **Base name**: Strip any `.rewritten_v{n}` suffix from the source filename. `guide.md` → base `guide`. `guide.rewritten_v1.md` → base `guide`. Never include `.rewritten_v{n}` in the base.
- **Next version**: If no prior rewritten file exists, use `v1`. If `<base>.rewritten_v{n}.md` already exists, use `v{n+1}`.
- **Working copy path**: `temp/temp_<base>.rewritten_v{N}.md` where `N` is the next version.
- **Filename normalization gate (required)**: Before writing output, normalize the target name to `<base>.rewritten_v{N}.md`. Remove any chained segments such as `.rewritten.rewritten`, `.rewritten_v1.rewritten_v2`, or repeated `.rewritten` tokens. These names are invalid and must be corrected before saving.

Examples: `guide.md` (first run) → `temp/temp_guide.rewritten_v1.md`. `guide.rewritten_v1.md` (re-run) → `temp/temp_guide.rewritten_v2.md`. `guide.rewritten.rewritten.md` (invalid source name) still normalizes to base `guide` and must output `temp/temp_guide.rewritten_v{N}.md`.

All intermediate files go inside `temp/`. All edits happen ONLY on the working copy. Never modify the source.

### Phase 3 — Skeleton

Using the source and rewritten context, write a flat heading list in the working copy. Next to each heading note its one-line purpose. Fix heading levels so they descend without skips (single `#`, then `##`, then `###`). If the document is long, place a concise summary after the title.

### Phase 4 — Rewrite and SQLite ingest

1. Rewrite the working copy using the canonical prompt rules: shorten paragraphs, convert dense prose to bullets, use tables for settings/options, keep code blocks unchanged.
2. Convert ASCII visuals and generate PNG files according to the diagram/chart rules.
3. Move the finalized working copy to `<base>.rewritten_v{N}.md`.
4. Ingest the document into SQLite: `python shards_db.py --ingest docs/MaraudersMap/<docId> --map-root docs/MaraudersMap`.

Parallel rewrite guidance: documents are independent and may be processed in parallel. Within one document, keep rewrite -> image capture -> ingest order sequential.

### Phase 5 — Verification and cleanup

Compare the finished output against the rewritten file and SQLite retrieval results:
1. SQLite query by keyword returns expected section(s) for the document.
2. SQLite BM25 query returns relevant results for the document.
3. Every embedded image path exists on disk and resolves correctly.
4. On simulated cache miss (query with no hit), fallback to rewritten file works.
5. Run the checklist below.

After verification passes:
1. Ensure `<base>.rewritten_v{N}.md` is present and normalized.
2. Ensure SQLite is up to date for this doc (`python shards_db.py --ingest ...` completed without error).
3. If processing multiple docs, run per-doc ingest in parallel, then run `python shards_db.py --status --map-root docs/MaraudersMap` once.
4. Delete transient files under `temp/` (working-copy artifacts only); do not delete `docs/MaraudersMap/<docId>/render-html/`.
5. Delete stale artifacts: remove original-file-derived outputs and stale version-suffixed docId directories for the same base (for example `guide_v2`).
6. Confirm the project contains: original source (untouched), exactly one active rewritten file (`<base>.rewritten_v{N}.md`), SQLite DB (`docs/MaraudersMap/shards.db`), and images under `docs/MaraudersMap/<docId>/images/*.png`.
7. Confirm there are no invalid rewritten filenames in the working set (for example `*.rewritten.rewritten.md` or `*.rewritten_v*.rewritten_v*.md`). If found, rename to the normalized `<base>.rewritten_v{N}.md` form before completion.

### Sync rule — rewritten changes must update SQLite

If the rewritten document is edited at any time:
1. Re-run the MaraudersMapMD generation on the current rewritten version file (`<base>.rewritten_v{N}.md`).
2. Re-ingest the updated doc into SQLite: `python shards_db.py --ingest docs/MaraudersMap/<docId> --map-root docs/MaraudersMap`.
3. Verify with a SQLite query that expected content is retrievable.
4. Do not continue work until SQLite results match the rewritten document.

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
- [ ] All ASCII diagrams converted to HTML, rendered as screenshot PNG images, and embedded with `![...]()` syntax — no data loss
- [ ] All ASCII charts converted to Markdown tables (simple) or HTML screenshot PNG images (complex) with every data point preserved
- [ ] Every diagram and chart PNG image visually verified after screenshot capture (labels readable, layout correct, no overlaps)
- [ ] Diagram images saved to `docs/MaraudersMap/<docId>/images/` with descriptive kebab-case filenames
- [ ] Diagram image filenames are deterministic across reruns for the same input
- [ ] No orphaned image files exist in `docs/MaraudersMap/<docId>/images/` (every PNG is referenced)
- [ ] Every PNG referenced by Markdown exists on local disk and is not removed during cleanup
- [ ] Filesystem proof was executed for each generated PNG before Markdown insertion (existence + non-zero size)
- [ ] Every embedded image path in Markdown is correct and relative to the rewritten Markdown file
- [ ] Diagram render HTML files use versioned names (`<diagram-name>.render_v{N}.html`) under `docs/MaraudersMap/<docId>/render-html/`
- [ ] For each diagram, only the latest render HTML version file remains (SSOT)
- [ ] `<docId>` is stable per logical document base (no version-suffixed duplicate docId directories)
- [ ] Only one active rewritten Markdown exists for the document (`<base>.rewritten_v{N}.md`); older rewritten versions are cleaned up
- [ ] Converted blocks include an HTML comment tracing origin (`<!-- Converted from ASCII art: ... -->`)
- [ ] Regression guard passes: missing `campaign-lifecycle.png` under `FORM_EVENT_INTRODUCTION` is regenerated in-run and linked with one valid image tag
- [ ] Output language matches the source's dominant language
- [ ] No translated narrative text appears unless translation was explicitly requested by the user
- [ ] Rewritten filename is normalized to `<base>.rewritten_v{N}.md` (no `rewritten.rewritten` or chained rewritten suffixes)
- [ ] Output is only the final Markdown — no commentary or preamble
