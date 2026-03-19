# Nextcloud Skill Package — Definitive Masterplan

## Status

Phase 3 complete. Finalized from raw masterplan after vooronderzoek review.
Date: 2026-03-19

---

## Decisions Made During Refinement

| # | Decision | Rationale |
|---|----------|-----------|
| R-01 | **Merged** `nextcloud-syntax-services` into `nextcloud-core-architecture` | DI and service layer patterns are architectural, not syntax. Research §10 shows the content is thin and belongs with architecture overview. |
| R-02 | **Merged** `nextcloud-syntax-frontend-data` into `nextcloud-syntax-vue-components` → renamed to `nextcloud-syntax-frontend` | Research §7+§8 are tightly coupled: Vue components always use @nextcloud/axios, router, initial-state. One skill covers the full frontend story. |
| R-03 | **Added** `nextcloud-syntax-authentication` | Research §6 reveals substantial content: Login Flow v2 (4-step protocol), app passwords, CSRF handling, brute force protection. Too much for core-security (which is architectural). |
| R-04 | **Merged** `nextcloud-impl-notifications` into `nextcloud-impl-sharing` → renamed to `nextcloud-impl-collaboration` | Research §13+§14 are complementary collaboration APIs. Combined scope fits within 500 lines. |

**Result**: 25 raw skills → **24 definitive skills** (2 merges, 1 addition, 0 removals).

---

## Definitive Skill Inventory (24 skills)

### nextcloud-core/ (3 skills)

| Name | Scope | Key APIs | Research Input | Complexity | Dependencies |
|------|-------|----------|----------------|------------|-------------|
| `nextcloud-core-architecture` | Platform architecture; PHP backend + Vue.js frontend layers; app lifecycle (IBootstrap register/boot); DI container; service layer patterns; key interfaces; auto-wiring | App, IBootstrap, IRegistrationContext, IServerContainer, auto-wiring | §1, §10, §11 | M | None |
| `nextcloud-core-config` | config.php reference; IConfig interface; occ config commands; app config; user config; environment variables; caching; proxy; mail | config.php keys, IConfig, IAppConfig, occ config:system/app | §16 | L | None |
| `nextcloud-core-security` | Security model overview; middleware chain; CSP; rate limiting architecture; brute force protection; encryption; security attributes overview | SecurityMiddleware, ContentSecurityPolicy, Middleware chain | §4 (middleware), §6 (security model) | M | None |

### nextcloud-syntax/ (8 skills)

| Name | Scope | Key APIs | Research Input | Complexity | Dependencies |
|------|-------|----------|----------------|------------|-------------|
| `nextcloud-syntax-ocs-api` | OCS REST API endpoints; v1 vs v2; authentication; response envelope; XML vs JSON; capabilities; user provisioning; share API endpoints; user status | /ocs/v2.php/*, OCSController, DataResponse | §2 | L | core-architecture |
| `nextcloud-syntax-webdav` | DAV file operations; PROPFIND/GET/PUT/MKCOL/MOVE/COPY/DELETE; properties; namespaces (d:/oc:/nc:); chunked upload v2; special headers | /remote.php/dav/*, Depth, X-OC-MTime, OC-Checksum | §3 | L | core-architecture |
| `nextcloud-syntax-controllers` | Controller types (Controller, OCSController); routes.php; attribute-based routing; parameter extraction; security attributes; response types; middleware | Controller, OCSController, #[NoAdminRequired], routes.php | §4 | M | core-architecture |
| `nextcloud-syntax-database` | Migrations; entities; QBMapper; query builder; TTransactional; column types; Oracle/Galera constraints; index management | ISchemaWrapper, Entity, QBMapper, IQueryBuilder, TTransactional | §5 | L | core-architecture |
| `nextcloud-syntax-events` | IEventDispatcher; typed events; IEventListener; event registration; Before/After pattern; built-in events catalog; custom events; frontend event-bus | IEventDispatcher, Event, IEventListener, @nextcloud/event-bus | §9, §8 (event-bus) | M | core-architecture |
| `nextcloud-syntax-frontend` | @nextcloud/vue components; @nextcloud/axios; @nextcloud/router; @nextcloud/initial-state; @nextcloud/dialogs; @nextcloud/files; Webpack config; CSS variables; dark mode | NcButton, NcAppContent, generateUrl, loadState, axios | §7, §8 | L | core-architecture |
| `nextcloud-syntax-authentication` | Login Flow v2 protocol; app passwords; CSRF token handling; rate limiting attributes; brute force protection; security attributes on controllers; OAuth2 | Login Flow v2, #[UserRateLimit], #[BruteForceProtection], CSRF | §6 | M | core-security |
| `nextcloud-syntax-file-api` | Node API; IRootFolder/IUserFolder; File/Folder interfaces; getById; storage wrappers; file events; versioning; trash | IRootFolder, IUserFolder, File, Folder, NotFoundException | §12 | M | core-architecture |

### nextcloud-impl/ (7 skills)

| Name | Scope | Key APIs | Research Input | Complexity | Dependencies |
|------|-------|----------|----------------|------------|-------------|
| `nextcloud-impl-app-scaffold` | App directory structure; info.xml manifest; Application.php bootstrap; namespace conventions; autoloading; app generator | info.xml, Application, IBootstrap, OCA namespace | §11 | M | core-architecture |
| `nextcloud-impl-app-development` | Full-stack workflow; controller + service + mapper + Vue.js; API endpoint creation; frontend integration; initial state bridge | Full stack: PHP → Vue.js | §4, §7, §8, §10 | L | All syntax skills |
| `nextcloud-impl-background-jobs` | QueuedJob; TimedJob; cron config; job registration; scheduleAfter; time sensitivity; parallel run control | QueuedJob, TimedJob, IJobList, setInterval | §17 | M | core-architecture |
| `nextcloud-impl-occ-commands` | Custom OCC commands; built-in commands reference; arguments/options; input/output; command registration | Command, InputInterface, OutputInterface | §15 | M | core-architecture |
| `nextcloud-impl-collaboration` | Share API (OCS endpoints, types, permissions); notifications (INotificationManager, INotifier); activity providers; push notifications | IShareManager, INotificationManager, IActivityManager | §13, §14 | L | syntax-ocs-api |
| `nextcloud-impl-testing` | PHPUnit setup; TestCase base; integration tests; mocking NC services; frontend testing; container testing | TestCase, createMock, bootstrap.php | §18 | M | impl-app-scaffold |
| `nextcloud-impl-file-operations` | File handling workflows; CRUD operations; search; storage backends; external storage; versioning; trash; favorites | IRootFolder, getUserFolder, File/Folder ops | §12 | L | syntax-file-api |

### nextcloud-errors/ (4 skills)

| Name | Scope | Key APIs | Research Input | Complexity | Dependencies |
|------|-------|----------|----------------|------------|-------------|
| `nextcloud-errors-api` | OCS error codes; DAV error responses; HTTP status mapping; v1 vs v2 status confusion; missing headers | OCS statuscode, DAV error XML | §2, §3 | M | syntax-ocs-api, syntax-webdav |
| `nextcloud-errors-app` | App registration failures; namespace/autoloading; info.xml problems; migration failures; bootstrap errors | AppManager errors, migration exceptions | §5, §11, §19 | M | impl-app-scaffold |
| `nextcloud-errors-database` | Migration errors; query builder mistakes; entity mapping; type mismatches; Oracle/Galera issues; index problems | Migration exceptions, QB errors | §5, §19 | M | syntax-database |
| `nextcloud-errors-frontend` | Vue/Webpack errors; import path issues; CORS; CSRF token failures; @nextcloud/* version mismatches; deprecated APIs | Webpack errors, CSRF, CORS | §7, §8, §19 | M | syntax-frontend |

### nextcloud-agents/ (2 skills)

| Name | Scope | Key APIs | Research Input | Complexity | Dependencies |
|------|-------|----------|----------------|------------|-------------|
| `nextcloud-agents-review` | Validation checklist; API correctness; security attributes; anti-pattern detection; NC 28+ compliance; full-stack completeness | All validation rules | §19 (all anti-patterns) | M | ALL skills |
| `nextcloud-agents-app-scaffolder` | Generate complete NC app; PHP backend + Vue.js frontend; info.xml; routes; controllers; database; initial state | All scaffolding patterns | §11, §4, §7 | L | ALL skills |

---

## Batch Execution Plan (DEFINITIVE)

| Batch | Skills | Count | Dependencies | Notes |
|-------|--------|-------|-------------|-------|
| 1 | `core-architecture`, `core-config`, `core-security` | 3 | None | Foundation, no deps |
| 2 | `syntax-ocs-api`, `syntax-webdav`, `syntax-controllers` | 3 | Batch 1 | Primary API surfaces |
| 3 | `syntax-database`, `syntax-events`, `syntax-authentication` | 3 | Batch 1 | Backend patterns |
| 4 | `syntax-frontend`, `syntax-file-api`, `impl-app-scaffold` | 3 | Batch 1-3 | Frontend + file API + scaffold |
| 5 | `impl-app-development`, `impl-background-jobs`, `impl-occ-commands` | 3 | Batch 1-4 | Implementation workflows |
| 6 | `impl-collaboration`, `impl-testing`, `impl-file-operations` | 3 | Batch 2-4 | Remaining impl skills |
| 7 | `errors-api`, `errors-app`, `errors-database` | 3 | Batch 2-5 | Error handling skills |
| 8 | `errors-frontend`, `agents-review`, `agents-app-scaffolder` | 3 | ALL above | Frontend errors + agent skills |

**Total**: 24 skills across 8 batches.

---

## Per-Skill Agent Prompts

### Constants

```
PROJECT_ROOT = C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package
RESEARCH_DIR = C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package\docs\research
REQUIREMENTS_FILE = C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package\REQUIREMENTS.md
REFERENCE_SKILL = C:\Users\Freek Heijting\Documents\GitHub\Tauri-2-Claude-Skill-Package\skills\source\tauri-core\tauri-core-architecture\SKILL.md
```

---

### Batch 1

#### Prompt: nextcloud-core-architecture

```
## Task: Create the nextcloud-core-architecture skill

### Output Directory
C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package\skills\source\nextcloud-core\nextcloud-core-architecture\

### Files to Create
1. SKILL.md (main skill file, <500 lines)
2. references/methods.md (key interfaces: App, IBootstrap, IRegistrationContext, IServerContainer, core services)
3. references/examples.md (Application.php, DI patterns, service layer)
4. references/anti-patterns.md (DI mistakes, bootstrap errors)

### Reference Format
Read and follow the structure of:
C:\Users\Freek Heijting\Documents\GitHub\Tauri-2-Claude-Skill-Package\skills\source\tauri-core\tauri-core-architecture\SKILL.md

### YAML Frontmatter
---
name: nextcloud-core-architecture
description: "Guides Nextcloud platform architecture including PHP backend structure, Vue.js frontend layer, app lifecycle with IBootstrap register/boot phases, dependency injection with auto-wiring, service layer patterns, and key OCP interfaces. Activates when creating Nextcloud apps, understanding the platform architecture, or configuring dependency injection."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

### Scope (EXACT — do not exceed)
- Nextcloud platform overview: PHP backend, Vue.js frontend, data directory, apps directory
- Request lifecycle: index.php → lib/base.php → routing → controller
- App lifecycle: IBootstrap with register() and boot() phases
- DI container: auto-wiring, IRegistrationContext methods, predefined parameters ($appName, $userId)
- Service layer: constructor injection, service aliases, optional dependencies (nullable)
- Key OCP interfaces table (IDBConnection, IConfig, IRootFolder, IUserManager, etc.)
- Namespace conventions: OCA\{Namespace} mapping to lib/

### Research Sections to Read
- docs/research/backend-apis-research.md §1: Platform Architecture
- docs/research/frontend-events-research.md §10: Services & DI
- docs/research/frontend-events-research.md §11: App Structure (namespace/autoloading only)

### Quality Rules
- English only
- SKILL.md < 500 lines; heavy content goes in references/
- Use ALWAYS/NEVER deterministic language
- Include key interfaces table
- Include Critical Warnings about register() vs boot() timing
```

#### Prompt: nextcloud-core-config

```
## Task: Create the nextcloud-core-config skill

### Output Directory
C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package\skills\source\nextcloud-core\nextcloud-core-config\

### Files to Create
1. SKILL.md (<500 lines)
2. references/methods.md (config.php keys, IConfig methods, IAppConfig methods)
3. references/examples.md (config patterns, occ commands)
4. references/anti-patterns.md (config mistakes)

### YAML Frontmatter
---
name: nextcloud-core-config
description: "Guides Nextcloud configuration including config.php parameters, IConfig/IAppConfig interfaces, occ config commands, caching setup, proxy configuration, mail settings, and logging configuration. Activates when configuring Nextcloud server, reading/writing app configuration, or troubleshooting config issues."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

### Scope (EXACT)
- config.php key reference: trusted_domains, datadirectory, dbtype, overwrite.cli.url, proxy, mail, caching, logging, maintenance
- IConfig interface: getSystemValue, getAppValue, getUserValue, setters
- IAppConfig interface for app-specific config
- occ config:system and config:app commands
- Redis/APCu caching setup
- Maintenance mode and maintenance_window_start

### Research Sections to Read
- docs/research/vooronderzoek-nextcloud.md §16: Configuration

### Quality Rules
- English only, <500 lines SKILL.md, ALWAYS/NEVER language
- Include config.php key reference table in references/
- Include occ config command examples
```

#### Prompt: nextcloud-core-security

```
## Task: Create the nextcloud-core-security skill

### Output Directory
C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package\skills\source\nextcloud-core\nextcloud-core-security\

### Files to Create
1. SKILL.md (<500 lines)
2. references/methods.md (security attributes, middleware methods, CSP methods)
3. references/examples.md (security patterns, CSP config, middleware)
4. references/anti-patterns.md (security mistakes)

### YAML Frontmatter
---
name: nextcloud-core-security
description: "Guides Nextcloud security model including controller security defaults, middleware chain architecture, Content Security Policy configuration, security attributes overview, and encryption interfaces. Activates when securing Nextcloud apps, configuring CSP, understanding the middleware chain, or implementing security patterns."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

### Scope (EXACT)
- Controller security defaults (admin-only, authenticated, 2FA, CSRF)
- Security attributes: #[NoAdminRequired], #[PublicPage], #[NoCSRFRequired], #[NoTwoFactorRequired]
- Middleware chain: beforeController → afterException → afterController → beforeOutput
- Custom middleware registration (app and global)
- Content Security Policy: CSP methods, per-response and global CSP
- Security-related events catalog

### Research Sections to Read
- docs/research/backend-apis-research.md §4: Middleware section
- docs/research/backend-apis-research.md §6: Security model

### Quality Rules
- English only, <500 lines SKILL.md, ALWAYS/NEVER language
- Include security attribute table
- Include middleware hook order diagram
- Critical Warnings about default security posture
```

---

### Batch 2

#### Prompt: nextcloud-syntax-ocs-api

```
## Task: Create the nextcloud-syntax-ocs-api skill

### Output Directory
C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package\skills\source\nextcloud-syntax\nextcloud-syntax-ocs-api\

### Files to Create
1. SKILL.md (<500 lines)
2. references/methods.md (all OCS endpoints, response format, share API details)
3. references/examples.md (curl examples for all major endpoints)
4. references/anti-patterns.md (OCS mistakes)

### YAML Frontmatter
---
name: nextcloud-syntax-ocs-api
description: "Guides Nextcloud OCS REST API including endpoint structure, v1 vs v2 versioning, authentication methods, response envelope format, capabilities discovery, user provisioning, share API endpoints, and user status API. Activates when calling OCS endpoints, creating OCS controllers, handling OCS responses, or implementing share operations."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

### Scope (EXACT)
- OCS v1 vs v2 endpoint differences and status codes
- OCS response envelope (ocs.meta, ocs.data) in XML and JSON
- Required OCS-APIRequest header
- Authentication: basic auth, app passwords, session cookies
- Key endpoints: capabilities, user provisioning, share API, user status, autocomplete
- OCSController for app endpoints
- Share API: types, permissions bitmask, create/read/update/delete

### Research Sections to Read
- docs/research/backend-apis-research.md §2: OCS API

### Quality Rules
- English only, <500 lines SKILL.md, ALWAYS/NEVER language
- Include endpoint reference table
- Include share type and permission bitmask tables
- Include curl examples for major operations
```

#### Prompt: nextcloud-syntax-webdav

```
## Task: Create the nextcloud-syntax-webdav skill

### Output Directory
C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package\skills\source\nextcloud-syntax\nextcloud-syntax-webdav\

### Files to Create
1. SKILL.md (<500 lines)
2. references/methods.md (DAV operations, properties, namespaces, chunked upload)
3. references/examples.md (curl examples for all DAV operations)
4. references/anti-patterns.md (DAV mistakes)

### YAML Frontmatter
---
name: nextcloud-syntax-webdav
description: "Guides Nextcloud WebDAV API including DAV endpoint structure, file operations (PROPFIND/GET/PUT/MKCOL/MOVE/COPY/DELETE), property namespaces, special headers, chunked upload v2 protocol, and public share DAV access. Activates when performing file operations via WebDAV, implementing chunked uploads, or querying file properties."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

### Scope (EXACT)
- DAV endpoint structure: /remote.php/dav/files/, calendars, contacts, uploads, trashbin, versions
- All 7 file operations with headers and examples
- Property namespaces: d:, oc:, nc:, ocs:, ocm:
- Special headers: X-OC-MTime, OC-Checksum, X-NC-WebDAV-AutoMkcol
- Chunked upload v2: 3-step protocol (MKCOL → PUT chunks → MOVE .file)
- Public share DAV access (NC 29+)

### Research Sections to Read
- docs/research/backend-apis-research.md §3: WebDAV

### Quality Rules
- English only, <500 lines SKILL.md, ALWAYS/NEVER language
- Include complete chunked upload protocol
- Include namespace reference table
- Include curl examples for all operations
```

#### Prompt: nextcloud-syntax-controllers

```
## Task: Create the nextcloud-syntax-controllers skill

### Output Directory
C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package\skills\source\nextcloud-syntax\nextcloud-syntax-controllers\

### Files to Create
1. SKILL.md (<500 lines)
2. references/methods.md (Controller types, route syntax, response types, parameter extraction)
3. references/examples.md (controller patterns, routing patterns)
4. references/anti-patterns.md (controller mistakes)

### YAML Frontmatter
---
name: nextcloud-syntax-controllers
description: "Guides Nextcloud controller development including Controller and OCSController types, routes.php definition, attribute-based routing, parameter extraction, security attributes, response types, and format negotiation. Activates when creating controllers, defining routes, handling requests, or implementing API endpoints."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

### Scope (EXACT)
- Controller types: Controller, OCSController, ApiController
- routes.php: routes, ocs, resources arrays
- Attribute-based routing (#[FrontpageRoute], #[ApiRoute]) (NC 29+)
- Route name resolution and URL generation
- Parameter extraction: URL path, query, JSON body, type casting
- Security attributes table
- Response types: TemplateResponse, JSONResponse, DataResponse, etc.
- Responder system for format negotiation

### Research Sections to Read
- docs/research/backend-apis-research.md §4: Controllers & Routing

### Quality Rules
- English only, <500 lines SKILL.md, ALWAYS/NEVER language
- Include route definition examples (all 3 array types)
- Include response type table
- Include security attribute table
```

---

### Batch 3

#### Prompt: nextcloud-syntax-database

```
## Task: Create the nextcloud-syntax-database skill

### Output Directory
C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package\skills\source\nextcloud-syntax\nextcloud-syntax-database\

### Files to Create
1. SKILL.md (<500 lines)
2. references/methods.md (migration API, Entity API, QBMapper API, QueryBuilder API)
3. references/examples.md (migration, entity, mapper, query builder patterns)
4. references/anti-patterns.md (database mistakes, Oracle/Galera issues)

### YAML Frontmatter
---
name: nextcloud-syntax-database
description: "Guides Nextcloud database layer including migrations with ISchemaWrapper, Entity definitions with auto-generated getters/setters, QBMapper CRUD operations, query builder with joins and expressions, TTransactional trait, column types, and Oracle/Galera constraints. Activates when creating database tables, writing migrations, implementing entities and mappers, or building queries."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

### Scope (EXACT)
- Migration system: SimpleMigrationStep, changeSchema, postSchemaChange, naming convention
- Entity: extend Entity, property types, camelCase→snake_case mapping, addType
- QBMapper: constructor, findEntity, findEntities, insert, update, delete
- Query builder: select, from, join, where, expressions, named parameters
- TTransactional trait for atomic operations
- Column types (OCP\DB\Types)
- Constraints: table name max 23 chars, Oracle limits, Galera primary keys
- Index management: AddMissingIndicesEvent, replaceIndex

### Research Sections to Read
- docs/research/backend-apis-research.md §5: Database Layer

### Quality Rules
- English only, <500 lines SKILL.md, ALWAYS/NEVER language
- Include complete migration example
- Include Entity + QBMapper pattern
- Include constraints table (Oracle, Galera)
```

#### Prompt: nextcloud-syntax-events

```
## Task: Create the nextcloud-syntax-events skill

### Output Directory
C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package\skills\source\nextcloud-syntax\nextcloud-syntax-events\

### Files to Create
1. SKILL.md (<500 lines)
2. references/methods.md (IEventDispatcher, Event base, IEventListener, all built-in events)
3. references/examples.md (custom events, listeners, dispatching, frontend event-bus)
4. references/anti-patterns.md (event mistakes)

### YAML Frontmatter
---
name: nextcloud-syntax-events
description: "Guides Nextcloud event system including IEventDispatcher, typed events, IEventListener interface, event registration via IRegistrationContext, Before/After naming pattern, built-in event catalog, custom event creation, and frontend @nextcloud/event-bus. Activates when creating event listeners, dispatching events, hooking into file/user/share operations, or implementing cross-component communication."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

### Scope (EXACT)
- IEventDispatcher: addListener, addServiceListener, dispatchTyped
- IEventListener interface and handle() method
- Event registration via registerEventListener in Application
- Custom event creation (extend Event)
- Before/After naming pattern
- Built-in events: file, user, group, share, calendar, contacts, auth, app lifecycle
- Frontend @nextcloud/event-bus: subscribe, emit, unsubscribe, typed events

### Research Sections to Read
- docs/research/frontend-events-research.md §9: Event System
- docs/research/frontend-events-research.md §8: @nextcloud/event-bus section

### Quality Rules
- English only, <500 lines SKILL.md, ALWAYS/NEVER language
- Include built-in events catalog table in references/
- Include both PHP and frontend event patterns
- NEVER use deprecated hooks or GenericEvent
```

#### Prompt: nextcloud-syntax-authentication

```
## Task: Create the nextcloud-syntax-authentication skill

### Output Directory
C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package\skills\source\nextcloud-syntax\nextcloud-syntax-authentication\

### Files to Create
1. SKILL.md (<500 lines)
2. references/methods.md (Login Flow v2 endpoints, security attributes, rate limiting)
3. references/examples.md (Login Flow v2, CSRF handling, brute force protection)
4. references/anti-patterns.md (auth mistakes)

### YAML Frontmatter
---
name: nextcloud-syntax-authentication
description: "Guides Nextcloud authentication including Login Flow v2 protocol, app passwords, CSRF token handling, rate limiting with UserRateLimit and AnonRateLimit attributes, brute force protection with throttle(), and OAuth2. Activates when implementing authentication, handling CSRF tokens, configuring rate limiting, or integrating external clients via Login Flow v2."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

### Scope (EXACT)
- Login Flow v2: 4-step protocol (initiate, browser auth, poll, receive credentials)
- App passwords: creation, usage, scoping
- CSRF protection: default behavior, requesttoken, OCS-APIRequest header
- Rate limiting: #[UserRateLimit], #[AnonRateLimit] attributes
- Brute force protection: #[BruteForceProtection], throttle() on response
- Security-related events: LoginFailedEvent, UserFirstTimeLoggedInEvent, etc.
- Controller defaults: admin-only, authenticated, 2FA, CSRF

### Research Sections to Read
- docs/research/backend-apis-research.md §6: Authentication & Security

### Quality Rules
- English only, <500 lines SKILL.md, ALWAYS/NEVER language
- Include complete Login Flow v2 sequence diagram
- Include CSRF decision tree
- Include rate limiting attribute examples
```

---

### Batch 4

#### Prompt: nextcloud-syntax-frontend

```
## Task: Create the nextcloud-syntax-frontend skill

### Output Directory
C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package\skills\source\nextcloud-syntax\nextcloud-syntax-frontend\

### Files to Create
1. SKILL.md (<500 lines)
2. references/methods.md (@nextcloud/vue components, @nextcloud/* package APIs)
3. references/examples.md (Vue app setup, data fetching, component usage)
4. references/anti-patterns.md (frontend mistakes)

### YAML Frontmatter
---
name: nextcloud-syntax-frontend
description: "Guides Nextcloud Vue.js frontend development including @nextcloud/vue component library, @nextcloud/axios HTTP client, @nextcloud/router URL generation, @nextcloud/initial-state data injection, @nextcloud/dialogs toasts and file picker, @nextcloud/files DAV client, Webpack configuration, CSS custom properties, and dark mode support. Activates when building Nextcloud app frontends, using Vue components, making API calls from JavaScript, or styling with Nextcloud design system."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

### Scope (EXACT)
- @nextcloud/vue: key components (NcButton, NcAppContent, NcAppNavigation, NcDialog, etc.), import patterns, version compatibility
- @nextcloud/axios: authenticated HTTP client, retry, session reload
- @nextcloud/router: generateUrl, generateOcsUrl, generateRemoteUrl, generateFilePath
- @nextcloud/initial-state: provideInitialState (PHP), loadState (JS), lazy state
- @nextcloud/dialogs: showSuccess/Error/Warning/Info, FilePicker
- @nextcloud/files: DAV client, File/Folder classes, Permission enum, sidebar/menu integration
- Webpack setup: @nextcloud/webpack-vue-config
- CSS custom properties for theming and dark mode
- Frontend app structure: src/, main.js, App.vue

### Research Sections to Read
- docs/research/frontend-events-research.md §7: Vue.js Frontend
- docs/research/frontend-events-research.md §8: Frontend Data Fetching

### Quality Rules
- English only, <500 lines SKILL.md, ALWAYS/NEVER language
- Include @nextcloud/vue component table
- Include CSS custom properties table
- Include import pattern examples (direct vs barrel)
```

#### Prompt: nextcloud-syntax-file-api

```
## Task: Create the nextcloud-syntax-file-api skill

### Output Directory
C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package\skills\source\nextcloud-syntax\nextcloud-syntax-file-api\

### Files to Create
1. SKILL.md (<500 lines)
2. references/methods.md (IRootFolder, IUserFolder, File, Folder methods)
3. references/examples.md (file CRUD, events, storage access)
4. references/anti-patterns.md (file handling mistakes)

### YAML Frontmatter
---
name: nextcloud-syntax-file-api
description: "Guides Nextcloud PHP file handling including Node API with IRootFolder and IUserFolder, File and Folder interfaces, file CRUD operations, file events (BeforeNodeCreated, NodeWritten, etc.), storage wrappers, versioning, and trash API. Activates when reading/writing files programmatically, listening to file events, or working with Nextcloud's filesystem abstraction."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

### Scope (EXACT)
- IRootFolder: injection point, getUserFolder()
- IUserFolder: get(), getById(), newFile(), newFolder(), nodeExists()
- File: getContent(), putContent(), getMimeType(), getSize()
- Folder: listing, searching, getting children
- File events: complete Before/After event table
- NotFoundException handling (ALWAYS wrap in try/catch)
- getById() returns array (multiple mount points)
- Storage layer access (use sparingly)

### Research Sections to Read
- docs/research/vooronderzoek-nextcloud.md §12: File Handling API

### Quality Rules
- English only, <500 lines SKILL.md, ALWAYS/NEVER language
- Include File/Folder method tables
- Include file events table
- Critical Warning: getById() returns array, not single node
```

#### Prompt: nextcloud-impl-app-scaffold

```
## Task: Create the nextcloud-impl-app-scaffold skill

### Output Directory
C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package\skills\source\nextcloud-impl\nextcloud-impl-app-scaffold\

### Files to Create
1. SKILL.md (<500 lines)
2. references/methods.md (info.xml fields, Application.php API, namespace mapping)
3. references/examples.md (complete info.xml, Application.php, directory structure)
4. references/anti-patterns.md (scaffold mistakes)

### YAML Frontmatter
---
name: nextcloud-impl-app-scaffold
description: "Guides Nextcloud app scaffolding including directory structure conventions, info.xml manifest with all fields and constraints, Application.php with IBootstrap lifecycle, namespace conventions and autoloading, and the official app generator. Activates when creating a new Nextcloud app, setting up info.xml, configuring Application.php, or understanding app directory layout."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

### Scope (EXACT)
- Complete app directory layout with all subdirectories
- info.xml: required fields, optional fields, field constraints, categories, deprecated fields
- Application.php: IBootstrap, register() vs boot() lifecycle
- Namespace conventions: OCA\{Namespace} → lib/
- Autoloading rules
- Navigation entry configuration
- App generator: https://apps.nextcloud.com/developer/apps/generate

### Research Sections to Read
- docs/research/frontend-events-research.md §11: App Structure & Bootstrap

### Quality Rules
- English only, <500 lines SKILL.md, ALWAYS/NEVER language
- Include complete directory structure diagram
- Include minimal and complete info.xml examples
- Include info.xml field constraints table
```

---

### Batch 5

#### Prompt: nextcloud-impl-app-development

```
## Task: Create the nextcloud-impl-app-development skill

### Output Directory
C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package\skills\source\nextcloud-impl\nextcloud-impl-app-development\

### Files to Create
1. SKILL.md (<500 lines)
2. references/methods.md (full-stack development patterns)
3. references/examples.md (complete app example: controller → service → mapper → Vue.js)
4. references/anti-patterns.md (development workflow mistakes)

### YAML Frontmatter
---
name: nextcloud-impl-app-development
description: "Guides full-stack Nextcloud app development workflow including creating controllers with routes, implementing service layer with DI, database entities and mappers, Vue.js frontend with @nextcloud packages, initial state bridge between PHP and JavaScript, and the development lifecycle. Activates when building a complete Nextcloud app, connecting PHP backend to Vue.js frontend, or implementing CRUD operations."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

### Scope (EXACT)
- Full-stack app creation workflow (step-by-step)
- PHP backend: Controller → Service → Mapper → Entity
- Frontend: main.js → App.vue → components → API calls
- Initial state bridge: provideInitialState (PHP) → loadState (JS)
- API patterns: OCS endpoint with OCSController + frontend axios call
- Development commands: npm run dev, npm run build
- Decision tree: when to use regular routes vs OCS routes

### Research Sections to Read
- All research sections — this is a cross-cutting implementation skill

### Quality Rules
- English only, <500 lines SKILL.md, ALWAYS/NEVER language
- MUST show both PHP and Vue.js sides for every pattern
- Include complete CRUD example flow
- Include initial state bridge pattern
```

#### Prompt: nextcloud-impl-background-jobs

```
## Task: Create the nextcloud-impl-background-jobs skill

### Output Directory
C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package\skills\source\nextcloud-impl\nextcloud-impl-background-jobs\

### Files to Create
1. SKILL.md (<500 lines)
2. references/methods.md (QueuedJob, TimedJob, IJobList API)
3. references/examples.md (timed job, queued job, scheduled job, registration)
4. references/anti-patterns.md (background job mistakes)

### YAML Frontmatter
---
name: nextcloud-impl-background-jobs
description: "Guides Nextcloud background jobs including QueuedJob for one-time tasks, TimedJob for recurring tasks, IJobList for programmatic management, scheduleAfter for delayed execution, cron configuration modes, time sensitivity, and parallel run control. Activates when implementing background processing, scheduling recurring tasks, or configuring cron."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

### Scope (EXACT)
- TimedJob: setInterval(), ITimeFactory requirement, recurring execution
- QueuedJob: one-time execution, argument passing
- Registration: info.xml background-jobs and programmatic IJobList
- scheduleAfter() for delayed execution
- Time sensitivity: setTimeSensitivity(TIME_INSENSITIVE) for heavy jobs
- Parallel runs: setAllowParallelRuns(false) (NC 27+)
- Cron modes: system cron (recommended), webcron, AJAX

### Research Sections to Read
- docs/research/vooronderzoek-nextcloud.md §17: Background Jobs

### Quality Rules
- English only, <500 lines SKILL.md, ALWAYS/NEVER language
- Include decision tree: QueuedJob vs TimedJob
- Include cron mode comparison table
- Critical Warning: NEVER use AJAX mode in production
```

#### Prompt: nextcloud-impl-occ-commands

```
## Task: Create the nextcloud-impl-occ-commands skill

### Output Directory
C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package\skills\source\nextcloud-impl\nextcloud-impl-occ-commands\

### Files to Create
1. SKILL.md (<500 lines)
2. references/methods.md (Command class, built-in commands reference)
3. references/examples.md (custom command, built-in command usage)
4. references/anti-patterns.md (occ mistakes)

### YAML Frontmatter
---
name: nextcloud-impl-occ-commands
description: "Guides Nextcloud OCC console commands including built-in commands for maintenance, user management, app management, file scanning, and configuration, plus custom command development with Symfony Console. Activates when using occ commands, creating custom CLI commands, or administering Nextcloud from the command line."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

### Scope (EXACT)
- occ usage: sudo -u www-data php occ [command]
- Built-in commands: maintenance, user, app, config, files, background
- Custom command: extend Symfony Command, configure(), execute()
- Arguments and options: InputArgument, InputOption
- Command registration in info.xml
- Output formatting: writeln, tables, progress bars

### Research Sections to Read
- docs/research/vooronderzoek-nextcloud.md §15: OCC Commands

### Quality Rules
- English only, <500 lines SKILL.md, ALWAYS/NEVER language
- Include built-in commands reference table
- Include complete custom command example
- Critical Warning: NEVER run occ as root
```

---

### Batch 6

#### Prompt: nextcloud-impl-collaboration

```
## Task: Create the nextcloud-impl-collaboration skill

### Output Directory
C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package\skills\source\nextcloud-impl\nextcloud-impl-collaboration\

### Files to Create
1. SKILL.md (<500 lines)
2. references/methods.md (Share API, Notification API, Activity API)
3. references/examples.md (share CRUD, notifications, activity events)
4. references/anti-patterns.md (collaboration mistakes)

### YAML Frontmatter
---
name: nextcloud-impl-collaboration
description: "Guides Nextcloud collaboration APIs including OCS Share API with share types and permissions, notification system with INotificationManager and INotifier, activity stream with IActivityManager, and push notifications. Activates when implementing file sharing, creating notifications, publishing activity events, or building collaboration features."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

### Scope (EXACT)
- Share API: OCS endpoints, share types (0-10), permission bitmask, share attributes
- Share CRUD: create, read, update, delete via OCS
- INotificationManager: createNotification, notify, markProcessed
- INotifier: prepare() with language keys, UnknownNotificationException
- Notification actions and rich subjects
- IActivityManager: generateEvent, publish
- Push notifications: defer/flush pattern

### Research Sections to Read
- docs/research/vooronderzoek-nextcloud.md §13: Sharing API
- docs/research/vooronderzoek-nextcloud.md §14: Notifications API

### Quality Rules
- English only, <500 lines SKILL.md, ALWAYS/NEVER language
- Include share type table and permission bitmask table
- Include notification creation + notifier pattern
- NEVER put translated strings in setSubject()
```

#### Prompt: nextcloud-impl-testing

```
## Task: Create the nextcloud-impl-testing skill

### Output Directory
C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package\skills\source\nextcloud-impl\nextcloud-impl-testing\

### Files to Create
1. SKILL.md (<500 lines)
2. references/methods.md (TestCase, mock methods, phpunit.xml)
3. references/examples.md (unit test, integration test, frontend test)
4. references/anti-patterns.md (testing mistakes)

### YAML Frontmatter
---
name: nextcloud-impl-testing
description: "Guides Nextcloud app testing including PHPUnit setup with TestCase base class, unit testing with mocks, integration testing with DI container, database transaction management, frontend testing with Vue Test Utils, and phpunit.xml configuration. Activates when writing tests for Nextcloud apps, setting up test infrastructure, or mocking Nextcloud services."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

### Scope (EXACT)
- PHPUnit setup: phpunit.xml, bootstrap path
- TestCase base class: setUp/tearDown (ALWAYS call parent)
- Unit testing: createMock, expectations
- Integration testing: container-based, service resolution
- Mocking NC services in DI container
- Frontend testing: Jest, @vue/test-utils
- Test file organization

### Research Sections to Read
- docs/research/vooronderzoek-nextcloud.md §18: Testing

### Quality Rules
- English only, <500 lines SKILL.md, ALWAYS/NEVER language
- Include phpunit.xml example
- Include unit and integration test examples
- Critical Warning: ALWAYS call parent::setUp()
```

#### Prompt: nextcloud-impl-file-operations

```
## Task: Create the nextcloud-impl-file-operations skill

### Output Directory
C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package\skills\source\nextcloud-impl\nextcloud-impl-file-operations\

### Files to Create
1. SKILL.md (<500 lines)
2. references/methods.md (complete File/Folder/IRootFolder method reference)
3. references/examples.md (CRUD workflows, search, event handling)
4. references/anti-patterns.md (file operation mistakes)

### YAML Frontmatter
---
name: nextcloud-impl-file-operations
description: "Guides Nextcloud file operation workflows including reading, writing, creating, deleting files and folders using the Node API, file search patterns, listening to file events, working with favorites, trash and versioning, and advanced storage access patterns. Activates when implementing file manipulation features, building file-aware apps, or handling file lifecycle events."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

### Scope (EXACT)
- File CRUD: create, read, update, delete with Node API
- Folder operations: create, list, search, recursive operations
- Error handling: NotFoundException, NotPermittedException
- File events: registering listeners, event data access
- Favorites: NodeAddedToFavorite, NodeRemovedFromFavorite
- Trash and versioning endpoints
- Storage backend access (when Node API is insufficient)

### Research Sections to Read
- docs/research/vooronderzoek-nextcloud.md §12: File Handling API

### Quality Rules
- English only, <500 lines SKILL.md, ALWAYS/NEVER language
- Include complete CRUD workflow examples
- Include error handling patterns
- Include file events integration
```

---

### Batch 7

#### Prompt: nextcloud-errors-api

```
## Task: Create the nextcloud-errors-api skill

### Output Directory
C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package\skills\source\nextcloud-errors\nextcloud-errors-api\

### Files to Create
1. SKILL.md (<500 lines)
2. references/methods.md (OCS error codes, DAV error format)
3. references/examples.md (error scenarios with fixes)
4. references/anti-patterns.md (API error causes)

### YAML Frontmatter
---
name: nextcloud-errors-api
description: "Diagnoses and resolves Nextcloud API errors including OCS status code confusion (v1 vs v2), missing OCS-APIRequest header, DAV error responses, HTTP status mapping, authentication failures, and CORS issues. Activates when encountering OCS or WebDAV API errors, debugging response codes, or troubleshooting authentication."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

### Scope (EXACT)
- OCS v1 vs v2 status code mapping
- Missing OCS-APIRequest header (CSRF rejection)
- DAV error XML format
- HTTP status codes for OCS endpoints
- Authentication failures: wrong credentials, expired tokens
- CORS issues with API controllers

### Research Sections to Read
- docs/research/backend-apis-research.md §2, §3 (error-related content)
- docs/research/vooronderzoek-nextcloud.md §19: Anti-Patterns (OCS section)

### Quality Rules
- English only, <500 lines SKILL.md, ALWAYS/NEVER language
- Format as diagnostic: Symptom → Cause → Fix
```

#### Prompt: nextcloud-errors-app

```
## Task: Create the nextcloud-errors-app skill

### Output Directory
C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package\skills\source\nextcloud-errors\nextcloud-errors-app\

### Files to Create
1. SKILL.md (<500 lines)
2. references/methods.md (error types, exception classes)
3. references/examples.md (error scenarios with fixes)
4. references/anti-patterns.md (app development mistakes)

### YAML Frontmatter
---
name: nextcloud-errors-app
description: "Diagnoses and resolves Nextcloud app development errors including namespace and autoloading failures, info.xml validation problems, migration errors, bootstrap timing issues, DI resolution failures, and deprecated API usage. Activates when encountering app registration errors, class not found exceptions, migration failures, or dependency injection problems."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

### Scope (EXACT)
- Namespace/autoloading: missing namespace in info.xml, wrong directory structure
- info.xml: deprecated fields, missing required fields, version constraints
- Migration errors: modifying existing migrations, naming convention
- Bootstrap: register() vs boot() timing violations
- DI: unresolvable constructor parameters, missing type hints
- Deprecated API warnings: OCP\ILogger, \OCP\Server::get(), hooks

### Research Sections to Read
- docs/research/frontend-events-research.md §11: App Structure (anti-patterns)
- docs/research/backend-apis-research.md §1, §5 (anti-patterns)
- docs/research/vooronderzoek-nextcloud.md §19

### Quality Rules
- English only, <500 lines SKILL.md, ALWAYS/NEVER language
- Format as diagnostic: Symptom → Cause → Fix
```

#### Prompt: nextcloud-errors-database

```
## Task: Create the nextcloud-errors-database skill

### Output Directory
C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package\skills\source\nextcloud-errors\nextcloud-errors-database\

### Files to Create
1. SKILL.md (<500 lines)
2. references/methods.md (database error types, constraint violations)
3. references/examples.md (error scenarios with fixes)
4. references/anti-patterns.md (database mistakes)

### YAML Frontmatter
---
name: nextcloud-errors-database
description: "Diagnoses and resolves Nextcloud database errors including migration failures, query builder mistakes, entity mapping issues, type mismatches, Oracle and Galera cluster constraints, index problems, and table naming violations. Activates when encountering database errors, migration problems, or query failures."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

### Scope (EXACT)
- Migration failures: modified existing migration, naming convention wrong
- Query builder: raw SQL instead of QB, forgetting named parameters
- Entity mapping: wrong property types, camelCase/snake_case mismatch
- Oracle constraints: name length, NOT NULL string, boolean, 4000 char limit
- Galera: missing primary key
- Table naming: exceeding 23 character limit
- Cursor management: forgetting closeCursor()
- Index: non-unique names

### Research Sections to Read
- docs/research/backend-apis-research.md §5: Database (anti-patterns and constraints)
- docs/research/vooronderzoek-nextcloud.md §19: Database section

### Quality Rules
- English only, <500 lines SKILL.md, ALWAYS/NEVER language
- Format as diagnostic: Symptom → Cause → Fix
- Include Oracle/Galera constraint reference table
```

---

### Batch 8

#### Prompt: nextcloud-errors-frontend

```
## Task: Create the nextcloud-errors-frontend skill

### Output Directory
C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package\skills\source\nextcloud-errors\nextcloud-errors-frontend\

### Files to Create
1. SKILL.md (<500 lines)
2. references/methods.md (frontend error types)
3. references/examples.md (error scenarios with fixes)
4. references/anti-patterns.md (frontend mistakes)

### YAML Frontmatter
---
name: nextcloud-errors-frontend
description: "Diagnoses and resolves Nextcloud frontend errors including Vue/Webpack build failures, @nextcloud/* import path issues, CORS problems, CSRF token failures, missing dialog styles, deprecated OC global usage, version mismatches between @nextcloud packages and Nextcloud server, and initial state loading errors. Activates when encountering frontend build errors, runtime JavaScript errors, or API call failures from the browser."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

### Scope (EXACT)
- Import path errors: wrong @nextcloud/* internal paths
- CSRF failures: missing token, missing @nextcloud/axios
- CORS issues: wrong controller type (Controller vs ApiController)
- Missing styles: @nextcloud/dialogs without CSS import
- Deprecated globals: OC.generateUrl, OCA.Theming without check
- loadState() throwing on missing key (no fallback)
- Vue 2 vs Vue 3 compatibility (@nextcloud/vue v8 vs v9)
- Webpack config issues

### Research Sections to Read
- docs/research/frontend-events-research.md §7, §8 (anti-patterns)
- docs/research/vooronderzoek-nextcloud.md §19: Frontend section

### Quality Rules
- English only, <500 lines SKILL.md, ALWAYS/NEVER language
- Format as diagnostic: Symptom → Cause → Fix
```

#### Prompt: nextcloud-agents-review

```
## Task: Create the nextcloud-agents-review skill

### Output Directory
C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package\skills\source\nextcloud-agents\nextcloud-agents-review\

### Files to Create
1. SKILL.md (<500 lines)
2. references/methods.md (complete validation checklist)
3. references/examples.md (review scenarios: good code, bad code, fixes)
4. references/anti-patterns.md (all anti-patterns consolidated)

### YAML Frontmatter
---
name: nextcloud-agents-review
description: "Validates generated Nextcloud code for correctness by checking controller security attributes, OCS endpoint patterns, database migration integrity, DI patterns, frontend import paths, CSRF handling, file API usage, and known anti-patterns. Activates when reviewing Nextcloud app code, validating before deployment, or checking for common mistakes."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

### Scope (EXACT)
- Controller validation: security attributes present, correct route patterns
- OCS validation: v2 endpoints, OCS-APIRequest header, response format
- Database validation: migration naming, no modified migrations, primary keys
- DI validation: constructor injection, no Server::get()
- Frontend validation: @nextcloud/* imports, no OC globals, CSRF handling
- File API validation: NotFoundException handling, getById() array check
- Security validation: no PublicPage+NoCSRFRequired on state-changing endpoints
- Event validation: typed events, no deprecated hooks

### Research Sections to Read
- docs/research/vooronderzoek-nextcloud.md §19: All Anti-Patterns

### Quality Rules
- English only, <500 lines SKILL.md, ALWAYS/NEVER language
- Structure as runnable checklist grouped by area
- Each check: what to verify, expected state, common failure
```

#### Prompt: nextcloud-agents-app-scaffolder

```
## Task: Create the nextcloud-agents-app-scaffolder skill

### Output Directory
C:\Users\Freek Heijting\Documents\GitHub\Nextcloud-Claude-Skill-Package\skills\source\nextcloud-agents\nextcloud-agents-app-scaffolder\

### Files to Create
1. SKILL.md (<500 lines)
2. references/methods.md (scaffolding templates, file generation patterns)
3. references/examples.md (complete scaffolded app output)
4. references/anti-patterns.md (scaffolding mistakes)

### YAML Frontmatter
---
name: nextcloud-agents-app-scaffolder
description: "Generates complete Nextcloud app structure including PHP backend with controllers, services, entities and mappers, Vue.js frontend with @nextcloud packages, info.xml manifest, routes.php, database migrations, Application.php bootstrap, webpack configuration, and test infrastructure. Activates when generating a new Nextcloud app from scratch, scaffolding app features, or creating a complete app template."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

### Scope (EXACT)
- Complete file listing with content templates
- PHP: Application.php, Controller, Service, Entity, Mapper, Migration
- Frontend: main.js, App.vue, webpack.config.js, package.json
- Config: info.xml, routes.php, composer.json
- Tests: phpunit.xml, bootstrap, sample test
- Decision tree: which components to include based on requirements
- Generated code follows ALL patterns from syntax skills

### Research Sections to Read
- All research sections — scaffolder must generate correct code for all patterns

### Quality Rules
- English only, <500 lines SKILL.md, ALWAYS/NEVER language
- Include complete file listing with templates
- Include feature selection decision tree
- Generated code MUST follow all patterns from other skills
```

---

## Appendix: Skill Directory Structure

```
skills/source/
├── nextcloud-core/
│   ├── nextcloud-core-architecture/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── methods.md
│   │       ├── examples.md
│   │       └── anti-patterns.md
│   ├── nextcloud-core-config/
│   │   ├── SKILL.md
│   │   └── references/
│   └── nextcloud-core-security/
│       ├── SKILL.md
│       └── references/
├── nextcloud-syntax/
│   ├── nextcloud-syntax-ocs-api/
│   ├── nextcloud-syntax-webdav/
│   ├── nextcloud-syntax-controllers/
│   ├── nextcloud-syntax-database/
│   ├── nextcloud-syntax-events/
│   ├── nextcloud-syntax-frontend/
│   ├── nextcloud-syntax-authentication/
│   └── nextcloud-syntax-file-api/
├── nextcloud-impl/
│   ├── nextcloud-impl-app-scaffold/
│   ├── nextcloud-impl-app-development/
│   ├── nextcloud-impl-background-jobs/
│   ├── nextcloud-impl-occ-commands/
│   ├── nextcloud-impl-collaboration/
│   ├── nextcloud-impl-testing/
│   └── nextcloud-impl-file-operations/
├── nextcloud-errors/
│   ├── nextcloud-errors-api/
│   ├── nextcloud-errors-app/
│   ├── nextcloud-errors-database/
│   └── nextcloud-errors-frontend/
└── nextcloud-agents/
    ├── nextcloud-agents-review/
    └── nextcloud-agents-app-scaffolder/
```
