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

If the skill is loaded correctly, the AI will follow the 5-phase procedure (Baseline → Working Copy → Skeleton → Section Rewrite → Verification) instead of doing a generic rewrite.

## Skill Contents

| File | Purpose |
|------|---------|
| [`SKILL.md`](./SKILL.md) | Skill definition — YAML frontmatter, canonical prompt, 5-phase procedure, checklist |
| `render_html_to_png.py` | Local Playwright-based HTML → PNG capture helper used by diagram/chart conversion flow |
| `README.md` | This file |
| `LICENSE` | MIT license |

## HTML to PNG Capture Helper

If your workflow generates HTML diagrams/charts but does not produce PNG output, run:

```bash
python3 render_html_to_png.py --html temp/diagram-example.html --output docs/MaraudersMap/SKILL/images/diagram-example.png --markdown-file guide.rewritten_v2.md --alt "architecture overview" --source-description "auth flow ASCII diagram" --viewport-width 1200 --viewport-height 900 --wait-ms 400
```

This command uses `npx playwright screenshot` under the hood and auto-installs the browser runtime when missing.

Recommended one-time setup on each machine:

```bash
npx playwright install chromium
```

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
