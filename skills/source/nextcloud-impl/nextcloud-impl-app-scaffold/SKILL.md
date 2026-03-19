---
name: nextcloud-impl-app-scaffold
description: >
  Use when creating a new Nextcloud app, setting up info.xml, configuring Application.php, or understanding app directory layout.
  Prevents incorrect info.xml fields, wrong namespace conventions, and missing IBootstrap implementation.
  Covers directory structure conventions, info.xml manifest with all fields and constraints, Application.php with IBootstrap lifecycle, namespace conventions and autoloading, and the official app generator.
  Keywords: info.xml, Application.php, IBootstrap, app scaffold, namespace, autoloading, app generator, appinfo.
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

# nextcloud-impl-app-scaffold

## Quick Reference

### App Directory Layout

```
myapp/
├── appinfo/
│   ├── info.xml              # App manifest (REQUIRED)
│   └── routes.php            # Route definitions
├── lib/
│   ├── AppInfo/
│   │   └── Application.php   # Bootstrap entry point (IBootstrap)
│   ├── Controller/            # HTTP controllers
│   ├── Service/               # Business logic layer
│   ├── Db/                    # Entity classes and mappers
│   ├── Listener/              # Event listeners
│   ├── Middleware/             # Request middleware
│   ├── Migration/             # Database migrations
│   └── Command/               # OCC CLI commands
├── src/                       # Vue.js frontend source
│   ├── main.js
│   ├── App.vue
│   └── components/
├── css/                       # Stylesheets (CSS/SCSS)
├── img/
│   └── app.svg               # App icon (used as navigation icon)
├── js/                        # Compiled JS output (generated)
├── templates/                 # PHP templates
│   └── main.php
├── tests/                     # PHPUnit tests
├── l10n/                      # Translation files
├── webpack.config.js
├── package.json
├── composer.json
└── LICENSE
```

### info.xml Required Fields

| Field | Constraint |
|-------|-----------|
| `id` | Lowercase ASCII + underscore only, MUST match app directory name |
| `name` | Human-readable app name |
| `summary` | Short description for app store listing |
| `description` | Full description, supports Markdown via `<![CDATA[]]>` |
| `version` | Semantic versioning (no build metadata) |
| `licence` | SPDX identifier (`AGPL-3.0-or-later`, `MIT`, etc.) |
| `author` | Developer name, optional `mail` and `homepage` attributes |
| `namespace` | PascalCase, maps to `OCA\{Namespace}\` PHP namespace |
| `category` | One of: customization, files, games, integration, monitoring, multimedia, office, organization, security, social, tools |
| `dependencies/nextcloud` | BOTH `min-version` AND `max-version` required |

### info.xml Optional Fields

| Field | Purpose |
|-------|---------|
| `bugs` | Issue tracker URL |
| `repository` | Source code URL (with `type` attribute) |
| `website` | Project homepage |
| `screenshot` | App store screenshot (HTTPS required), optional `small-thumbnail` |
| `documentation` | Child elements: `user`, `admin`, `developer` |
| `navigations/navigation` | Top-level navigation entry |
| `background-jobs/job` | Cron job class registrations |
| `repair-steps` | Install/post-migration/uninstall repair steps |
| `commands/command` | OCC CLI command registrations |
| `settings` | Admin/personal settings page classes |
| `activity` | Activity app integration (settings + providers) |

### Deprecated info.xml Fields (NEVER Use)

These fields cause app store validation failure:
`standalone`, `default_enable`, `shipped`, `public`, `remote`, `requiremin`, `requiremax`

### Namespace to File Path Mapping

| info.xml `<namespace>` | PHP Class | File Path |
|------------------------|-----------|-----------|
| `MyApp` | `OCA\MyApp\AppInfo\Application` | `lib/AppInfo/Application.php` |
| `MyApp` | `OCA\MyApp\Controller\PageController` | `lib/Controller/PageController.php` |
| `MyApp` | `OCA\MyApp\Service\ItemService` | `lib/Service/ItemService.php` |
| `MyApp` | `OCA\MyApp\Db\ItemMapper` | `lib/Db/ItemMapper.php` |
| `MyApp` | `OCA\MyApp\Listener\MyListener` | `lib/Listener/MyListener.php` |
| `MyApp` | `OCA\MyApp\Migration\Version1000Date` | `lib/Migration/Version1000Date.php` |

### IBootstrap Lifecycle

| Phase | Method | When Called | Rules |
|-------|--------|------------|-------|
| 1 | `register(IRegistrationContext $context)` | Early, before all apps loaded | ONLY use `$context` API methods. NEVER query services. |
| 2 | `boot(IBootContext $context)` | After ALL apps completed `register()` | All services available. Use `$context->injectFn()` for DI. |

### Valid Category Values

`customization` | `files` | `games` | `integration` | `monitoring` | `multimedia` | `office` | `organization` | `security` | `social` | `tools`

---

## Critical Warnings

**ALWAYS** include `<namespace>` in `info.xml` -- the autoloader and DI container depend on it to map `OCA\{Namespace}\*` to the `lib/` directory.

**ALWAYS** set both `min-version` and `max-version` in `<dependencies><nextcloud>` -- both are required for app store validation.

**ALWAYS** implement `IBootstrap` in `Application.php` for NC 28+ apps -- legacy constructor-based service resolution is deprecated.

**ALWAYS** use `register()` for event listeners, middleware, and service aliases -- these are lazily resolved.

**ALWAYS** place `Application.php` at `lib/AppInfo/Application.php` -- Nextcloud expects this exact path.

**ALWAYS** use the `app.svg` file in `img/` as the app icon -- Nextcloud uses it automatically for navigation and favicons.

**NEVER** query services or resolve dependencies in `register()` -- other apps may not have completed their registration yet.

**NEVER** put business logic in `Application.php` -- keep it in `Service/` classes. Application.php handles only registration and boot wiring.

**NEVER** use `database.xml` for new apps -- use PHP migration classes in `lib/Migration/` instead.

**NEVER** use deprecated `requiremin`/`requiremax` -- use `<dependencies><nextcloud min-version="" max-version=""/>`.

**NEVER** include sensitive data (API keys, passwords) in `info.xml` -- it is publicly readable.

**NEVER** omit the `id` field or use characters other than lowercase ASCII and underscores.

---

## Essential Patterns

### Pattern 1: Minimal info.xml

```xml
<?xml version="1.0"?>
<info xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:noNamespaceSchemaLocation="https://apps.nextcloud.com/schema/apps/info.xsd">
    <id>myapp</id>
    <name>My Application</name>
    <summary>Short description for app listing</summary>
    <description>Full description with **Markdown** support</description>
    <version>1.0.0</version>
    <licence>AGPL-3.0-or-later</licence>
    <author mail="dev@example.com">Developer Name</author>
    <namespace>MyApp</namespace>
    <category>tools</category>
    <bugs>https://github.com/org/myapp/issues</bugs>
    <dependencies>
        <nextcloud min-version="28" max-version="32"/>
        <php min-version="8.1"/>
    </dependencies>
</info>
```

### Pattern 2: Application.php with IBootstrap

```php
<?php
declare(strict_types=1);

namespace OCA\MyApp\AppInfo;

use OCA\MyApp\Listener\UserDeletedListener;
use OCA\MyApp\Middleware\AuthMiddleware;
use OCP\AppFramework\App;
use OCP\AppFramework\Bootstrap\IBootstrap;
use OCP\AppFramework\Bootstrap\IBootContext;
use OCP\AppFramework\Bootstrap\IRegistrationContext;
use OCP\User\Events\BeforeUserDeletedEvent;

class Application extends App implements IBootstrap {
    public const APP_ID = 'myapp';

    public function __construct() {
        parent::__construct(self::APP_ID);
    }

    public function register(IRegistrationContext $context): void {
        // Event listeners (lazily resolved via DI)
        $context->registerEventListener(
            BeforeUserDeletedEvent::class,
            UserDeletedListener::class
        );

        // Middleware
        $context->registerMiddleware(AuthMiddleware::class);

        // Interface binding (only when auto-wiring is insufficient)
        $context->registerServiceAlias(IMyInterface::class, MyImplementation::class);
    }

    public function boot(IBootContext $context): void {
        // Post-registration initialization
        // All services from all apps are now available
        $context->injectFn(function (IFooManager $manager) {
            $manager->registerProvider(MyProvider::class);
        });
    }
}
```

### Pattern 3: Navigation Entry in info.xml

```xml
<navigations>
    <navigation>
        <name>My App</name>
        <route>myapp.page.index</route>
        <icon>app.svg</icon>
        <order>10</order>
    </navigation>
</navigations>
```

The `route` value uses the format `{appid}.{controller}.{method}` -- it MUST match a route defined in `appinfo/routes.php`.

### Pattern 4: Minimal routes.php

```php
<?php
return [
    'routes' => [
        ['name' => 'page#index', 'url' => '/', 'verb' => 'GET'],
    ],
];
```

### Pattern 5: Minimal PHP Template

```php
<!-- templates/main.php -->
<?php
script('myapp', 'myapp-main');  // loads js/myapp-main.js
style('myapp', 'style');         // loads css/style.(s)css
?>

<div id="app-content">
    <div id="content"></div>
</div>
```

### Pattern 6: App Generator

Use the official Nextcloud app generator to scaffold a new app:

**URL:** https://apps.nextcloud.com/developer/apps/generate

This generates a downloadable skeleton with correct directory structure, info.xml, Application.php, basic controller, routes, and build configuration. It does NOT publish to the app store.

---

## Decision Tree: Starting a New App

```
Need a new Nextcloud app?
├── Use the app generator → https://apps.nextcloud.com/developer/apps/generate
│   └── Download and customize the skeleton
├── OR create manually:
│   ├── 1. Create appinfo/info.xml with ALL required fields
│   ├── 2. Create lib/AppInfo/Application.php implementing IBootstrap
│   ├── 3. Create appinfo/routes.php with at least one route
│   ├── 4. Create lib/Controller/ with your first controller
│   ├── 5. Create templates/main.php for the page template
│   └── 6. Place app.svg in img/ for the app icon
│
├── Need a navigation entry?
│   └── Add <navigations> to info.xml with route matching routes.php
│
├── Need background jobs?
│   └── Add <background-jobs> to info.xml + create Job class in lib/Cron/
│
├── Need database tables?
│   └── Create migration class in lib/Migration/ (NEVER use database.xml)
│
├── Need admin settings?
│   └── Add <settings> to info.xml + create Settings class in lib/Settings/
│
└── Need OCC commands?
    └── Add <commands> to info.xml + create Command class in lib/Command/
```

---

## Bootstrap Sequence (NC 28+)

1. Nextcloud scans enabled apps for `lib/AppInfo/Application.php`
2. Apps implementing `IBootstrap` have `register()` called (ordered by app dependencies)
3. App load groups processed (filesystem, session, etc.) in priority order
4. All `Application` classes fully instantiated
5. All `boot()` methods called -- all prior registrations are guaranteed complete
6. Request routing begins

---

## Reference Links

- [references/methods.md](references/methods.md) -- info.xml fields, Application.php API, namespace mapping
- [references/examples.md](references/examples.md) -- Complete info.xml, Application.php, directory structure
- [references/anti-patterns.md](references/anti-patterns.md) -- Scaffold mistakes

### Official Sources

- https://docs.nextcloud.com/server/latest/developer_manual/app_development/info.html
- https://docs.nextcloud.com/server/latest/developer_manual/app_development/bootstrap.html
- https://docs.nextcloud.com/server/latest/developer_manual/app_development/intro.html
- https://docs.nextcloud.com/server/latest/developer_manual/basics/dependency_injection.html
- https://apps.nextcloud.com/developer/apps/generate
