---
name: nextcloud-core-architecture
description: >
  Use when creating Nextcloud apps, understanding the platform architecture, or configuring dependency injection.
  Prevents misuse of IBootstrap phases, incorrect DI wiring, and violating the OCP interface contract.
  Covers PHP backend structure, Vue.js frontend layer, app lifecycle with IBootstrap register/boot phases, dependency injection with auto-wiring, service layer patterns, and key OCP interfaces.
  Keywords: IBootstrap, register, boot, OCP, dependency injection, auto-wiring, service layer, Application.php, how Nextcloud works, app structure, DI container, lifecycle phases, getting started..
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

# nextcloud-core-architecture

## Quick Reference

### Architecture Layers (NC 28+)

| Layer | Technology | Location | Role |
|-------|-----------|----------|------|
| PHP Backend | PHP 8.1+ | `lib/` | Controllers, services, database, business logic |
| Vue.js Frontend | Vue 2 (v8.x) / Vue 3 (v9.x) | `src/` | Single-page app UI with `@nextcloud/vue` components |
| Data Directory | Filesystem | `data/` | User files, app data, logs |
| Apps Directory | PHP + JS | `apps/` / `apps-extra/` | Modular app extensions |
| OCS API | REST + JSON/XML | `/ocs/v2.php/` | Structured API with envelope responses |
| WebDAV | RFC 4918 | `/remote.php/dav/` | File, calendar, and contact operations |

### Key Dependencies

| Package | Type | Purpose |
|---------|------|---------|
| `@nextcloud/vue` | npm | Vue.js component library (NC UI kit) |
| `@nextcloud/axios` | npm | Authenticated HTTP client |
| `@nextcloud/router` | npm | URL generation (`generateUrl`, `generateOcsUrl`) |
| `@nextcloud/initial-state` | npm | Server-to-client data transfer |
| `@nextcloud/event-bus` | npm | Frontend cross-component events |
| `@nextcloud/webpack-vue-config` | npm (dev) | Pre-configured webpack base |

### Critical Warnings

**NEVER** query services from other apps inside `register()` -- they may not be registered yet. ALWAYS use `boot()` for cross-app service dependencies.

**NEVER** omit the `<namespace>` element in `appinfo/info.xml` -- auto-wiring will silently fail because the DI container cannot map `OCA\{Namespace}\*` classes to the `lib/` directory.

**NEVER** use `\OCP\Server::get()` for service resolution in new code -- it is a service locator anti-pattern that breaks testability. ALWAYS use constructor injection.

**NEVER** use `OCP\ILogger` -- deprecated since NC 24. ALWAYS inject `Psr\Log\LoggerInterface` instead.

**NEVER** put business logic in `Application.php` -- keep it in `Service/` classes. `Application.php` MUST only contain registration and boot wiring.

**NEVER** perform I/O or side effects in constructors -- constructors MUST only assign dependencies.

---

## Request Lifecycle

All HTTP requests follow this path:

```
index.php
  -> lib/base.php (init: auth backends, filesystem, logging)
    -> Load all enabled apps (appinfo/info.xml)
    -> Load navigation and pre-config files
    -> Load route definitions (appinfo/routes.php)
    -> Router matches URL to Controller method
      -> Middleware chain (beforeController -> controller -> afterController)
        -> Response rendered and returned
```

1. `index.php` loads `lib/base.php`, which abstracts web server differences and initializes core classes
2. Authentication backends, filesystem, and logging are bootstrapped
3. Each installed app is loaded based on its `appinfo/info.xml`
4. Route definitions from each app's `appinfo/routes.php` are loaded
5. The router matches the incoming URL to a controller method
6. The middleware chain processes the request and response

---

## App Lifecycle: IBootstrap

The `Application` class in `lib/AppInfo/Application.php` implements `IBootstrap` for a two-phase lifecycle:

### Phase 1: register() -- Lazy Registration

Called during app loading. ONLY use `IRegistrationContext` methods here:

```php
public function register(IRegistrationContext $context): void {
    $context->registerMiddleware(MyMiddleware::class);
    $context->registerServiceAlias(IMyInterface::class, MyImplementation::class);
    $context->registerEventListener(ItemCreatedEvent::class, ItemCreatedListener::class);
    $context->registerParameter('TableName', 'my_app_table');
}
```

### Phase 2: boot() -- Post-Registration Initialization

Called after ALL apps have completed `register()`. All services are now available:

```php
public function boot(IBootContext $context): void {
    $context->injectFn(function (IFooManager $manager) {
        $manager->registerCustomFoo(MyFooImpl::class);
    });
}
```

### Bootstrap Sequence

1. Nextcloud scans enabled apps for `lib/AppInfo/Application.php`
2. Apps with `IBootstrap` -> `register()` called (in app dependency order)
3. App load groups processed (filesystem, session, etc.)
4. All `Application` classes fully instantiated
5. All `boot()` methods called -- prior registrations guaranteed complete
6. Request routing begins

---

## Dependency Injection

Nextcloud uses auto-wiring as the primary DI mechanism (PSR-11 compatible container).

### How Auto-Wiring Resolves Parameters

1. **Type hints**: `SomeType $param` resolves via `$container->get(SomeType::class)`
2. **Parameter names**: `$variable` resolves via `$container->get('variable')`

### Predefined Parameters

| Parameter | Type | Value |
|-----------|------|-------|
| `$appName` | `string` | Application ID |
| `$userId` | `?string` | Current user ID (null if no session) |
| `$webRoot` | `string` | Nextcloud installation path |

### Auto-Wiring Requirements

1. `<namespace>` MUST be declared in `appinfo/info.xml`
2. Array-style routes in `appinfo/routes.php`
3. Constructor parameters MUST have type hints

### IRegistrationContext Methods

| Method | Purpose |
|--------|---------|
| `registerService(string $class, Closure $factory)` | Explicit factory registration |
| `registerParameter(string $name, $value)` | Register primitive values |
| `registerServiceAlias(string $interface, string $impl)` | Interface-to-implementation binding |
| `registerEventListener(string $event, string $listener)` | Event listener registration |
| `registerMiddleware(string $class, bool $global = false)` | Middleware registration |

### Optional Dependencies (NC 28+)

Use nullable types for services that may not exist:

```php
class MyService {
    public function __construct(private ?SomeOptionalService $service) { }
}
```

---

## Key OCP Interfaces

| Interface | Purpose |
|-----------|---------|
| `OCP\AppFramework\App` | Base class for app entry point (`Application`) |
| `OCP\AppFramework\Bootstrap\IBootstrap` | Two-phase app lifecycle (register/boot) |
| `OCP\AppFramework\Bootstrap\IRegistrationContext` | Service registration during app loading |
| `OCP\AppFramework\Bootstrap\IBootContext` | Runtime operations after all apps registered |
| `OCP\IDBConnection` | Database abstraction (MySQL, PostgreSQL, SQLite, Oracle) |
| `OCP\IRequest` | HTTP request abstraction |
| `OCP\IConfig` | Server and app configuration |
| `OCP\IAppConfig` | App-specific configuration |
| `OCP\IUserManager` | User CRUD operations |
| `OCP\IUserSession` | Current user session management |
| `OCP\Files\IRootFolder` | Filesystem root access |
| `OCP\IURLGenerator` | URL generation for routes and assets |
| `OCP\ICacheFactory` | Cache factory |
| `OCP\Security\ICrypto` | Cryptographic operations |
| `OCP\IL10N` | Localization/translation |
| `OCP\AppFramework\Services\IInitialState` | Server-to-frontend state transfer |
| `OCP\EventDispatcher\IEventDispatcher` | Event dispatch service |
| `Psr\Log\LoggerInterface` | PSR-3 compliant logging (ALWAYS use this) |
| `Psr\Container\ContainerInterface` | PSR-11 DI container |

---

## Namespace Conventions

The `<namespace>` element in `info.xml` determines the `OCA\{Namespace}` prefix. Nextcloud's autoloader maps this to the `lib/` directory:

| info.xml namespace | PHP namespace | File path |
|-------------------|---------------|-----------|
| `<namespace>MyApp</namespace>` | `OCA\MyApp\AppInfo\Application` | `lib/AppInfo/Application.php` |
| | `OCA\MyApp\Controller\PageController` | `lib/Controller/PageController.php` |
| | `OCA\MyApp\Service\ItemService` | `lib/Service/ItemService.php` |
| | `OCA\MyApp\Db\ItemMapper` | `lib/Db/ItemMapper.php` |
| | `OCA\MyApp\Listener\ItemListener` | `lib/Listener/ItemListener.php` |

---

## Project Structure

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
│   ├── main.js                # Vue app entry point
│   ├── App.vue                # Root Vue component
│   ├── components/            # Reusable Vue components
│   ├── views/                 # Page-level components
│   ├── store/                 # Vuex/Pinia store
│   └── services/              # API service layer
├── css/                       # Stylesheets (CSS/SCSS)
├── img/                       # Icons (app.svg = app icon)
├── js/                        # Compiled JS output (generated)
├── templates/                 # PHP templates
├── tests/                     # PHPUnit tests
├── l10n/                      # Translation files
├── webpack.config.js          # Build configuration
└── package.json               # NPM dependencies
```

### Source Control Rules

- **ALWAYS commit**: `composer.lock`, `package-lock.json` (deterministic builds)
- **ALWAYS ignore**: `vendor/`, `node_modules/`, `js/` (build artifacts)
- **NEVER edit**: generated files in `js/` directory

---

## Reference Links

- [references/methods.md](references/methods.md) -- Key interfaces: App, IBootstrap, IRegistrationContext, IServerContainer, core services
- [references/examples.md](references/examples.md) -- Application.php, DI patterns, service layer examples
- [references/anti-patterns.md](references/anti-patterns.md) -- DI mistakes, bootstrap errors, common pitfalls

### Official Sources

- https://docs.nextcloud.com/server/latest/developer_manual/app_development/intro.html
- https://docs.nextcloud.com/server/latest/developer_manual/app_development/bootstrap.html
- https://docs.nextcloud.com/server/latest/developer_manual/basics/dependency_injection.html
- https://docs.nextcloud.com/server/latest/developer_manual/app_development/info.html
