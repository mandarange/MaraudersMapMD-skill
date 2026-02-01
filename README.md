# MaraudersMapMD Skill

AI agent skill for [MaraudersMapMD](https://github.com/mandarange/MaraudersMapMD) — the VS Code extension for AI-first Markdown workflows.

## What This Skill Does

`maraudersmapmd-readability-flow` rewrites Markdown documents to maximize readability and scan-ability, following the MaraudersMapMD extension's formatting philosophy.

The skill contains three parts:

1. **Canonical Prompt** — the verbatim prompt from the extension's `src/ai/aiService.ts` `buildReadabilityPrompt()`, copied without modification
2. **4-Phase Procedure** — an artifact-driven editorial flow (Baseline Capture → Skeleton → Section Rewrite → Verification & Cleanup)
3. **Verification Checklist** — items that confirm the canonical prompt rules were followed

## Quick Install

Cursor 채팅창에 아래 프롬프트를 붙여넣으면 AI가 알아서 설치합니다:

```
https://raw.githubusercontent.com/mandarange/MaraudersMapMD-skill/main/SKILL.md 내용을 fetch해서 이 프로젝트의 .cursor/rules/maraudersmapmd-readability-flow.mdc 파일로 저장해줘
```

## Installation

### Cursor

```bash
mkdir -p .cursor/rules && curl -fsSL https://raw.githubusercontent.com/mandarange/MaraudersMapMD-skill/main/SKILL.md -o .cursor/rules/maraudersmapmd-readability-flow.mdc
```

### Claude Code

```bash
mkdir -p .claude/skills && curl -fsSL https://raw.githubusercontent.com/mandarange/MaraudersMapMD-skill/main/SKILL.md -o .claude/skills/maraudersmapmd-readability-flow.md
```

### Manual

Download [`SKILL.md`](./SKILL.md) from this repo and place it at:

| Tool | Path |
|------|------|
| Cursor | `.cursor/rules/maraudersmapmd-readability-flow.mdc` |
| Claude Code (project) | `.claude/skills/maraudersmapmd-readability-flow.md` |
| Claude Code (global) | `~/.claude/skills/maraudersmapmd-readability-flow/SKILL.md` |

## Verify Installation

설치 후 Cursor 채팅창에서 아래처럼 입력하면 됩니다:

```
이 문서의 가독성을 개선해줘
```

스킬이 정상 로드되면 AI가 4-phase 절차(Baseline → Skeleton → Section Rewrite → Verification)를 따라 리라이트합니다.

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
