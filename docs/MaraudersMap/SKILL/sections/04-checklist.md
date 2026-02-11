<!-- Section from: /Users/choi-dong-won/Desktop/devs/MaraudersMapMD-skill/SKILL.md | Lines: 274-296 -->

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
