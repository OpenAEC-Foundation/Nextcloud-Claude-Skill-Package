# REQUIREMENTS

## What This Skill Package Must Achieve

### Primary Goal
Enable Claude to write correct, version-aware Nextcloud code for PHP backend, TypeScript/Vue.js frontend, and server administration — without hallucinating APIs or using deprecated patterns.

### What Claude Should Do After Loading Skills
1. Recognize Nextcloud context from user requests
2. Select the correct skill(s) automatically based on the request
3. Write correct PHP, TypeScript, and Vue.js code for the specified operation
4. Use the correct OCS/DAV/REST API endpoints with proper authentication
5. Avoid known anti-patterns and common AI mistakes
6. Follow best practices documented in the skill references

### Quality Guarantees
| Guarantee | Description |
|-----------|-------------|
| Version-correct | Code MUST target Nextcloud 28+ |
| API-accurate | All method signatures and endpoints verified against official docs |
| Multi-language | App development skills show PHP backend AND TypeScript/Vue.js frontend |
| Anti-pattern-free | Known mistakes are explicitly documented and avoided |
| Deterministic | Skills use ALWAYS/NEVER language, not suggestions |
| Self-contained | Each skill works independently without requiring other skills |

---

## Per-Area Requirements

### 1. OCS API
| Requirement | Detail |
|-------------|--------|
| Core pattern | OCS REST API endpoint structure, authentication methods |
| Endpoints | User provisioning, shares, notifications, app config, capabilities |
| Authentication | Basic auth, app passwords, OAuth2 tokens |
| Response format | OCS response envelope (ocs.meta, ocs.data), XML vs JSON |
| Critical | Correct endpoint versioning (/ocs/v2.php/ vs /ocs/v1.php/) |

### 2. WebDAV
| Requirement | Detail |
|-------------|--------|
| Core pattern | DAV endpoint structure for files, calendars, contacts |
| File operations | PROPFIND, GET, PUT, MKCOL, MOVE, COPY, DELETE |
| Properties | Custom DAV properties, extended attributes |
| Chunked upload | Chunked upload protocol for large files |
| Critical | Correct DAV paths and namespace URIs |

### 3. App Framework
| Requirement | Detail |
|-------------|--------|
| Structure | App directory layout, info.xml, appinfo/, lib/, src/ |
| Controllers | OCS controllers, page controllers, API controllers |
| Database | Migrations, entities, mappers (ORM), raw queries |
| Services | Service layer patterns, dependency injection |
| Frontend | Vue.js app registration, router, store patterns |
| Critical | Correct namespace conventions and autoloading |

### 4. Vue.js Frontend
| Requirement | Detail |
|-------------|--------|
| Components | @nextcloud/vue component library usage |
| Data fetching | @nextcloud/axios, OCS/DAV client usage from frontend |
| Routing | Vue Router integration with Nextcloud |
| State | Vuex/Pinia store patterns for Nextcloud apps |
| Critical | Correct import paths for @nextcloud/* packages |

### 5. Server Administration
| Requirement | Detail |
|-------------|--------|
| OCC commands | occ command syntax, custom command development |
| Configuration | config.php settings, environment variables |
| Background jobs | Cron, webcron, AJAX, custom background jobs |
| Logging | ILogger usage, log levels, structured logging |
| Critical | Correct occ command patterns and config.php keys |

### 6. Authentication & Security
| Requirement | Detail |
|-------------|--------|
| Auth flows | Login flow v2, app passwords, OAuth2 |
| CSRF | CSRF token handling in controllers and API calls |
| Middleware | Rate limiting, CORS, brute force protection |
| Encryption | Server-side encryption, end-to-end encryption basics |
| Critical | Correct CSRF protection patterns in custom apps |

### 7. File Handling
| Requirement | Detail |
|-------------|--------|
| Node API | INode, File, Folder interfaces in PHP |
| Storage | Storage backends, external storage configuration |
| Hooks/Events | File event listeners (BeforeNodeCreated, etc.) |
| Versions | File versioning API |
| Critical | Correct IRootFolder/IUserFolder usage patterns |

### 8. Collaboration
| Requirement | Detail |
|-------------|--------|
| Shares | Public shares, internal shares, federated shares |
| Talk API | Talk/Spreed API for messaging and video |
| Activity | Activity stream API and custom activity providers |
| Notifications | Notification API, push notifications |
| Critical | Share permission bitmask values and combinations |

---

## Critical Requirements (apply to ALL skills)

- All PHP code MUST work with Nextcloud 28+ server
- All TypeScript/Vue.js MUST work with @nextcloud/* packages for NC 28+
- OCS API examples MUST include correct endpoint paths and response formats
- App development skills MUST show both PHP backend and Vue.js frontend sides (D-008)
- Code examples MUST be verified against official documentation
- All DAV paths and property namespaces MUST be accurate

---

## Structural Requirements

### Skill Format
- SKILL.md < 500 lines (heavy content in references/)
- YAML frontmatter with name and description (including trigger words)
- English-only content
- Deterministic language (ALWAYS/NEVER, imperative)

### Skill Categories
| Category | Purpose | Must Include |
|----------|---------|--------------|
| syntax/ | How to write it | API endpoints, method signatures, code patterns, version notes |
| impl/ | How to build it | Decision trees, workflows, step-by-step |
| errors/ | How to handle failures | Error patterns, diagnostics, recovery |
| core/ | Cross-cutting | API overview, architecture, concepts |
| agents/ | Orchestration | Validation checklists, auto-detection |

---

## Research Requirements (before creating any skill)

1. Official documentation MUST be consulted and referenced
2. Source code MUST be checked for accuracy when docs are ambiguous
3. Anti-patterns MUST be identified from real issues (GitHub issues, forums)
4. Code examples MUST be verified (not hallucinated)
5. Version accuracy MUST be confirmed via WebFetch (D-012)

---

## Non-Requirements (explicitly out of scope)

- No Nextcloud versions before 28 (except migration notes where critical)
- No Docker/Snap deployment deep-dives (skills cover Nextcloud code, not infrastructure)
- No end-user UI tutorials (skills cover code APIs, not clicking through settings)
- No specific client app development (desktop/mobile sync clients are separate projects)
- No third-party app reviews or comparisons
