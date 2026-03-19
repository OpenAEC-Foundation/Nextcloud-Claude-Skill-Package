# Nextcloud Skill Package — Raw Masterplan

## Status

Phase 1 complete. Raw masterplan created with preliminary skill inventory.
Date: 2026-03-19

---

## Preliminary Skill Inventory (25 skills — subject to refinement in Phase 3)

### nextcloud-core/ (3 skills)

| Name | Scope | Key APIs | Complexity |
|------|-------|----------|------------|
| `nextcloud-core-architecture` | NC platform architecture; PHP backend + Vue.js frontend layers; OCS/DAV/REST API model; app ecosystem; directory structure; key interfaces | IAppManager, IServerContainer, IAppConfig | M |
| `nextcloud-core-config` | config.php reference; occ config commands; environment variables; system config vs app config; theming config | config.php keys, occ config:system, occ config:app | L |
| `nextcloud-core-security` | Authentication model; CSRF protection; rate limiting; brute force protection; encryption; middleware chain; Content Security Policy | ISecureRandom, ICrypto, CSRF tokens, Middleware | M |

### nextcloud-syntax/ (8 skills)

| Name | Scope | Key APIs | Complexity |
|------|-------|----------|------------|
| `nextcloud-syntax-ocs-api` | OCS REST API endpoints; v1 vs v2 endpoints; authentication methods; response envelope format; XML vs JSON; status codes | /ocs/v2.php/*, OCSController, basic auth, app passwords | L |
| `nextcloud-syntax-webdav` | DAV file operations; PROPFIND/GET/PUT/MKCOL/MOVE/COPY/DELETE; properties; namespaces; chunked upload protocol | /remote.php/dav/files/, /remote.php/dav/uploads/ | L |
| `nextcloud-syntax-controllers` | PHP controllers; OCSController vs Controller; routing (routes.php); API controllers; middleware; annotations/attributes | OCSController, Controller, #[ApiRoute], routes.php | M |
| `nextcloud-syntax-database` | Database layer; migrations; entities; mappers; QBMapper; query builder; raw queries; types | ISchemaWrapper, Entity, QBMapper, IQueryBuilder | L |
| `nextcloud-syntax-services` | Service layer patterns; dependency injection; IServerContainer; registrations; inter-service communication | IServerContainer, IRegistrationContext, registerService | M |
| `nextcloud-syntax-events` | Event system; EventDispatcher; typed events; listeners; hooks (deprecated vs new); BeforeNode/AfterNode events | IEventDispatcher, Event classes, registerEventListener | M |
| `nextcloud-syntax-vue-components` | @nextcloud/vue component library; NcButton, NcDialog, NcAppContent, NcAppNavigation; Nextcloud design patterns | @nextcloud/vue components, slots, props | M |
| `nextcloud-syntax-frontend-data` | Frontend data fetching; @nextcloud/axios; DAV client (@nextcloud/cdav-library); @nextcloud/router; initial state | @nextcloud/axios, generateUrl, getInitialState | M |

### nextcloud-impl/ (8 skills)

| Name | Scope | Key APIs | Complexity |
|------|-------|----------|------------|
| `nextcloud-impl-app-scaffold` | App directory structure; info.xml manifest; appinfo/routes.php; lib/ structure; src/ frontend; Application.php bootstrap | info.xml, Application::register(), IBootstrap | M |
| `nextcloud-impl-app-development` | Full-stack app development workflow; controller + service + mapper + Vue.js; API endpoint creation; frontend integration | Full stack: PHP controllers → Vue.js components | L |
| `nextcloud-impl-background-jobs` | Background jobs; IJob types (QueuedJob, TimedJob, Job); cron configuration; job registration; error handling | IJobList, QueuedJob, TimedJob, registerJobClasses | M |
| `nextcloud-impl-occ-commands` | Custom OCC console commands; built-in commands reference; command registration; input/output; interactive commands | Command, InputInterface, OutputInterface | M |
| `nextcloud-impl-file-operations` | File handling; Node API; IRootFolder/IUserFolder; File/Folder interfaces; storage wrappers; versioning; trash | IRootFolder, IUserFolder, File, Folder, IStorage | L |
| `nextcloud-impl-sharing` | Share API; OCS share endpoints; share types; permission bitmask; public links; federated sharing; share creation flow | IShare, IShareManager, share permissions constants | L |
| `nextcloud-impl-notifications` | Notification API; creating notifications; push notifications; notification actions; activity providers; activity events | INotificationManager, INotification, IActivityManager | M |
| `nextcloud-impl-testing` | PHPUnit testing; integration tests; frontend testing; test base classes; database transaction rollback | TestCase, OCSControllerTest, mock patterns | M |

### nextcloud-errors/ (4 skills)

| Name | Scope | Key APIs | Complexity |
|------|-------|----------|------------|
| `nextcloud-errors-api` | OCS error codes; DAV error responses; HTTP status mapping; common API mistakes; response debugging | OCS status codes, DAV error XML, HTTP 4xx/5xx | M |
| `nextcloud-errors-app` | App registration failures; autoloading; namespace issues; info.xml problems; migration failures; dependency conflicts | AppManager errors, composer autoload, migrations | M |
| `nextcloud-errors-database` | Migration errors; query builder mistakes; entity mapping issues; type mismatches; performance anti-patterns | Migration exceptions, QB errors, mapper errors | M |
| `nextcloud-errors-frontend` | Vue compilation errors; import path issues; CORS problems; CSRF token failures; @nextcloud/* version mismatches | Webpack errors, CSRF errors, CORS headers | M |

### nextcloud-agents/ (2 skills)

| Name | Scope | Key APIs | Complexity |
|------|-------|----------|------------|
| `nextcloud-agents-review` | Validation checklist for Nextcloud code; API correctness; permission handling; anti-pattern detection; NC 28+ compliance | All validation rules | M |
| `nextcloud-agents-app-scaffolder` | Generate complete Nextcloud app structure; PHP backend + Vue.js frontend; info.xml; routes; controllers; database | All scaffolding patterns | L |

---

## Category Summary

| Category | Count | Purpose |
|----------|-------|---------|
| nextcloud-core/ | 3 | Architecture, configuration, security model |
| nextcloud-syntax/ | 8 | API syntax, code patterns, component usage |
| nextcloud-impl/ | 8 | Development workflows, step-by-step guides |
| nextcloud-errors/ | 4 | Error handling, debugging, anti-patterns |
| nextcloud-agents/ | 2 | Validation, code generation |
| **Total** | **25** | |

---

## Batch Execution Plan (PRELIMINARY — will be refined in Phase 3)

| Batch | Skills | Count | Dependencies | Notes |
|-------|--------|-------|-------------|-------|
| 1 | `core-architecture`, `core-config` | 2 | None | Foundation, no deps |
| 2 | `core-security`, `syntax-ocs-api`, `syntax-webdav` | 3 | Batch 1 | Security model + primary APIs |
| 3 | `syntax-controllers`, `syntax-database`, `syntax-services` | 3 | Batch 1 | PHP backend patterns |
| 4 | `syntax-events`, `syntax-vue-components`, `syntax-frontend-data` | 3 | Batch 1 | Event system + frontend |
| 5 | `impl-app-scaffold`, `impl-app-development`, `impl-testing` | 3 | Batch 1-4 | App dev workflow |
| 6 | `impl-background-jobs`, `impl-occ-commands`, `impl-file-operations` | 3 | Batch 1-3 | Server-side impl |
| 7 | `impl-sharing`, `impl-notifications` | 2 | Batch 2, 6 | Collaboration features |
| 8 | `errors-api`, `errors-app`, `errors-database` | 3 | Batch 2-6 | Error handling |
| 9 | `errors-frontend`, `agents-review` | 2 | Batch 4, ALL | Frontend errors + review agent |
| 10 | `agents-app-scaffolder` | 1 | ALL | Scaffolding agent last |

**Total**: 25 skills across 10 batches.

---

## Phase 2 Research Topics

The vooronderzoek must cover these areas (matching REQUIREMENTS.md):

1. **Platform Architecture** — NC server structure, PHP backend, Vue.js frontend, data directory
2. **OCS API** — All OCS v2 endpoints, authentication, response format, versioning
3. **WebDAV** — File DAV, CalDAV, CardDAV endpoints, properties, namespaces, chunked upload
4. **App Framework** — App structure, controllers, services, DI, routing, middleware, Application bootstrap
5. **Database Layer** — Migrations, entities, QBMapper, query builder, types
6. **Event System** — Typed events, listeners, deprecated hooks, BeforeNode/AfterNode
7. **Vue.js Frontend** — @nextcloud/vue components, @nextcloud/axios, router, initial state, Webpack
8. **Authentication & Security** — Login flow v2, app passwords, CSRF, rate limiting, CSP, middleware
9. **File Handling** — IRootFolder, IUserFolder, Node API, storage, versioning, trash
10. **Collaboration** — Sharing API, notifications, activity, Talk integration points
11. **Server Administration** — config.php, occ commands, background jobs, logging
12. **Testing** — PHPUnit, integration tests, frontend tests
13. **Anti-Patterns** — Common mistakes from GitHub issues and forums

---

## Next Steps

1. ~~Phase 1: Create raw masterplan~~ DONE
2. Phase 2: Deep research (vooronderzoek) — delegate to research agents
3. Phase 3: Refine masterplan based on research findings
4. Phase 4-5: Topic research + skill creation in batches
5. Phase 6: Validation pass
6. Phase 7: Publication

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
│   └── nextcloud-core-security/
├── nextcloud-syntax/
│   ├── nextcloud-syntax-ocs-api/
│   ├── nextcloud-syntax-webdav/
│   ├── nextcloud-syntax-controllers/
│   ├── nextcloud-syntax-database/
│   ├── nextcloud-syntax-services/
│   ├── nextcloud-syntax-events/
│   ├── nextcloud-syntax-vue-components/
│   └── nextcloud-syntax-frontend-data/
├── nextcloud-impl/
│   ├── nextcloud-impl-app-scaffold/
│   ├── nextcloud-impl-app-development/
│   ├── nextcloud-impl-background-jobs/
│   ├── nextcloud-impl-occ-commands/
│   ├── nextcloud-impl-file-operations/
│   ├── nextcloud-impl-sharing/
│   ├── nextcloud-impl-notifications/
│   └── nextcloud-impl-testing/
├── nextcloud-errors/
│   ├── nextcloud-errors-api/
│   ├── nextcloud-errors-app/
│   ├── nextcloud-errors-database/
│   └── nextcloud-errors-frontend/
└── nextcloud-agents/
    ├── nextcloud-agents-review/
    └── nextcloud-agents-app-scaffolder/
```
