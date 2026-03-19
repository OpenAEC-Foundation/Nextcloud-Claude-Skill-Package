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
