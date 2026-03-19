# Lessons Learned

Observations and findings captured during skill package development.

---

## L-001: Nextcloud is a Multi-Layer Platform

- **Date**: 2026-03-19
- **Context**: Nextcloud combines PHP backend, TypeScript/Vue.js frontend, OCS REST API, WebDAV, and server administration in one platform.
- **Finding**: Skills must be organized by API surface (OCS, DAV, app framework) rather than by language. A single feature like file sharing spans PHP controllers, OCS endpoints, DAV operations, and Vue.js components. The skill structure must reflect these API boundaries, not language boundaries.

---

## L-002: NC 28+ Marks a Significant Frontend Shift

- **Date**: 2026-03-19
- **Context**: Nextcloud 28 introduced Vue 3 migration and updated @nextcloud/* packages.
- **Finding**: Frontend code from NC 27 and earlier uses Vue 2 patterns that are incompatible with NC 28+. Skills MUST target Vue 3 patterns and the latest @nextcloud/vue library. This is why D-007 restricts coverage to NC 28+ only — mixing Vue 2 and Vue 3 patterns in skills would cause confusion and broken code.

---

## L-003: Batch Execution with 3 Agents is Optimal

- **Date**: 2026-03-19
- **Context**: Phase 5 skill creation used 8 batches of 3 agents each to create 24 skills.
- **Finding**: 3 agents per batch is the sweet spot for Claude Code Agent tool. More agents increase context window pressure and risk of interference. Fewer agents waste parallelism potential. The 8-batch execution (24 skills) completed efficiently with no file conflicts because batch planning ensured separated file scopes.

---

## L-004: Vooronderzoek Can Replace Topic Research

- **Date**: 2026-03-19
- **Context**: Phase 4 was skipped because the Phase 2 vooronderzoek (364 lines, 19 sections) already covered all skill topics.
- **Finding**: For single-technology packages with a clear API surface, a comprehensive vooronderzoek (covering all API areas, version differences, anti-patterns) can eliminate the need for separate per-skill topic research. This saves a full phase without quality loss, as proven by the 24 skills passing structural validation. The decision to skip should be recorded in DECISIONS.md (D-012).

---

## L-005: YAML Frontmatter Format Must Be Checked During Validation

- **Date**: 2026-03-19
- **Context**: Phase 6 validation checked structural aspects (file existence, line counts, reference files) but did not verify YAML frontmatter format compliance.
- **Finding**: The YAML description field format (folded block scalar `>` vs quoted strings, "Use when..." opening, "Prevents..." warning, "Keywords:" section) must be explicitly included in the Phase 6 validation checklist. In this project, all 24 skills passed structural validation but failed the YAML format standard. The compliance audit caught this — validation should catch it first.

---

## L-006: Governance Files Need Cross-Phase Updates

- **Date**: 2026-03-19
- **Context**: DECISIONS.md had only 7 entries despite 5 refinement decisions being made in Phase 3, and SOURCES.md was never updated after initial setup.
- **Finding**: Governance file updates (DECISIONS.md, SOURCES.md, LESSONS.md) must be treated as a mandatory step in EVERY phase completion, not just logged in ROADMAP.md. The Document Sync Protocol (P-006) exists for this reason — it must be enforced, not just documented.
