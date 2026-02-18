# MaraudersMapMD Skill

AI agent skill for [MaraudersMapMD](https://github.com/mandarange/MaraudersMapMD) — the VS Code extension for AI-first Markdown workflows.

## What This Skill Does

`maraudersmapmd-skill` rewrites Markdown documents to maximize readability and scan-ability, following the MaraudersMapMD extension's formatting philosophy. It uses a SQLite-first retrieval workflow for fast lookup and falls back to rewritten/original Markdown on cache miss.

The skill contains three parts:

1. **Canonical Prompt** — the verbatim prompt from the extension's `src/ai/aiService.ts` `buildReadabilityPrompt()`, copied without modification
2. **5-Phase Procedure** — an editorial flow (Baseline Capture → Working Copy → Skeleton → Rewrite & SQLite Ingest → Verification & Cleanup)
3. **Verification Checklist** — items that confirm the canonical prompt rules were followed

## SQLite-First Retrieval Workflow (AI Accuracy)

The skill uses SQLite as the primary retrieval source:

1. **SQLite Index** (`docs/MaraudersMap/shards.db`) — primary source for keyword/BM25 retrieval
2. **Rewritten full document** (`<base>.rewritten_vN.md`) — first fallback on cache miss
3. **Original source document** — final fallback for fact verification

If the rewritten document changes, re-ingest it into SQLite immediately so retrieval stays consistent.

Optional debug artifacts (`sections/*.md`, `index.json`, `ai-map.md`, `shards.json`) may exist but are not required for normal retrieval.

### Diagram/Chart Image Reliability

The skill enforces a strict capture lifecycle for ASCII-to-image conversion:

- Always regenerate PNG in the current run (do not rely on old files)
- Verify PNG exists on disk and has non-zero size before inserting Markdown image tags
- Keep `temp/diagram-*.html` until PNG proof + Markdown insertion are complete
- If PNG is missing (including manual deletion), regenerate it before completion

Rewritten output uses explicit versioned filenames:
- First rewrite: `<filename>.rewritten_v1.md`
- Next revision: `<filename>.rewritten_v2.md` (not `rewritten.rewritten.md`)

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

### Cursor (Claude-style folder, team standard)

```bash
mkdir -p .cursor/skills/maraudersmapmd-skill && curl -fsSL https://raw.githubusercontent.com/mandarange/MaraudersMapMD-skill/main/SKILL.md -o .cursor/skills/maraudersmapmd-skill/SKILL.md
```

### Claude Code

```bash
mkdir -p .claude/skills/maraudersmapmd-skill && curl -fsSL https://raw.githubusercontent.com/mandarange/MaraudersMapMD-skill/main/SKILL.md -o .claude/skills/maraudersmapmd-skill/SKILL.md
```

### Manual

Download [`SKILL.md`](./SKILL.md) from this repo and place it at:

| Tool | Path |
|------|------|
| Cursor | `.cursor/rules/maraudersmapmd-skill.mdc` |
| Cursor (Claude-style) | `.cursor/skills/maraudersmapmd-skill/SKILL.md` |
| Claude Code (project) | `.claude/skills/maraudersmapmd-skill/SKILL.md` |
| Claude Code (global) | `~/.claude/skills/maraudersmapmd-skill/SKILL.md` |

## Compatibility Notes

This skill follows the Anthropic Agent Skills folder convention (`<skill-name>/SKILL.md`) so one artifact can be reused across Claude Code and Cursor workflows.

- **Claude Code**: Use the folder path above directly.
- **Cursor**: Prefer `.cursor/skills/<skill-name>/SKILL.md` for the same folder convention. Keep `.cursor/rules/*.mdc` only for backward compatibility.

## Verify Installation

After installing, type the following in Cursor's chat:

```
Improve the readability of this document
```

If the skill is loaded correctly, the AI will follow the 5-phase procedure (Baseline → Working Copy → Skeleton → Rewrite & SQLite Ingest → Verification) instead of doing a generic rewrite.

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
- Use SQLite-first retrieval with cache-miss fallback to rewritten/original documents

## Related

- [MaraudersMapMD](https://github.com/mandarange/MaraudersMapMD) — The VS Code extension this skill is based on
- [Anthropic Skills Spec](https://github.com/anthropics/skills) — The skill format specification

## License

MIT
