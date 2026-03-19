# Skill Index — Nextcloud Claude Skill Package

24 deterministic skills for Nextcloud development (NC 28+).

---

## Core (3 skills)

| Skill | Description |
|-------|-------------|
| [nextcloud-core-architecture](skills/source/nextcloud-core/nextcloud-core-architecture/SKILL.md) | Platform architecture, app lifecycle (IBootstrap), DI container, service layer, key interfaces |
| [nextcloud-core-config](skills/source/nextcloud-core/nextcloud-core-config/SKILL.md) | config.php reference, IConfig/IAppConfig, occ config commands, environment variables, caching |
| [nextcloud-core-security](skills/source/nextcloud-core/nextcloud-core-security/SKILL.md) | Security model, middleware chain, CSP, rate limiting architecture, encryption |

## Syntax (8 skills)

| Skill | Description |
|-------|-------------|
| [nextcloud-syntax-ocs-api](skills/source/nextcloud-syntax/nextcloud-syntax-ocs-api/SKILL.md) | OCS REST API endpoints, v1 vs v2, response envelope, share API, capabilities |
| [nextcloud-syntax-webdav](skills/source/nextcloud-syntax/nextcloud-syntax-webdav/SKILL.md) | DAV file operations, PROPFIND/GET/PUT/MKCOL/MOVE/COPY/DELETE, chunked upload v2 |
| [nextcloud-syntax-controllers](skills/source/nextcloud-syntax/nextcloud-syntax-controllers/SKILL.md) | Controller types, routes.php, attribute-based routing, security attributes, response types |
| [nextcloud-syntax-database](skills/source/nextcloud-syntax/nextcloud-syntax-database/SKILL.md) | Migrations, Entity, QBMapper, query builder, TTransactional, Oracle/Galera constraints |
| [nextcloud-syntax-events](skills/source/nextcloud-syntax/nextcloud-syntax-events/SKILL.md) | IEventDispatcher, typed events, IEventListener, built-in events catalog, frontend event-bus |
| [nextcloud-syntax-authentication](skills/source/nextcloud-syntax/nextcloud-syntax-authentication/SKILL.md) | Login Flow v2, app passwords, CSRF, rate limiting, brute force protection |
| [nextcloud-syntax-frontend](skills/source/nextcloud-syntax/nextcloud-syntax-frontend/SKILL.md) | @nextcloud/vue, axios, router, initial-state, dialogs, files, Webpack, CSS theming |
| [nextcloud-syntax-file-api](skills/source/nextcloud-syntax/nextcloud-syntax-file-api/SKILL.md) | IRootFolder, File/Folder interfaces, file events, getById() patterns, storage access |

## Implementation (7 skills)

| Skill | Description |
|-------|-------------|
| [nextcloud-impl-app-scaffold](skills/source/nextcloud-impl/nextcloud-impl-app-scaffold/SKILL.md) | App directory structure, info.xml, Application.php, IBootstrap lifecycle, namespaces |
| [nextcloud-impl-app-development](skills/source/nextcloud-impl/nextcloud-impl-app-development/SKILL.md) | Full-stack workflow: Controller → Service → Mapper → Vue.js, initial state bridge |
| [nextcloud-impl-background-jobs](skills/source/nextcloud-impl/nextcloud-impl-background-jobs/SKILL.md) | TimedJob, QueuedJob, cron modes, scheduleAfter, parallel run control |
| [nextcloud-impl-occ-commands](skills/source/nextcloud-impl/nextcloud-impl-occ-commands/SKILL.md) | Built-in occ commands, custom Symfony Console commands, arguments/options |
| [nextcloud-impl-collaboration](skills/source/nextcloud-impl/nextcloud-impl-collaboration/SKILL.md) | Share API CRUD, notifications (INotifier), activity stream, push notifications |
| [nextcloud-impl-testing](skills/source/nextcloud-impl/nextcloud-impl-testing/SKILL.md) | PHPUnit setup, unit/integration tests, mocking NC services, Vue Test Utils |
| [nextcloud-impl-file-operations](skills/source/nextcloud-impl/nextcloud-impl-file-operations/SKILL.md) | File CRUD workflows, search, event-driven processing, trash, versioning |

## Errors (4 skills)

| Skill | Description |
|-------|-------------|
| [nextcloud-errors-api](skills/source/nextcloud-errors/nextcloud-errors-api/SKILL.md) | OCS v1/v2 status confusion, missing headers, DAV errors, auth failures, CORS |
| [nextcloud-errors-app](skills/source/nextcloud-errors/nextcloud-errors-app/SKILL.md) | Namespace/autoloading, info.xml, migration errors, bootstrap timing, DI failures |
| [nextcloud-errors-database](skills/source/nextcloud-errors/nextcloud-errors-database/SKILL.md) | Migration failures, query builder mistakes, Oracle/Galera constraints, entity mapping |
| [nextcloud-errors-frontend](skills/source/nextcloud-errors/nextcloud-errors-frontend/SKILL.md) | Vue/Webpack errors, CSRF/CORS, import paths, version mismatches, deprecated globals |

## Agents (2 skills)

| Skill | Description |
|-------|-------------|
| [nextcloud-agents-review](skills/source/nextcloud-agents/nextcloud-agents-review/SKILL.md) | 8-area validation checklist for generated Nextcloud code, 34 anti-patterns |
| [nextcloud-agents-app-scaffolder](skills/source/nextcloud-agents/nextcloud-agents-app-scaffolder/SKILL.md) | Generates complete Nextcloud app with 20+ file templates, feature selection |
