# Approved Sources Registry

All skills in this package MUST be verified against these approved sources. No other sources are authoritative.

## Official Documentation

| Source | URL | Purpose |
|--------|-----|---------|
| Nextcloud Documentation | https://docs.nextcloud.com | Primary reference for all Nextcloud content |
| Nextcloud Developer Manual | https://docs.nextcloud.com/server/latest/developer_manual/ | App development, API reference, architecture |
| Nextcloud Admin Manual | https://docs.nextcloud.com/server/latest/admin_manual/ | Server configuration, administration, occ commands |
| Nextcloud User Manual | https://docs.nextcloud.com/server/latest/user_manual/ | User-facing features (reference only) |

## Source Code

| Source | URL | Purpose |
|--------|-----|---------|
| Nextcloud Server | https://github.com/nextcloud/server | Core server source code, OCS controllers, DAV |
| Nextcloud Organization | https://github.com/nextcloud | All official repositories |
| Nextcloud Vue Components | https://github.com/nextcloud-libraries/nextcloud-vue | @nextcloud/vue component library |
| Nextcloud Frontend Libraries | https://github.com/nextcloud-libraries | @nextcloud/axios, @nextcloud/router, etc. |
| Nextcloud App Tutorial | https://github.com/nextcloud/app-tutorial | Official app development tutorial |

## App Store & Ecosystem

| Source | URL | Purpose |
|--------|-----|---------|
| Nextcloud App Store | https://apps.nextcloud.com | App store, app metadata, developer portal |
| Nextcloud App Store Docs | https://nextcloudappstore.readthedocs.io | App store API, publishing requirements |

## API References

| Source | URL | Purpose |
|--------|-----|---------|
| OCS API Documentation | https://docs.nextcloud.com/server/latest/developer_manual/client_apis/OCS/index.html | OCS REST API endpoints |
| WebDAV API Documentation | https://docs.nextcloud.com/server/latest/developer_manual/client_apis/WebDAV/index.html | DAV file operations |
| Login Flow v2 | https://docs.nextcloud.com/server/latest/developer_manual/client_apis/LoginFlow/index.html | Authentication flow |

## Package/Library Docs

| Source | URL | Purpose |
|--------|-----|---------|
| @nextcloud/vue (npm) | https://www.npmjs.com/package/@nextcloud/vue | Vue component library |
| @nextcloud/axios (npm) | https://www.npmjs.com/package/@nextcloud/axios | HTTP client wrapper |
| @nextcloud/router (npm) | https://www.npmjs.com/package/@nextcloud/router | URL generation |
| @nextcloud/dialogs (npm) | https://www.npmjs.com/package/@nextcloud/dialogs | Dialog components |
| @nextcloud/files (npm) | https://www.npmjs.com/package/@nextcloud/files | File handling utilities |

## Community (for Anti-Pattern Research)

| Source | URL | Purpose |
|--------|-----|---------|
| GitHub Issues (Server) | https://github.com/nextcloud/server/issues | Real-world error patterns |
| GitHub Discussions | https://github.com/nextcloud/server/discussions | Q&A, patterns |
| Nextcloud Forum | https://help.nextcloud.com | Community help, common problems |
| Nextcloud Dev Forum | https://help.nextcloud.com/c/dev/11 | Developer-specific discussions |

## Claude / Anthropic (Skill Development Platform)

| Source | URL | Purpose |
|--------|-----|---------|
| Agent Skills Standard | https://agentskills.io | Open standard |
| Agent Skills Spec | https://github.com/agentskills/agentskills | Specification |
| Agent Skills Best Practices | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices | Authoring guide |

## OpenAEC Foundation

| Source | URL | Purpose |
|--------|-----|---------|
| ERPNext Skill Package | https://github.com/OpenAEC-Foundation/ERPNext_Anthropic_Claude_Development_Skill_Package | Methodology template |
| Blender Skill Package | https://github.com/OpenAEC-Foundation/Blender-Bonsai-ifcOpenshell-Sverchok-Claude-Skill-Package | Proven 73-skill package |
| Tauri 2 Skill Package | https://github.com/OpenAEC-Foundation/Tauri-2-Claude-Skill-Package | Proven 27-skill package |

## Source Verification Rules

1. **Primary sources ONLY** — Official docs, official repos, official npm docs.
2. **NEVER trust random blog posts** — Even popular ones may be outdated or wrong for NC 28+.
3. **Verify code against official docs** — Every code snippet in a skill MUST match current API.
4. **Note when source was last verified** — Track in the table below.
5. **Cross-reference if docs are sparse** — When official docs lack detail, verify against source code in the server repo.
6. **Check @nextcloud/* package versions** — Frontend packages update frequently. ALWAYS verify import paths and method signatures against latest published versions.

## Last Verified

| Technology | Date | Action | Notes |
|------------|------|--------|-------|
| Nextcloud | 2026-03-19 | Initial setup | All URLs pending verification |
