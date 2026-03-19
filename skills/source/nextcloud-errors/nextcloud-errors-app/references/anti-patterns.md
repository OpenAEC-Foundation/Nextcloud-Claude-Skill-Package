# App Development Anti-Patterns

## Namespace & Autoloading

### AP-001: Missing Namespace in info.xml

**NEVER** omit `<namespace>` from info.xml.

The autoloader depends on it to map `OCA\{Namespace}\*` to the `lib/` directory. Without it, auto-wiring silently fails and no classes are discoverable.

```xml
<!-- WRONG: No namespace -->
<info>
    <id>myapp</id>
    <name>My App</name>
</info>

<!-- CORRECT -->
<info>
    <id>myapp</id>
    <name>My App</name>
    <namespace>MyApp</namespace>
</info>
```

### AP-002: Namespace Casing Mismatch

**NEVER** use different casing between info.xml `<namespace>` and PHP `namespace` declarations.

Linux filesystems are case-sensitive. `MyApp` is not `Myapp` is not `MYAPP`.

### AP-003: Classes Outside lib/

**NEVER** place PHP classes outside the `lib/` directory and expect them to autoload.

Nextcloud's autoloader only maps `OCA\{Namespace}\*` to `{appdir}/lib/*`. Files in `src/`, `php/`, or root directory are invisible to the autoloader.

---

## info.xml Mistakes

### AP-004: Using Deprecated Fields

**NEVER** use `requiremin`, `requiremax`, `standalone`, `default_enable`, `shipped`, `public`, or `remote` in info.xml.

These fields cause app store validation failure. Use `<dependencies>` for version constraints.

### AP-005: Missing Version Bounds

**NEVER** omit `min-version` or `max-version` from the nextcloud dependency.

Both are required for app store validation. Omitting either prevents publication.

```xml
<!-- WRONG: Missing max-version -->
<dependencies>
    <nextcloud min-version="28"/>
</dependencies>

<!-- CORRECT -->
<dependencies>
    <nextcloud min-version="28" max-version="32"/>
</dependencies>
```

### AP-006: Invalid App ID Format

**NEVER** use hyphens, uppercase letters, or leading numbers in the `<id>` field.

The app ID MUST be lowercase ASCII letters and underscores only. The app ID also determines the directory name and URL paths.

---

## Migration Mistakes

### AP-007: Modifying Executed Migrations

**NEVER** edit an existing migration file after it has been deployed.

Nextcloud records which migrations have run in `oc_migrations`. Modified migrations are skipped on existing installs. ALWAYS create a new migration class.

### AP-008: Missing Existence Guards

**NEVER** call `createTable()` or `addColumn()` without checking `hasTable()` or `hasColumn()` first.

Re-enabling an app or running migrations on an existing database will crash without guards.

### AP-009: Tables Without Primary Keys

**NEVER** create database tables without primary keys.

Galera Cluster (used by many hosting providers) requires primary keys on all tables. The standard pattern is:

```php
$table->addColumn('id', Types::BIGINT, ['autoincrement' => true, 'notnull' => true]);
$table->setPrimaryKey(['id']);
```

### AP-010: Using database.xml

**NEVER** use `database.xml` (legacy XML schema) for new apps.

ALWAYS use PHP migration classes in `lib/Migration/`. The XML schema format is deprecated and lacks features like data migration and conditional logic.

### AP-011: Wrong Migration Naming

**NEVER** deviate from the naming convention `Version{MajorMinor}Date{Timestamp}`.

Nextcloud discovers and orders migrations by class name. Wrong naming causes migrations to be skipped or run out of order.

---

## Bootstrap Mistakes

### AP-012: Service Queries in register()

**NEVER** query services from other apps inside `register()`.

During `register()`, other apps may not have completed their registration. Use `boot()` with `$context->injectFn()` for cross-app service access.

```php
// WRONG
public function register(IRegistrationContext $context): void {
    $manager = \OCP\Server::get(ISomeManager::class);  // May fail
}

// CORRECT
public function boot(IBootContext $context): void {
    $context->injectFn(function (ISomeManager $manager) {
        $manager->registerProvider(MyProvider::class);
    });
}
```

### AP-013: Business Logic in Application.php

**NEVER** put business logic in Application.php.

Application.php is the bootstrap entry point for registration and wiring only. Business logic belongs in Service/ classes. The Application class is instantiated on EVERY request, so heavy logic here degrades performance.

### AP-014: Event Listeners in boot()

**NEVER** register event listeners in `boot()`.

Listeners registered in `boot()` may miss events dispatched during the boot phase of other apps. ALWAYS use `register()` with `$context->registerEventListener()` for lazy, reliable listener registration.

### AP-015: Side Effects in Constructors

**NEVER** perform I/O, database queries, or network calls in constructors.

Constructors should only assign dependencies. Side effects in constructors break DI container behavior (classes may be instantiated speculatively) and make testing impossible.

---

## Dependency Injection Mistakes

### AP-016: Using \OCP\Server::get()

**NEVER** use `\OCP\Server::get()` for service resolution in application code.

This is the service locator anti-pattern. It hides dependencies, breaks testability, and may fail during bootstrap. ALWAYS use constructor injection.

```php
// WRONG
class MyService {
    public function doWork(): void {
        $manager = \OCP\Server::get(IUserManager::class);
    }
}

// CORRECT
class MyService {
    public function __construct(private IUserManager $userManager) { }
}
```

### AP-017: Non-Nullable Optional Dependencies

**NEVER** use a non-nullable type hint for a service from another app that may not be installed.

If the optional app is disabled, DI will throw a `QueryException`. Use nullable types:

```php
// WRONG: Crashes if other_app is not installed
public function __construct(private OtherAppService $service) { }

// CORRECT: Gracefully handles missing app
public function __construct(private ?OtherAppService $service) { }
```

### AP-018: Explicit Registration When Auto-Wiring Works

**NEVER** register services explicitly when auto-wiring can resolve them.

If a class has only type-hinted constructor parameters that point to concrete classes or core interfaces, auto-wiring handles it automatically. Explicit registration adds maintenance burden for no benefit.

### AP-019: Injecting Unused Services

**NEVER** inject services that the class does not use.

Unused injections waste memory (DI must resolve and instantiate them) and obscure the class's actual dependencies.

---

## Deprecated API Mistakes

### AP-020: Using OCP\ILogger

**NEVER** use `OCP\ILogger` -- deprecated since NC 24.

ALWAYS inject `Psr\Log\LoggerInterface`. The PSR-3 logger automatically includes app context based on the calling namespace.

### AP-021: Using Legacy Hooks

**NEVER** use the legacy hook system (`$manager->listen(...)`, `\OC_Hook`).

ALWAYS use typed events via `IEventDispatcher` or `IRegistrationContext::registerEventListener()`. Legacy hooks are unmaintained and will be removed.

### AP-022: Using GenericEvent

**NEVER** use `OCP\EventDispatcher\GenericEvent` -- deprecated since NC 22.

ALWAYS create typed event classes extending `OCP\EventDispatcher\Event`. Typed events provide IDE support, type safety, and clear API contracts.

### AP-023: Using OC.generateUrl() in Frontend

**NEVER** use `OC.generateUrl()` in new frontend code.

ALWAYS use `import { generateUrl } from '@nextcloud/router'`. The `OC.*` global API is legacy and not tree-shakeable.

### AP-024: Using Raw fetch() or Plain Axios

**NEVER** use raw `fetch()` or plain `axios` for Nextcloud API calls.

ALWAYS use `import axios from '@nextcloud/axios'` which automatically handles authentication headers and CSRF tokens.

---

## General Mistakes

### AP-025: Forgetting parent::__construct() in Events

**NEVER** skip `parent::__construct()` in custom event classes.

The base `Event` class constructor performs required initialization. Skipping it causes undefined behavior in the event dispatcher.

```php
class MyEvent extends Event {
    public function __construct(private string $data) {
        parent::__construct();  // REQUIRED
    }
}
```

### AP-026: Missing instanceof Check in Listeners

**NEVER** skip the `instanceof` check in event listener `handle()` methods.

The `IEventListener::handle()` interface types the parameter as base `Event`. Without the check, calling event-specific methods causes fatal errors.

```php
public function handle(Event $event): void {
    if (!($event instanceof MyEvent)) {
        return;  // REQUIRED guard
    }
    // Now safe to use MyEvent methods
}
```

### AP-027: Sensitive Data in info.xml

**NEVER** include API keys, passwords, or internal URLs in info.xml.

The file is publicly readable and included in app store packages.
