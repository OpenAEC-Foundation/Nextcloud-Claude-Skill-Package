# DECISIONS

Architectural and process decisions with rationale. Each decision is numbered and immutable once recorded. New decisions may supersede old ones but old ones are never deleted.

---

## D-001: 7-Phase Research-First Methodology
**Date**: 2026-03-19
**Status**: ACTIVE
**Context**: Need a structured approach to build high-quality skills
**Decision**: Adopt the 7-phase methodology proven in the ERPNext Skill Package, Blender-Bonsai Skill Package, and Tauri 2 Skill Package
**Rationale**: ERPNext project successfully produced 28 domain skills, Blender-Bonsai produced 73 skills, Tauri 2 produced 27 skills with this approach. Research-first prevents hallucinated content.
**Reference**: https://github.com/OpenAEC-Foundation/ERPNext_Anthropic_Claude_Development_Skill_Package/blob/main/WAY_OF_WORK.md

## D-002: Single Technology Package
**Date**: 2026-03-19
**Status**: ACTIVE
**Context**: Nextcloud is one platform with PHP backend and TypeScript/Vue.js frontend
**Decision**: No per-technology separation needed. All skills share the `nextcloud-` prefix under a single `skills/source/` tree.
**Rationale**: Nextcloud is a single platform. PHP, TypeScript, and Vue.js are different layers of the same system, not separate technologies. Splitting into sub-packages would add complexity without benefit.

## D-003: English-Only Skills
**Date**: 2026-03-19
**Status**: ACTIVE
**Context**: Team works primarily in Dutch, skills target international audience
**Decision**: ALL skill content in English only
**Rationale**: Skills are instructions for Claude, not end-user documentation. Claude reads English and responds in any language. Bilingual skills double maintenance with zero functional benefit. Proven in ERPNext, Blender, and Tauri projects.

## D-004: Claude Code Agent Tool for Orchestration
**Date**: 2026-03-19
**Status**: ACTIVE
**Context**: Need to produce skills efficiently. Windows environment, no oa-cli available.
**Decision**: Use Claude Code Agent tool for parallel execution instead of oa-cli
**Rationale**: Windows environment does not support oa-cli (requires WSL/Linux). Claude Code Agent tool provides native parallelism within the Claude Code session. Simpler setup, no tmux/fcntl dependencies.

## D-005: MIT License
**Date**: 2026-03-19
**Status**: ACTIVE
**Context**: Need to choose open-source license
**Decision**: MIT License
**Rationale**: Most permissive, maximizes adoption. Consistent with OpenAEC Foundation philosophy.

## D-006: ROADMAP.md as Single Source of Truth
**Date**: 2026-03-19
**Status**: ACTIVE
**Context**: Need to track project status across multiple sessions and agents
**Decision**: ROADMAP.md is the ONLY place where project status is tracked
**Rationale**: Multiple status locations cause drift and confusion. Single source prevents "which is current?" questions. Proven in ERPNext, Blender, and Tauri projects.

## D-007: Nextcloud 28+ Only
**Date**: 2026-03-19
**Status**: ACTIVE
**Context**: Nextcloud evolves rapidly with annual major releases. Older versions have different APIs and patterns.
**Decision**: All skills target Nextcloud 28+ exclusively. No coverage of deprecated APIs from older versions.
**Rationale**: NC 28 introduced significant app framework changes including the migration to Vue 3, updated @nextcloud/* packages, and PHP 8.1+ requirement. Supporting older versions would dilute quality and create confusion. Skills covering migration may reference older patterns for context only.

## D-008: Merge Services into Architecture Skill
**Date**: 2026-03-19
**Status**: ACTIVE
**Context**: Phase 3 masterplan refinement — evaluating skill boundaries
**Decision**: Merge `nextcloud-syntax-services` into `nextcloud-core-architecture`. DI and service layer patterns are architectural, not syntax.
**Rationale**: Research §10 showed the service layer content is thin and belongs with the architecture overview. Standalone skill would be under 100 lines.

## D-009: Merge Frontend Data into Frontend Skill
**Date**: 2026-03-19
**Status**: ACTIVE
**Context**: Phase 3 masterplan refinement — evaluating skill boundaries
**Decision**: Merge `nextcloud-syntax-frontend-data` into `nextcloud-syntax-frontend`. Renamed combined skill covers the full frontend story.
**Rationale**: Research §7+§8 are tightly coupled: Vue components always use @nextcloud/axios, router, initial-state. Splitting creates artificial boundary.

## D-010: Add Authentication Skill
**Date**: 2026-03-19
**Status**: ACTIVE
**Context**: Phase 3 masterplan refinement — research revealed substantial auth content
**Decision**: Add `nextcloud-syntax-authentication` as new skill. Login Flow v2 (4-step protocol), app passwords, CSRF handling, brute force protection warrant dedicated coverage.
**Rationale**: Research §6 contains too much content for core-security (which is architectural). Authentication is a distinct API surface developers interact with directly.

## D-011: Merge Notifications into Collaboration Skill
**Date**: 2026-03-19
**Status**: ACTIVE
**Context**: Phase 3 masterplan refinement — evaluating skill boundaries
**Decision**: Merge `nextcloud-impl-notifications` into `nextcloud-impl-collaboration`. Combined scope fits within 500 lines.
**Rationale**: Research §13+§14 are complementary collaboration APIs. Notifications are almost always used alongside sharing and activity.

## D-012: Skip Phase 4 Topic Research
**Date**: 2026-03-19
**Status**: ACTIVE
**Context**: Phase 4 evaluation — the vooronderzoek from Phase 2 already covered all 19 topic areas
**Decision**: Skip Phase 4 (topic-specific research). The vooronderzoek is comprehensive enough for skill creation.
**Rationale**: The vooronderzoek (364 lines, 19 sections) covers all API surfaces at sufficient depth. Creating redundant per-skill research documents would add overhead without new information. This pattern was also used in the Tauri 2 package.
