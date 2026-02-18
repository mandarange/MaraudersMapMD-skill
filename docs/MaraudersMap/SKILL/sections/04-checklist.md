<!-- Section from: /Users/choi-dong-won/Desktop/devs/MaraudersMapMD-skill/SKILL.md | Lines: 664-692 -->

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
- [ ] Every embedded image path in Markdown is correct and relative to the rewritten Markdown file
- [ ] No `temp/diagram-*.html` files remain after completion
- [ ] Converted blocks include an HTML comment tracing origin (`<!-- Converted from ASCII art: ... -->`)
- [ ] Output language matches the source's dominant language
- [ ] No translated narrative text appears unless translation was explicitly requested by the user
- [ ] Output is only the final Markdown — no commentary or preamble
