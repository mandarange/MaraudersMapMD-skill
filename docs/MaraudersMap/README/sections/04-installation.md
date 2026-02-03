<!-- Section from: /Users/choi-dong-won/Desktop/devs/MaraudersMapMD-skill/README.md | Lines: 36-59 -->

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
