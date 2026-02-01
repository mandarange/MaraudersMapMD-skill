# MaraudersMapMD Skill

AI agent skill for [MaraudersMapMD](https://github.com/mandarange/MaraudersMapMD) — the VS Code extension for AI-first Markdown workflows.

## What This Skill Does

`maraudersmapmd-readability-flow` rewrites Markdown documents to maximize readability and scan-ability, following the MaraudersMapMD extension's formatting philosophy.

The skill contains three parts:

1. **Canonical Prompt** — the verbatim prompt from the extension's `src/ai/aiService.ts` `buildReadabilityPrompt()`, copied without modification
2. **4-Phase Procedure** — an artifact-driven editorial flow (Baseline Capture → Skeleton → Section Rewrite → Verification & Cleanup)
3. **Verification Checklist** — items that confirm the canonical prompt rules were followed

## Quick Install

Copy the prompt below and paste it into your AI coding assistant (Claude Code, Cursor, Windsurf, etc.):

```
Install the MaraudersMapMD readability skill into this project:
1. Create .claude/skills/ directory if it doesn't exist
2. Download SKILL.md from https://raw.githubusercontent.com/mandarange/MaraudersMapMD-skill/main/SKILL.md
3. Save it as .claude/skills/maraudersmapmd-readability-flow.md
```

Or run this one-liner in your terminal:

```bash
mkdir -p .claude/skills && curl -fsSL https://raw.githubusercontent.com/mandarange/MaraudersMapMD-skill/main/SKILL.md -o .claude/skills/maraudersmapmd-readability-flow.md
```

## Installation

### Method 1: Project skill (recommended)

Install into a single project. The skill is available only in that project's context.

```bash
cd your-project
mkdir -p .claude/skills
curl -fsSL https://raw.githubusercontent.com/mandarange/MaraudersMapMD-skill/main/SKILL.md \
  -o .claude/skills/maraudersmapmd-readability-flow.md
```

### Method 2: Personal skill (all projects)

Install once, available across every project on your machine.

```bash
mkdir -p ~/.claude/skills/maraudersmapmd-readability-flow
curl -fsSL https://raw.githubusercontent.com/mandarange/MaraudersMapMD-skill/main/SKILL.md \
  -o ~/.claude/skills/maraudersmapmd-readability-flow/SKILL.md
```

### Method 3: Git clone + symlink

Keep the skill repo for updates via `git pull`.

```bash
# Clone once (anywhere you like)
git clone https://github.com/mandarange/MaraudersMapMD-skill.git

# Symlink into your project
mkdir -p .claude/skills
ln -s "$(pwd)/MaraudersMapMD-skill/SKILL.md" .claude/skills/maraudersmapmd-readability-flow.md
```

To update later:

```bash
cd MaraudersMapMD-skill && git pull
```

### Method 4: Manual copy

Download [`SKILL.md`](./SKILL.md) from this repo and place it at either location:

| Scope | Path |
|-------|------|
| Project only | `.claude/skills/maraudersmapmd-readability-flow.md` |
| All projects | `~/.claude/skills/maraudersmapmd-readability-flow/SKILL.md` |

## Verify Installation

After installing, open your AI coding assistant and type:

```
이 문서의 가독성을 개선해줘
```

or

```
Apply MaraudersMapMD readability flow to this document
```

If the skill is loaded correctly, the agent will follow the 4-phase procedure (Baseline → Skeleton → Section Rewrite → Verification) instead of doing a generic rewrite.

## Skill Contents

| File | Purpose |
|------|---------|
| [`SKILL.md`](./SKILL.md) | Skill definition — YAML frontmatter, canonical prompt, 4-phase procedure, checklist |
| `README.md` | This file |
| `LICENSE` | MIT license |

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
