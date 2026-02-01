---
name: maraudersmapmd-readability-flow
description: Rewrite Markdown documents to maximize readability and scan-ability using the MaraudersMapMD readability flow. Use this skill when the user asks to improve, rewrite, or optimize a Markdown document for readability, or when asked to apply MaraudersMapMD readability formatting.
metadata:
  version: "3.0.0"
  source: "MaraudersMapMD src/ai/aiService.ts → buildReadabilityPrompt()"
  tags:
    - markdown
    - readability
    - formatting
    - maraudersmapmd
---

# MaraudersMapMD Readability Flow

## When to Use

- User asks to improve readability, rewrite for clarity, or optimize a Markdown document for scanning
- User asks to apply MaraudersMapMD formatting or make a document AI-readable
- User provides a Markdown document and asks for editorial polish

## Core Instructions (Verbatim)

Create a copy of the Markdown document, then edit the copy for MaraudersMapMD. Apply our format and feature rules to maximize readability and AI consumption.

Rules:
- Keep the final language the same as the original (do not translate).
- Preserve meaning, constraints, and technical facts. Remove fluff only.
- Use clean heading hierarchy so Section Pack splits are meaningful.
- Keep Markdown semantics correct (headings, lists, tables, links, code fences).
- Use AI Hint Blocks for critical content:
  > [AI RULE] must-not-violate constraints
  > [AI DECISION] key decisions and rationale
  > [AI TODO] concrete follow-up actions
  > [AI CONTEXT] essential background for AI
- Keep code blocks and inline code unchanged.
- Prefer short paragraphs, bullet lists, and tables for settings/options.
- Output ONLY the revised Markdown.

Readability guidance:
- Add a concise summary at the top for long docs.
- Prefer short paragraphs (2-4 lines) and bullet lists for dense text.
- Use consistent numbering for sections and sub-sections.
- Use tables for settings, options, and comparisons.
- Use bold for key terms and short callouts; use inline code for identifiers.
- Keep blockquotes for important notes or constraints (avoid overuse).
- Spacing: leave a single blank line between sections; no extra blank lines inside a list.
- Line breaks: avoid manual hard breaks inside paragraphs; use Markdown lists/headings to separate ideas.
- Typos: fix spelling/grammar and normalize terminology; keep product names and commands unchanged.

Icons (emoji) usage:
- Use emojis sparingly and consistently (1 per heading max).
- Only use when it improves scanning (e.g., ✅ for done, ⚠️ for warnings, 🔒 for constraints).
- Do not decorate every line; avoid repeated icons in lists.

Separators (horizontal rules):
- Use --- only between major sections or before a new major part.
- Avoid consecutive rules or rules inside lists.
- Do not use rules as visual noise; prefer headings and spacing.

Markdown syntax for readability:
- Headings: use # to ### for hierarchy; avoid skipping levels.
- Lists: use '-' for bullets; use '1.' for ordered steps.
- Tables: use for structured options/configs; keep columns short.
- Code: use fenced blocks with language; inline code for identifiers.
- Quotes: use > for critical notes; keep them short.

How to express visual emphasis in MaraudersMapMD:
- Heading levels (H1-H3) are color-coded in preview; use them to create visual hierarchy.
- Links are colored; convert raw URLs to proper Markdown links.
- Code blocks and inline code are styled; use them for commands, keys, or file names.
- Blockquotes are styled with a colored border; use for critical notes.
- AI Hint Blocks render with distinct styling; use them for must-read content.

File name: ${fileName}
Path: ${filePath}

## Checklist (Verification Only)

### A. Readability

- [ ] Heading hierarchy correct — single `#`, no level skips
- [ ] Summary present for long documents (>100 lines)
- [ ] Paragraphs short (2–4 lines max)
- [ ] Dense paragraphs converted to bullets where it improves scanning
- [ ] Tables used for settings, options, or structured comparisons

### B. Formatting / Semantics

- [ ] Markdown syntax preserved (headings, lists, tables, links, code)
- [ ] Inline code used for identifiers, commands, paths, config keys
- [ ] Code blocks and inline code unchanged
- [ ] Blockquotes reserved for critical notes or AI Hint Blocks only

### C. Visual Emphasis

- [ ] Headings leverage preview color hierarchy
- [ ] Links descriptive — not bare URLs
- [ ] AI Hint Blocks used only where source content matches the semantic

### D. Spacing / Line Breaks / Typos

- [ ] One blank line between sections
- [ ] No extra blank lines inside lists
- [ ] No hard line breaks inside paragraphs
- [ ] Typos fixed; product names, command names, identifiers preserved exactly

### E. Long Document Flow

- [ ] Outline added at top (restating existing sections, not new content)
- [ ] Section-by-section rewrite for self-contained scanning
- [ ] All keywords and constraints from source accounted for
- [ ] Final consistency pass completed

### F. Completeness

- [ ] Every fact, constraint, and detail from source present in output
- [ ] No information fabricated beyond structural reorganization
- [ ] Output language matches source dominant language
- [ ] Output is Markdown only — no preamble, no commentary
