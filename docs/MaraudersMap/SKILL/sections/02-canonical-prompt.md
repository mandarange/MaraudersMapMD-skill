<!-- Section from: /Users/choi-dong-won/Desktop/devs/MaraudersMapMD-skill/SKILL.md | Lines: 15-47 -->

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
  - **Diagrams** (flowcharts, ER, architecture) → HTML rendering → screenshot PNG image.
  - **Charts** (bar charts, histograms, sparklines) → Markdown tables (simple) or HTML rendering → screenshot PNG image (complex).
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
