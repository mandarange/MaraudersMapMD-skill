<!-- Section from: /Users/choi-dong-won/Desktop/devs/MaraudersMapMD-skill/README.md | Lines: 5-14 -->

## What This Skill Does

`maraudersmapmd-skill` rewrites Markdown documents to maximize readability and scan-ability, following the MaraudersMapMD extension's formatting philosophy. It also enforces sharded Markdown access for fast lookup and keeps shards strictly synced with the rewritten document for accuracy.

The skill contains three parts:

1. **Canonical Prompt** — the verbatim prompt from the extension's `src/ai/aiService.ts` `buildReadabilityPrompt()`, copied without modification
2. **5-Phase Procedure** — an artifact-driven editorial flow (Baseline Capture → Working Copy → Skeleton → Section Rewrite → Verification & Cleanup)
3. **Verification Checklist** — items that confirm the canonical prompt rules were followed
