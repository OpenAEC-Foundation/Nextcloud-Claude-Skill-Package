# WAY OF WORK

## Overview
This project follows the 7-phase research-first methodology proven in the ERPNext Skill Package (28 skills), Blender-Bonsai Skill Package (73 skills), and Tauri 2 Skill Package (27 skills). The methodology ensures deterministic, high-quality skills by mandating deep research before any skill creation.

**Core principle**: You cannot create deterministic skills for something you don't deeply understand.

## The 7 Phases

### Phase 1: Raw Masterplan
- Define project scope and Nextcloud coverage areas
- Create preliminary skill inventory (estimate, not final)
- Set up repository structure and core files
- Establish protocols (CLAUDE.md)
- Output: `docs/masterplan/nextcloud-masterplan.md`, CLAUDE.md, ROADMAP.md

### Phase 2: Deep Research (Vooronderzoek)
- One comprehensive research document for Nextcloud
- Cover: OCS API surface, WebDAV, app framework architecture, Vue.js frontend patterns, authentication, file handling, collaboration APIs, server administration
- Minimum 2000 words
- Must include: version matrix, API overview, code examples, error patterns
- Output: `docs/research/vooronderzoek-nextcloud.md`

### Phase 3: Masterplan Refinement
- Review research against preliminary skill inventory
- Add, merge, or remove skills based on findings
- Define dependencies between skills
- Write ready-to-use prompts for each skill (so agents can execute directly)
- Output: updated `docs/masterplan/nextcloud-masterplan.md`, updated ROADMAP.md

### Phase 4: Topic-Specific Research
- Before each skill: focused research document
- Only the information that specific skill needs
- Verify against official documentation using WebFetch (D-012)
- Collect and validate code examples
- Identify anti-patterns from real issues
- Output: `docs/research/topic-research/{skill-name}-research.md`

### Phase 5: Skill Creation
- Transform research into deterministic skills
- Follow skill structure strictly (see below)
- Execute in batches of 3 agents via Claude Code Agent tool
- Quality gate after every batch
- Output: `skills/source/nextcloud-{category}/{skill-name}/`

### Phase 6: Validation
- Structural validation (frontmatter, line count, references)
- Content validation (deterministic language, English-only, multi-language coverage)
- Cross-reference validation (skills reference each other correctly)
- Functional validation (test with real Claude Code questions)
- Output: validation report

### Phase 7: Publication
- Update INDEX.md with complete skill catalog
- Update README.md with installation instructions
- Final ROADMAP.md update to 100%
- Release tag on GitHub

## Skill Structure

### Directory Layout
```
skill-name/
├── SKILL.md              # Main file, < 500 lines
└── references/
    ├── methods.md        # Complete API signatures (PHP + TypeScript)
    ├── examples.md       # Working code examples (both languages)
    └── anti-patterns.md  # What NOT to do
```

### SKILL.md Format
```yaml
---
name: nextcloud-{category}-{topic}
description: "Deterministic [description]. Use this skill when Claude needs to [trigger scenario]..."
---
```

Content sections (in order):
1. Quick Reference (critical warnings, decision trees)
2. Essential Patterns (with PHP AND TypeScript/Vue.js code where applicable)
3. Common Operations (code snippets)
4. Reference Links (to references/ files)

### Naming Convention
- `nextcloud-{category}-{topic}`
- Prefix: `nextcloud-` (single technology, single prefix)
- Categories: syntax, impl, errors, core, agents
- Examples: `nextcloud-syntax-ocs-api`, `nextcloud-impl-app-dev`, `nextcloud-errors-dav`, `nextcloud-core-architecture`

## Content Standards

### DO:
- Use imperative, deterministic language: "ALWAYS use X when Y", "NEVER do X because Y"
- Verify all code against official documentation
- Show BOTH PHP and TypeScript/Vue.js sides for app development patterns (D-008)
- Provide working examples that follow Nextcloud coding standards
- Document anti-patterns with explanations
- Use decision trees for common choices
- Keep SKILL.md under 500 lines
- Include correct OCS/DAV endpoint paths with authentication headers

### DON'T:
- Use vague language: "you might consider", "it's often good practice"
- Make assumptions about API behavior
- Copy from outdated pre-NC28 sources
- Show only one side of the stack (PHP without Vue.js or vice versa) for full-stack patterns
- Include speculative features or unreleased APIs
- Write skills in any language other than English
- Use training data without WebFetch verification (D-012)

## Orchestration Model

### Delegation-First Architecture
- Main session = ORCHESTRATOR (coordinates, validates, never does work)
- Workers = agents spawned via Claude Code Agent tool
- Results collected automatically when agents complete

### Batch Execution
- 3 agents per batch (optimal for Claude Code Agent tool)
- Each agent writes to its own unique directory (no file conflicts)
- Quality gate between batches
- Orchestrator does QA after each batch before starting next

### Quality Gate Checklist (after every batch):
1. YAML frontmatter present and valid?
2. Line count < 500?
3. English-only?
4. Deterministic language?
5. PHP + TypeScript/Vue.js coverage (for full-stack skills)?
6. Sources traceable to SOURCES.md?
7. All referenced files exist?

## Version Control Discipline
- Commit after EVERY completed phase
- Commit message format: `Phase X.Y: [action] [subject]`
- ROADMAP.md updated with every commit
- NEVER track status in multiple places (ROADMAP.md is the ONLY source)

## Session Recovery Protocol
When starting a new session or recovering from interruption:
1. Read ROADMAP.md (what's done, what's next)
2. Read LESSONS.md (recent discoveries)
3. Check git log (last commits)
4. Identify where we left off
5. Confirm with user before continuing

## Key Lesson: English-Only Skills
Skills are instructions FOR Claude, not for end users. Claude reads English and responds in ANY language the user speaks. Creating bilingual skills doubles maintenance with zero functional benefit. ALL skills MUST be in English.

## Reference Projects
- ERPNext Skill Package: https://github.com/OpenAEC-Foundation/ERPNext_Anthropic_Claude_Development_Skill_Package
- Blender-Bonsai Skill Package: https://github.com/OpenAEC-Foundation/Blender-Bonsai-ifcOpenshell-Sverchok-Claude-Skill-Package
- Tauri 2 Skill Package: https://github.com/OpenAEC-Foundation/Tauri-2-Claude-Skill-Package
