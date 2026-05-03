# AGENTS.md

Repository-level guidance for coding agents working on this project.

## 1) Project Purpose

Build and maintain an AI-native conversational TTRPG product presence and assets:

- Product-facing web pages in `pages/`
- Business/supporting templates in `templates/`
- Market and strategy docs in root markdown files

Primary goal: keep outputs product-centric, execution-oriented, and ready for real development handoff.

## 2) Scope and Directory Map

- `pages/index.html`, `pages/style.css`: landing page
- `pages/product-brief.html`: printable brief page
- `templates/invoice.html`, `templates/proposal.html`: reusable business templates
- `ai_ttrpg_market_report.md`: market research source of truth
- `documents/progress-log.md`: durable cross-session project memory
- `documents/rules-data-sources.md`: upstream corpus policy, pinning, version honesty
- `documents/rules-retrieval-embedding-adr.md`: staged embedding/reranker decision record
- `README.md`: public repository overview
- `requirements.txt`: Python dependencies for story-pack validation/runtime (`jsonschema`)
- `rules_index/`: dual retrieval implementation (chunk ingest, FTS, entity store, routing)
- `eval/queries.yaml`: retrieval routing/query benchmark set
- `scripts/`: local verification/build/import utilities used in workflow
- `vendor/`: local upstream snapshots for validation only (do not commit by default)
- `build/`: generated local artifacts (indexes, manifests, debug outputs)
- `.cursor/rules/*.mdc`: hard constraints and content standards
- `.agents/skills/*/SKILL.md`: project-scoped reusable workflows

If directory names or structure change, update this file in the same PR.

## 3) Default Workflow (Mandatory)

For any non-trivial request, follow this sequence:

1. Explore current files and constraints first
2. Propose a short plan or step list
3. Implement in small, reviewable changes
4. Verify output (rendering, links, formatting, consistency)
5. Summarize what changed and next actions

Do not jump directly to large edits without inspecting current files.

## 4) Skill Trigger Rules

Use installed skills proactively when relevant:

- `brainstorming`: before ambiguous feature/content direction work
- `writing-plans`: when work spans multiple files or phases
- `executing-plans`: when a written plan exists and should be followed
- `dispatching-parallel-agents`: for independent parallel subtasks
- `systematic-debugging`: for errors, regressions, or unclear failures
- `test-driven-development`: for logic-heavy code changes with testable behavior
- `verification-before-completion`: before declaring task done
- `requesting-code-review` and `receiving-code-review`: during review loops
- `story-pack-spec`: when defining story-pack schema or runtime content fields
- `release-checklist`: before publishing or milestone handoff

If a workflow repeats 2+ times, convert it into a reusable skill or template.

## 5) Editing and Content Rules

- Prefer product language over personal-brand language on public pages
- Keep copy concise and specific; avoid hype claims without evidence
- Keep HTML/CSS simple and static-first unless dynamic behavior is required
- Preserve reusable placeholders in templates (invoice/proposal fields)
- Do not commit private notes or local transcript files
- Do not commit local `vendor/` snapshots or generated `build/` artifacts unless explicitly requested

## 6) Verification Checklist

Before completion, verify:

- HTML structure is valid and page renders without broken sections
- Internal paths are correct (especially in `pages/`)
- Contact links and repo links are intentional
- Text changes are consistent with product positioning
- No accidental sensitive data was added
- Repository structure references match actual folders (especially `pages/`)
- `vendor/` and generated `build/` artifacts are not accidentally staged

## 7) Definition of Done

A task is done only when:

- Requested files are updated and internally consistent
- Quick verification is performed
- Summary includes changed files and any required follow-up actions

## 8) Maintenance Rule

Keep this file short and practical. Add only rules that change agent behavior.
When the same mistake happens twice, update this file with a concrete rule.

## 9) Session Continuity Rule

At the start of substantive work, read `documents/progress-log.md`.
At the end of substantive work, append a concise update to that log.
