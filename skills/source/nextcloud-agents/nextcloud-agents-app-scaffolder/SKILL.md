---
name: nextcloud-agents-app-scaffolder
description: "Generates complete Nextcloud app structure including PHP backend with controllers, services, entities and mappers, Vue.js frontend with @nextcloud packages, info.xml manifest, routes.php, database migrations, Application.php bootstrap, webpack configuration, and test infrastructure. Activates when generating a new Nextcloud app from scratch, scaffolding app features, or creating a complete app template."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

# nextcloud-agents-app-scaffolder

## Purpose

This agent skill guides Claude through generating a complete, production-ready Nextcloud app from scratch. It produces all required files with correct patterns, ensuring the generated code follows every convention from the Nextcloud developer manual.

## Quick Reference: Generated File Tree

```
{appid}/
├── appinfo/
│   ├── info.xml              # App manifest
│   └── routes.php            # Route definitions
├── lib/
│   ├── AppInfo/
│   │   └── Application.php   # IBootstrap entry point
│   ├── Controller/
│   │   ├── PageController.php    # Frontend page serving
│   │   └── ApiController.php     # OCS API endpoints (if needed)
│   ├── Service/
│   │   └── {Entity}Service.php   # Business logic
│   ├── Db/
│   │   ├── {Entity}.php          # Entity class
│   │   └── {Entity}Mapper.php    # QBMapper
│   ├── Listener/                  # Event listeners (if needed)
│   ├── Middleware/                 # Custom middleware (if needed)
│   └── Migration/
│       └── Version1000Date{timestamp}.php  # Initial schema
├── src/
│   ├── main.js               # Vue app entry point
│   ├── App.vue               # Root Vue component
│   ├── components/            # Reusable components
│   ├── views/                 # Page-level components
│   └── services/              # Frontend API layer
├── css/
│   └── style.scss            # App styles using CSS variables
├── img/
│   └── app.svg               # App icon (REQUIRED)
├── templates/
│   └── main.php              # PHP template mounting Vue
├── tests/
│   ├── Unit/
│   │   └── Service/
│   │       └── {Entity}ServiceTest.php
│   └── bootstrap.php
├── webpack.config.js
├── package.json
├── composer.json
├── phpunit.xml
└── LICENSE
```

---

## Feature Selection Decision Tree

```
Scaffolding a new Nextcloud app?
│
├── What does the app need?
│   │
│   ├── Database storage?
│   │   ├── YES → Generate: Migration, Entity, Mapper, Service
│   │   └── NO  → Skip Db/ and Migration/ directories
│   │
│   ├── Vue.js frontend?
│   │   ├── YES → Generate: src/, webpack.config.js, package.json, templates/main.php
│   │   └── NO  → Skip src/, webpack.config.js, package.json
│   │
│   ├── OCS API endpoints?
│   │   ├── YES → Generate: ApiController (extends OCSController), add 'ocs' routes
│   │   └── NO  → Only generate PageController with standard routes
│   │
│   ├── Navigation entry?
│   │   ├── YES → Add <navigations> to info.xml
│   │   └── NO  → Skip navigations section
│   │
│   ├── Background jobs?
│   │   ├── YES → Generate: lib/Cron/ job class, add <background-jobs> to info.xml
│   │   └── NO  → Skip background jobs
│   │
│   ├── Admin settings page?
│   │   ├── YES → Generate: lib/Settings/ classes, add <settings> to info.xml
│   │   └── NO  → Skip settings
│   │
│   ├── OCC commands?
│   │   ├── YES → Generate: lib/Command/ class, add <commands> to info.xml
│   │   └── NO  → Skip commands
│   │
│   └── Event listeners?
│       ├── YES → Generate: lib/Listener/ class, register in Application.php
│       └── NO  → Skip listeners
│
└── ALWAYS generate (mandatory):
    ├── appinfo/info.xml
    ├── appinfo/routes.php
    ├── lib/AppInfo/Application.php
    ├── lib/Controller/PageController.php
    ├── img/app.svg
    ├── composer.json
    ├── phpunit.xml
    ├── tests/bootstrap.php
    └── LICENSE
```

---

## Scaffolding Procedure

### Step 1: Collect Requirements

ALWAYS ask the user for these inputs before generating:

| Input | Required | Default |
|-------|----------|---------|
| App ID | YES | -- |
| App display name | YES | -- |
| PHP namespace | YES | PascalCase of app ID |
| Description | YES | -- |
| Author name + email | YES | -- |
| License | NO | `AGPL-3.0-or-later` |
| NC min-version | NO | `28` |
| NC max-version | NO | `32` |
| Category | NO | `tools` |
| Needs database? | NO | `true` |
| Primary entity name | If DB=yes | -- |
| Needs Vue.js frontend? | NO | `true` |
| Needs OCS API? | NO | `false` |
| Needs navigation entry? | NO | `true` |
| Needs background jobs? | NO | `false` |
| Needs admin settings? | NO | `false` |

### Step 2: Generate Mandatory Files

ALWAYS generate these files in this order:

1. `appinfo/info.xml` -- see [references/methods.md](references/methods.md) for template
2. `appinfo/routes.php` -- route definitions
3. `lib/AppInfo/Application.php` -- IBootstrap implementation
4. `lib/Controller/PageController.php` -- main page controller
5. `img/app.svg` -- placeholder app icon
6. `composer.json` -- PHP dependencies and autoloading
7. `phpunit.xml` -- test configuration
8. `tests/bootstrap.php` -- test bootstrap
9. `LICENSE` -- license file

### Step 3: Generate Conditional Files

Based on feature selection, generate applicable files from [references/methods.md](references/methods.md).

### Step 4: Validate Output

After generating all files, verify:

1. `info.xml` has ALL required fields including `<namespace>`
2. `Application.php` implements `IBootstrap` with `register()` and `boot()`
3. All controller methods have correct security attributes
4. All routes in `routes.php` match controller class + method names
5. Entity properties map to migration columns (camelCase to snake_case)
6. `package.json` includes ALL required `@nextcloud/*` packages
7. `webpack.config.js` uses `@nextcloud/webpack-vue-config`
8. Migration class name follows `Version{MajorMinor}Date{Timestamp}` pattern
9. Table names are max 23 characters (27 with `oc_` prefix for Oracle)
10. All tables have auto-increment `BIGINT` primary key

---

## Critical Rules

**ALWAYS** implement `IBootstrap` in Application.php -- NEVER use legacy constructor patterns.

**ALWAYS** include `<namespace>` in info.xml -- auto-wiring silently fails without it.

**ALWAYS** set both `min-version` and `max-version` in nextcloud dependencies.

**ALWAYS** use `declare(strict_types=1)` at the top of every PHP file.

**ALWAYS** use constructor injection for all dependencies -- NEVER use `\OCP\Server::get()`.

**ALWAYS** use `Psr\Log\LoggerInterface` -- NEVER use deprecated `OCP\ILogger`.

**ALWAYS** use `@nextcloud/axios` for HTTP requests -- NEVER use raw `fetch()` or plain `axios`.

**ALWAYS** use `@nextcloud/router` for URL generation -- NEVER use `OC.generateUrl()`.

**ALWAYS** use CSS custom properties (`--color-*`) -- NEVER hardcode colors.

**ALWAYS** use `QBMapper` with query builder -- NEVER use raw SQL.

**ALWAYS** generate `#[NoAdminRequired]` on endpoints that non-admin users need.

**ALWAYS** generate `#[NoCSRFRequired]` only on API endpoints authenticated via `OCS-APIRequest` header.

**ALWAYS** prefix table names with app ID (e.g., `myapp_items`) to avoid collisions.

**ALWAYS** use direct component imports (`@nextcloud/vue/components/NcButton`) not barrel imports.

**NEVER** generate `database.xml` -- use migration classes instead.

**NEVER** register event listeners in `boot()` -- ALWAYS use `register()`.

**NEVER** perform I/O in constructors -- constructors MUST only assign dependencies.

**NEVER** create tables without primary keys -- Galera Cluster requires them.

**NEVER** omit `parent::setUp()` in test classes extending `TestCase`.

---

## Generated Code Patterns

See [references/methods.md](references/methods.md) for all file templates.
See [references/examples.md](references/examples.md) for a complete scaffolded app.
See [references/anti-patterns.md](references/anti-patterns.md) for common mistakes.

---

## Reference Links

- [references/methods.md](references/methods.md) -- File templates and generation patterns
- [references/examples.md](references/examples.md) -- Complete scaffolded app output
- [references/anti-patterns.md](references/anti-patterns.md) -- Scaffolding mistakes to avoid

### Official Sources

- https://docs.nextcloud.com/server/latest/developer_manual/app_development/intro.html
- https://docs.nextcloud.com/server/latest/developer_manual/app_development/info.html
- https://docs.nextcloud.com/server/latest/developer_manual/app_development/bootstrap.html
- https://docs.nextcloud.com/server/latest/developer_manual/basics/dependency_injection.html
- https://docs.nextcloud.com/server/latest/developer_manual/basics/front-end/js.html
- https://docs.nextcloud.com/server/latest/developer_manual/digging_deeper/database.html
- https://apps.nextcloud.com/developer/apps/generate
