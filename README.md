# MaraudersMapMD Skill

AI agent skill for [MaraudersMapMD](https://github.com/mandarange/MaraudersMapMD) — the VS Code extension for AI-first Markdown workflows.

## What This Skill Does

`maraudersmapmd-skill` rewrites Markdown documents to maximize readability and scan-ability, following the MaraudersMapMD extension's formatting philosophy. It also enforces sharded Markdown access for fast lookup and keeps shards strictly synced with the rewritten document for accuracy.

The skill contains three parts:

1. **Canonical Prompt** — the verbatim prompt from the extension's `src/ai/aiService.ts` `buildReadabilityPrompt()`, copied without modification
2. **5-Phase Procedure** — an artifact-driven editorial flow (Baseline Capture → Working Copy → Skeleton → Section Rewrite → Verification & Cleanup)
3. **Verification Checklist** — items that confirm the canonical prompt rules were followed

## Sharded Markdown Workflow (AI Accuracy)

The skill assumes the MaraudersMapMD artifacts are available and uses them as the primary source for AI lookup:

1. **Section Pack** (`docs/MaraudersMap/<docId>/sections/*.md`) — primary source for fast retrieval
2. **Search Index** (`docs/MaraudersMap/<docId>/index.json`) — validation of keywords, links, and AI Hint Blocks
3. **AI Map** (`docs/MaraudersMap/<docId>/ai-map.md`) — section boundaries and summaries
4. **Rewritten full document** (`<filename>.rewritten.md`) — only for cross-section context

If the rewritten document changes, shards and index must be regenerated immediately so they match exactly.

## Quick Install (Recommended)

Humans make mistakes. We recommend letting the AI handle the installation for you.

Paste the prompt below into Cursor's chat and the AI will set it up for you:

```
Fetch the content from https://raw.githubusercontent.com/mandarange/MaraudersMapMD-skill/main/SKILL.md and save it as .cursor/rules/maraudersmapmd-skill.mdc in this project.
```

## Installation

### Cursor

```bash
mkdir -p .cursor/rules && curl -fsSL https://raw.githubusercontent.com/mandarange/MaraudersMapMD-skill/main/SKILL.md -o .cursor/rules/maraudersmapmd-skill.mdc
```

### Claude Code

```bash
mkdir -p .claude/skills && curl -fsSL https://raw.githubusercontent.com/mandarange/MaraudersMapMD-skill/main/SKILL.md -o .claude/skills/maraudersmapmd-skill.md
```

### Manual

Download [`SKILL.md`](./SKILL.md) from this repo and place it at:

| Tool | Path |
|------|------|
| Cursor | `.cursor/rules/maraudersmapmd-skill.mdc` |
| Claude Code (project) | `.claude/skills/maraudersmapmd-skill.md` |
| Claude Code (global) | `~/.claude/skills/maraudersmapmd-skill/SKILL.md` |

## Verify Installation

After installing, type the following in Cursor's chat:

```
Improve the readability of this document
```

If the skill is loaded correctly, the AI will follow the 5-phase procedure (Baseline → Working Copy → Skeleton → Section Rewrite → Verification) instead of doing a generic rewrite.

## Skill Contents

| File | Purpose |
|------|---------|
| [`SKILL.md`](./SKILL.md) | Skill definition — YAML frontmatter, canonical prompt, 5-phase procedure, checklist |
| `README.md` | This file |
| `LICENSE` | MIT license |

## When It Triggers

The skill activates when the user asks to:

- Improve readability of a Markdown document
- Rewrite a document for clarity or scanning
- Apply MaraudersMapMD formatting
- Make a document AI-readable or AI-friendly
- Polish a Markdown document editorially
- Use sharded Markdown for fast retrieval or keep shards synced with the rewritten document

## Related

- [MaraudersMapMD](https://github.com/mandarange/MaraudersMapMD) — The VS Code extension this skill is based on
- [Anthropic Skills Spec](https://github.com/anthropics/skills) — The skill format specification

## License

MIT
