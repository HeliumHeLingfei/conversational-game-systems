---
name: release-checklist
description: Run a lightweight release readiness checklist for this repository. Use before pushing major content, publishing pages, or handing off a milestone.
---

# Release Checklist

Use this skill to standardize pre-release checks for this project.

## Scope

- Product-facing pages in `pages/`
- Business templates in `templates/`
- Core docs in repository root

## Checklist

1. **Content consistency**
   - Product positioning is consistent across landing page and brief.
   - Public links and contact information are intentional.

2. **Structure and paths**
   - GitHub Pages paths are valid for `/pages`.
   - Relative stylesheet and internal links resolve correctly.

3. **Template integrity**
   - `invoice.html` and `proposal.html` retain editable placeholders.
   - No accidental hardcoded client-sensitive values.

4. **Repository hygiene**
   - No private/transcript files staged for commit.
   - Commit message scope matches actual changes.

5. **Handoff summary**
   - Report changed files, risks, and recommended next step.

## Output Format

Return:

- `Status`: Ready / Needs fixes
- `Checked`: bullet list of completed checks
- `Issues`: blocking and non-blocking findings
- `Next`: specific action items
