<!-- Section from: /Users/choi-dong-won/Desktop/devs/MaraudersMapMD-skill/README.md | Lines: 15-25 -->

## Sharded Markdown Workflow (AI Accuracy)

The skill assumes the MaraudersMapMD artifacts are available and uses them as the primary source for AI lookup:

1. **Section Pack** (`docs/MaraudersMap/<docId>/sections/*.md`) — primary source for fast retrieval
2. **Search Index** (`docs/MaraudersMap/<docId>/index.json`) — validation of keywords, links, and AI Hint Blocks
3. **AI Map** (`docs/MaraudersMap/<docId>/ai-map.md`) — section boundaries and summaries
4. **Rewritten full document** (`<filename>.rewritten.md`) — only for cross-section context

If the rewritten document changes, shards and index must be regenerated immediately so they match exactly.
