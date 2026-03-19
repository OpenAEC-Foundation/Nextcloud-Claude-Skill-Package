# Nextcloud Claude Skill Package

![Claude Code Ready](https://img.shields.io/badge/Claude_Code-Ready-blue?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJDNi40OCAyIDIgNi40OCAyIDEyczQuNDggMTAgMTAgMTAgMTAtNC40OCAxMC0xMFMxNy41MiAyIDEyIDJ6IiBmaWxsPSIjZmZmIi8+PC9zdmc+)
![Nextcloud 28+](https://img.shields.io/badge/Nextcloud-28+-0082C9?style=flat-square&logo=nextcloud&logoColor=white)
![PHP + TypeScript + Vue.js](https://img.shields.io/badge/PHP_+_TypeScript_+_Vue.js-Full_Stack-orange?style=flat-square)
![Skills](https://img.shields.io/badge/Skills-24-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

**Deterministic Claude AI skills for Nextcloud development — PHP backend, TypeScript/Vue.js frontend, OCS API, WebDAV, and app framework coverage.**

Built on the [Agent Skills](https://agentskills.org) open standard.

---

## Why This Exists

Without skills, Claude generates outdated or incorrect Nextcloud patterns:

```php
// Wrong — deprecated pattern, missing proper DI and return types
class MyController extends Controller {
    public function index() {
        return new JSONResponse(['data' => 'hello']);
    }
}
```

With this skill package, Claude produces correct NC 28+ code:

```php
// Correct — proper attribute routing, typed responses, DI
use OCA\MyApp\Service\MyService;
use OCP\AppFramework\Http\Attribute\NoAdminRequired;
use OCP\AppFramework\Http\JSONResponse;
use OCP\AppFramework\OCSController;
use OCP\IRequest;

class MyController extends OCSController {
    public function __construct(
        string $appName,
        IRequest $request,
        private MyService $service,
    ) {
        parent::__construct($appName, $request);
    }

    #[NoAdminRequired]
    public function index(): JSONResponse {
        return new JSONResponse($this->service->findAll());
    }
}
```

---

## Skills (24)

See [INDEX.md](INDEX.md) for the complete catalog with links.

| Category | Count | Coverage |
|----------|-------|----------|
| **core/** | 3 | Architecture, configuration, security model |
| **syntax/** | 8 | OCS API, WebDAV, controllers, database, events, auth, frontend, file API |
| **impl/** | 7 | App scaffold, full-stack dev, background jobs, occ, collaboration, testing, file ops |
| **errors/** | 4 | API errors, app errors, database errors, frontend errors |
| **agents/** | 2 | Code review validator, app scaffolder |

## Installation

### Claude Code

```bash
# Option 1: Clone the full package
git clone https://github.com/OpenAEC-Foundation/Nextcloud-Claude-Skill-Package.git
cp -r Nextcloud-Claude-Skill-Package/skills/source/ ~/.claude/skills/nextcloud/

# Option 2: Add as git submodule
git submodule add https://github.com/OpenAEC-Foundation/Nextcloud-Claude-Skill-Package.git .claude/skills/nextcloud
```

### Claude.ai (Web)

Upload individual SKILL.md files as project knowledge.

## Version Compatibility

| Technology | Versions | Notes |
|------------|----------|-------|
| Nextcloud | **28+** | Primary target |
| PHP | 8.1+ | Minimum PHP version for NC 28 |
| TypeScript | 5.x | Frontend type safety |
| Vue.js | 3.x | Frontend framework (NC 28+) |
| Node.js | 18+ | Build tooling |

## Methodology

This package is developed using the **7-phase research-first methodology**, proven across multiple skill packages:

1. **Setup + Raw Masterplan** — Project structure and governance files
2. **Deep Research** — Comprehensive source analysis of Nextcloud documentation, source code, and community resources
3. **Masterplan Refinement** — Skill inventory refinement based on research findings
4. **Topic-Specific Research** — Deep-dive per skill topic
5. **Skill Creation** — Deterministic skill files following Agent Skills standard
6. **Validation** — Correctness, completeness, and consistency checks
7. **Publication** — GitHub release and documentation

## Documentation

| Document | Purpose |
|----------|---------|
| [ROADMAP.md](ROADMAP.md) | Project status (single source of truth) |
| [REQUIREMENTS.md](REQUIREMENTS.md) | Quality guarantees and per-area requirements |
| [DECISIONS.md](DECISIONS.md) | Architectural decisions with rationale |
| [SOURCES.md](SOURCES.md) | Official reference URLs and verification rules |
| [WAY_OF_WORK.md](WAY_OF_WORK.md) | 7-phase development methodology |
| [LESSONS.md](LESSONS.md) | Lessons learned during development |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

## Related Projects

| Project | Description |
|---------|-------------|
| [ERPNext Skill Package](https://github.com/OpenAEC-Foundation/ERPNext_Anthropic_Claude_Development_Skill_Package) | 28 skills for ERPNext/Frappe development |
| [Blender-Bonsai Skill Package](https://github.com/OpenAEC-Foundation/Blender-Bonsai-ifcOpenshell-Sverchok-Claude-Skill-Package) | 73 skills for Blender, Bonsai, IfcOpenShell & Sverchok |
| [Tauri 2 Skill Package](https://github.com/OpenAEC-Foundation/Tauri-2-Claude-Skill-Package) | 27 skills for Tauri 2 desktop development |
| [OpenAEC Foundation](https://github.com/OpenAEC-Foundation) | Parent organization |

## License

[MIT](LICENSE)

---

Part of the [OpenAEC Foundation](https://github.com/OpenAEC-Foundation) ecosystem.
