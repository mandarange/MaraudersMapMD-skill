# MaraudersMapMD Skill

AI agent skill for [MaraudersMapMD](https://github.com/mandarange/MaraudersMapMD) — the VS Code extension for AI-first Markdown workflows.

## What This Skill Does

`maraudersmapmd-readability-flow` rewrites Markdown documents to maximize readability and scan-ability, following the MaraudersMapMD extension's formatting philosophy.

When activated, the skill instructs the AI agent to:

- Restructure headings into a clean hierarchy
- Break dense paragraphs into short, scannable blocks
- Convert inline lists to bullet points and structured data to tables
- Apply AI Hint Blocks (`> [AI RULE]`, `> [AI DECISION]`, `> [AI TODO]`, `> [AI CONTEXT]`) for critical content
- Preserve all facts, code blocks, and technical details exactly
- Remove fluff and redundancy while keeping the original language

The prompt is sourced from the extension's `src/ai/aiService.ts` `buildReadabilityPrompt()` function.

## Skill Contents

| File | Purpose |
|------|---------|
| [`SKILL.md`](./SKILL.md) | Skill definition — YAML frontmatter + rewrite instructions + verification checklist |
| `README.md` | This file |
| `LICENSE` | MIT license |

## Installation

### Claude Code (CLI)

Copy `SKILL.md` into your project's `.claude/skills/` directory:

```bash
mkdir -p .claude/skills
cp SKILL.md .claude/skills/maraudersmapmd-readability-flow.md
```

Or clone the entire repo and symlink:

```bash
git clone https://github.com/mandarange/MaraudersMapMD-skill.git
ln -s "$(pwd)/MaraudersMapMD-skill/SKILL.md" .claude/skills/maraudersmapmd-readability-flow.md
```

### Manual Use

You can also copy the prompt text from the "Core Instructions" section of `SKILL.md` directly into any AI chat interface.

## When It Triggers

The skill activates when the user asks to:

- Improve readability of a Markdown document
- Rewrite a document for clarity or scanning
- Apply MaraudersMapMD formatting
- Make a document AI-readable or AI-friendly
- Polish a Markdown document editorially

## Related

- [MaraudersMapMD](https://github.com/mandarange/MaraudersMapMD) — The VS Code extension this skill is based on
- [Anthropic Skills Spec](https://github.com/anthropics/skills) — The skill format specification

## License

MIT
