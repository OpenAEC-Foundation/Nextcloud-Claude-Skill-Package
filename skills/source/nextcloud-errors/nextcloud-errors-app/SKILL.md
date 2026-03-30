---
name: nextcloud-errors-app
description: >
  Use when encountering app registration errors, class not found exceptions, migration failures, or dependency injection problems.
  Prevents namespace typos causing ClassNotFoundException, incorrect info.xml version constraints, and boot-time service access.
  Covers namespace and autoloading failures, info.xml validation problems, migration errors, bootstrap timing issues, DI resolution failures, and deprecated API usage.
  Keywords: ClassNotFoundException, autoload, info.xml, migration error, DI resolution, bootstrap, deprecated API, namespace, app not loading, class not found, migration fails, namespace error, app broken after update..
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

# nextcloud-errors-app

## Quick Diagnostic Index

| Symptom | Jump To |
|---------|---------|
| `Class "OCA\MyApp\..." not found` | [Namespace & Autoloading](#error-1-namespace--autoloading-failures) |
| App not visible in app store / validation fails | [info.xml Validation](#error-2-infoxml-validation-problems) |
| `Migration ... already executed` or schema errors | [Migration Errors](#error-3-migration-errors) |
| Services unavailable during registration | [Bootstrap Timing](#error-4-bootstrap-timing-violations) |
| `Could not resolve ...` or constructor errors | [DI Resolution](#error-5-dependency-injection-failures) |
| `OCP\ILogger is deprecated` or hook warnings | [Deprecated API Usage](#error-6-deprecated-api-usage) |

---

## Error 1: Namespace & Autoloading Failures

### Symptom
```
OCP\AppFramework\QueryException: Could not resolve OCA\MyApp\Controller\PageController!
Class "OCA\MyApp\Service\ItemService" not found
```

### Cause A: Missing `<namespace>` in info.xml

The `<namespace>` element in `appinfo/info.xml` tells Nextcloud's autoloader how to map `OCA\{Namespace}\*` to the `lib/` directory. Without it, no classes are discoverable.

**Fix:**
```xml
<!-- appinfo/info.xml -->
<info>
    <id>myapp</id>
    <namespace>MyApp</namespace>
    <!-- ... -->
</info>
```

**ALWAYS** ensure the `<namespace>` value matches the second segment of your PHP namespace exactly: `OCA\MyApp\*` requires `<namespace>MyApp</namespace>`.

### Cause B: Directory Structure Mismatch

Nextcloud maps `OCA\{Namespace}\Controller\PageController` to `lib/Controller/PageController.php`. A mismatch between namespace and file path causes autoload failure.

**Fix:** Verify the mapping:

| PHP Namespace | Required File Path |
|---------------|-------------------|
| `OCA\MyApp\Controller\PageController` | `lib/Controller/PageController.php` |
| `OCA\MyApp\Service\ItemService` | `lib/Service/ItemService.php` |
| `OCA\MyApp\Db\ItemMapper` | `lib/Db/ItemMapper.php` |
| `OCA\MyApp\AppInfo\Application` | `lib/AppInfo/Application.php` |

**NEVER** place PHP classes outside the `lib/` directory -- Nextcloud's autoloader only scans `lib/`.

### Cause C: Case Sensitivity

Linux filesystems are case-sensitive. `lib/controller/PageController.php` will NOT match namespace `OCA\MyApp\Controller\PageController`.

**Fix:** ALWAYS match directory casing exactly to namespace casing.

---

## Error 2: info.xml Validation Problems

### Symptom
App rejected by app store, app not appearing after enable, or validation warnings in logs.

### Cause A: Deprecated Fields

These fields cause validation failure on the Nextcloud app store:

| Deprecated Field | Replacement |
|-----------------|-------------|
| `standalone` | Remove entirely |
| `default_enable` | Remove entirely |
| `shipped` | Remove entirely |
| `public` | Remove entirely |
| `remote` | Remove entirely |
| `requiremin` | `<dependencies><nextcloud min-version="28"/>` |
| `requiremax` | `<dependencies><nextcloud max-version="32"/>` |

**Fix:** NEVER use deprecated fields. ALWAYS use the `<dependencies>` block:
```xml
<dependencies>
    <nextcloud min-version="28" max-version="32"/>
    <php min-version="8.1"/>
</dependencies>
```

### Cause B: Missing Required Fields

Minimum required fields for a valid info.xml:

```xml
<info xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:noNamespaceSchemaLocation="https://apps.nextcloud.com/schema/apps/info.xsd">
    <id>myapp</id>
    <name>My Application</name>
    <summary>Short description</summary>
    <description>Full description</description>
    <version>1.0.0</version>
    <licence>AGPL-3.0-or-later</licence>
    <author>Developer Name</author>
    <namespace>MyApp</namespace>
    <category>tools</category>
    <dependencies>
        <nextcloud min-version="28" max-version="32"/>
    </dependencies>
</info>
```

**ALWAYS** include both `min-version` AND `max-version` in the nextcloud dependency -- omitting either causes app store validation failure.

### Cause C: Invalid Category

Valid categories: `customization`, `files`, `games`, `integration`, `monitoring`, `multimedia`, `office`, `organization`, `security`, `social`, `tools`.

**Fix:** NEVER use categories outside this list.

### Cause D: Invalid `<id>` Format

The `<id>` field MUST contain only lowercase ASCII letters and underscores. No hyphens, no uppercase, no numbers at the start.

---

## Error 3: Migration Errors

### Symptom
```
Migration OCA\MyApp\Migration\Version1000Date20240101000000 already executed
An exception occurred while executing a query: ... duplicate column name
```

### Cause A: Modifying an Executed Migration

Nextcloud tracks which migrations have run in the `oc_migrations` table. Once a migration executes, changing its code has NO effect -- or worse, causes schema conflicts.

**Fix:** NEVER modify existing migration files. ALWAYS create a new migration class for any schema change:

```php
// NEW file: lib/Migration/Version1000Date20240201000000.php
class Version1000Date20240201000000 extends SimpleMigrationStep {
    public function changeSchema(IOutput $output, Closure $schemaClosure, array $options) {
        $schema = $schemaClosure();
        $table = $schema->getTable('myapp_items');
        if (!$table->hasColumn('new_column')) {
            $table->addColumn('new_column', Types::STRING, [
                'notnull' => false,
                'length' => 255,
            ]);
        }
        return $schema;
    }
}
```

### Cause B: Wrong Naming Convention

Migration class names MUST follow: `Version{MajorMinor}Date{YYYYMMDDHHmmss}`.

| App Version | Migration Prefix |
|------------|-----------------|
| 1.0.x | `Version1000Date` |
| 2.34.x | `Version2034Date` |
| 3.1.x | `Version3001Date` |

**Fix:** ALWAYS use the correct version-to-number mapping: major * 1000 + minor.

### Cause C: Missing Existence Checks

Running `occ app:enable` on an existing install without guarding against existing tables/columns causes crashes.

**Fix:** ALWAYS check before creating:
```php
if (!$schema->hasTable('myapp_items')) {
    $table = $schema->createTable('myapp_items');
    // ...
}

// For columns on existing tables:
$table = $schema->getTable('myapp_items');
if (!$table->hasColumn('new_field')) {
    $table->addColumn('new_field', Types::STRING, ['notnull' => false]);
}
```

### Cause D: Missing Primary Key

Tables without primary keys fail on Galera Cluster setups (used by many hosting providers).

**Fix:** ALWAYS add a primary key:
```php
$table->addColumn('id', Types::BIGINT, ['autoincrement' => true, 'notnull' => true]);
$table->setPrimaryKey(['id']);
```

---

## Error 4: Bootstrap Timing Violations

### Symptom
```
Service not found / null service during app loading
Random "class not found" errors that resolve on reload
Intermittent failures depending on app load order
```

### Cause: Querying Services in `register()`

The `register()` method is called during app loading BEFORE all apps have completed registration. Querying services from other apps here is unreliable.

**Wrong:**
```php
public function register(IRegistrationContext $context): void {
    // WRONG: Other apps may not be registered yet
    $manager = \OCP\Server::get(ISomeManager::class);
    $manager->registerProvider(MyProvider::class);
}
```

**Fix:**
```php
public function register(IRegistrationContext $context): void {
    // ONLY use IRegistrationContext methods here
    $context->registerEventListener(SomeEvent::class, MyListener::class);
    $context->registerMiddleware(MyMiddleware::class);
    $context->registerServiceAlias(IMyInterface::class, MyImpl::class);
}

public function boot(IBootContext $context): void {
    // Safe to query services here -- all apps are registered
    $context->injectFn(function (ISomeManager $manager) {
        $manager->registerProvider(MyProvider::class);
    });
}
```

### Decision Tree: register() vs boot()

```
Need to register a service/listener/middleware?
  YES --> Use register() with IRegistrationContext methods ONLY
  NO --> Need to call methods on services from other apps?
    YES --> Use boot() with $context->injectFn()
    NO --> Need to set up runtime state?
      YES --> Use boot()
      NO --> You probably do not need Application.php at all
```

**NEVER** put business logic in Application.php -- keep it in Service/ classes.

**NEVER** use `\OCP\Server::get()` inside `register()` -- it is a service locator anti-pattern AND may fail due to load ordering.

---

## Error 5: Dependency Injection Failures

### Symptom
```
OCP\AppFramework\QueryException: Could not resolve parameter $someParam
Could not resolve type SomeInterface
```

### Cause A: Missing Type Hint

Auto-wiring requires type hints on all constructor parameters. Untyped or primitively-typed parameters (except `$appName`, `$userId`, `$webRoot`) cannot be resolved.

**Wrong:**
```php
class MyService {
    public function __construct(private $mapper) { }  // No type hint
}
```

**Fix:**
```php
class MyService {
    public function __construct(private ItemMapper $mapper) { }
}
```

### Cause B: Interface Without Alias

Auto-wiring resolves concrete classes automatically but cannot guess which implementation to use for an interface.

**Fix:** Register an alias in Application.php:
```php
public function register(IRegistrationContext $context): void {
    $context->registerServiceAlias(IMyMapper::class, MyMapper::class);
}
```

### Cause C: Unresolvable Primitive Parameters

Constructor parameters like `string $tableName` or `int $maxRetries` cannot be auto-wired (except the predefined `$appName`, `$userId`, `$webRoot`).

**Fix:** Register the parameter explicitly:
```php
public function register(IRegistrationContext $context): void {
    $context->registerParameter('tableName', 'myapp_items');
}
```

Or use a factory:
```php
$context->registerService(MyMapper::class, function (ContainerInterface $c) {
    return new MyMapper($c->get(IDBConnection::class), 'myapp_items');
});
```

### Cause D: Optional Dependency Not Nullable

When depending on a service from another app that may not be installed, a non-nullable type hint causes a fatal error.

**Fix:** ALWAYS use nullable types for optional dependencies:
```php
class MyService {
    public function __construct(private ?OptionalService $optional) { }

    public function doWork(): void {
        if ($this->optional !== null) {
            $this->optional->integrate();
        }
    }
}
```

---

## Error 6: Deprecated API Usage

### Symptom
```
OCP\ILogger is deprecated since Nextcloud 24
Using \OCP\Server::get() is discouraged
Legacy hook system warnings
```

### Deprecated: OCP\ILogger

**Since:** NC 24

**Wrong:**
```php
use OCP\ILogger;

class MyService {
    public function __construct(private ILogger $logger) { }
}
```

**Fix:** ALWAYS use PSR-3 LoggerInterface:
```php
use Psr\Log\LoggerInterface;

class MyService {
    public function __construct(private LoggerInterface $logger) { }

    public function process(): void {
        $this->logger->info('Processing started');
        $this->logger->error('Failed', ['exception' => $e]);
    }
}
```

### Deprecated: \OCP\Server::get()

**Wrong:**
```php
$userManager = \OCP\Server::get(IUserManager::class);
```

**Fix:** ALWAYS use constructor injection:
```php
class MyService {
    public function __construct(private IUserManager $userManager) { }
}
```

### Deprecated: Legacy Hooks

**Wrong:**
```php
$userManager->listen('\OC\User', 'postDelete', function ($user) { });
```

**Fix:** ALWAYS use typed events with IRegistrationContext:
```php
// In Application::register()
$context->registerEventListener(
    UserDeletedEvent::class,
    UserDeletedListener::class
);
```

### Deprecated: GenericEvent

**Since:** NC 22

**Wrong:**
```php
use OCP\EventDispatcher\GenericEvent;
$dispatcher->dispatch('my.event', new GenericEvent($subject, $args));
```

**Fix:** ALWAYS create typed event classes:
```php
class ItemCreatedEvent extends \OCP\EventDispatcher\Event {
    public function __construct(private string $itemId) {
        parent::__construct();
    }
    public function getItemId(): string { return $this->itemId; }
}

// Dispatch
$dispatcher->dispatchTyped(new ItemCreatedEvent($id));
```

### Deprecated: database.xml

**Fix:** NEVER use `database.xml` for new apps. ALWAYS use migrations in `lib/Migration/`.

### Deprecated: requiremin/requiremax in info.xml

**Fix:** ALWAYS use the `<dependencies>` block instead. See [Error 2](#error-2-infoxml-validation-problems).

---

## Critical Rules Summary

| Rule | Scope |
|------|-------|
| ALWAYS set `<namespace>` in info.xml | Autoloading |
| ALWAYS match directory casing to namespace casing | Autoloading |
| ALWAYS include both `min-version` and `max-version` | info.xml |
| NEVER use deprecated info.xml fields | info.xml |
| NEVER modify executed migrations | Migrations |
| ALWAYS guard with `hasTable()`/`hasColumn()` | Migrations |
| ALWAYS add primary keys to tables | Migrations |
| NEVER query services in `register()` | Bootstrap |
| NEVER use `\OCP\Server::get()` | DI |
| ALWAYS use nullable types for optional deps | DI |
| ALWAYS use `Psr\Log\LoggerInterface` | Logging |
| ALWAYS use typed events, not hooks or GenericEvent | Events |

---

## Reference Links

- [references/methods.md](references/methods.md) -- Error types, exception classes, diagnostic methods
- [references/examples.md](references/examples.md) -- Error scenarios with complete fixes
- [references/anti-patterns.md](references/anti-patterns.md) -- App development mistakes to avoid

### Official Sources

- https://docs.nextcloud.com/server/latest/developer_manual/app_development/info.html
- https://docs.nextcloud.com/server/latest/developer_manual/app_development/bootstrap.html
- https://docs.nextcloud.com/server/latest/developer_manual/basics/dependency_injection.html
- https://docs.nextcloud.com/server/latest/developer_manual/basics/events.html
