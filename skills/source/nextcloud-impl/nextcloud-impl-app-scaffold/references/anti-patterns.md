# anti-patterns.md -- App Scaffold Mistakes

## AP-1: Missing `<namespace>` in info.xml

**Wrong:**
```xml
<info>
    <id>myapp</id>
    <name>My App</name>
    <!-- No namespace element -->
    <dependencies>
        <nextcloud min-version="28" max-version="32"/>
    </dependencies>
</info>
```

**Why it fails:** Without `<namespace>`, Nextcloud cannot map `OCA\{Namespace}\*` classes to the `lib/` directory. Auto-wiring breaks, controllers cannot be resolved, and DI throws `ClassNotFoundException`.

**Correct:**
```xml
<info>
    <id>myapp</id>
    <name>My App</name>
    <namespace>MyApp</namespace>
    <!-- ... -->
</info>
```

---

## AP-2: Missing `max-version` in Nextcloud Dependency

**Wrong:**
```xml
<dependencies>
    <nextcloud min-version="28"/>
</dependencies>
```

**Why it fails:** The app store requires BOTH `min-version` and `max-version`. Without `max-version`, the app will fail validation and cannot be published. Even for self-hosted apps, omitting it prevents Nextcloud from detecting compatibility issues during upgrades.

**Correct:**
```xml
<dependencies>
    <nextcloud min-version="28" max-version="32"/>
</dependencies>
```

---

## AP-3: Querying Services in `register()`

**Wrong:**
```php
public function register(IRegistrationContext $context): void {
    // WRONG: Other apps have not finished registering yet
    $userManager = \OCP\Server::get(IUserManager::class);
    $config = \OCP\Server::get(IConfig::class);

    if ($config->getSystemValueBool('debug')) {
        $context->registerMiddleware(DebugMiddleware::class);
    }
}
```

**Why it fails:** During `register()`, other apps' registrations are incomplete. Services may not be available, or they may be in a partially initialized state. This causes unpredictable `ContainerExceptionInterface` errors depending on app load order.

**Correct:**
```php
public function register(IRegistrationContext $context): void {
    // ALWAYS register unconditionally in register()
    $context->registerMiddleware(DebugMiddleware::class);
}

public function boot(IBootContext $context): void {
    // Query services in boot() where all registrations are complete
    $context->injectFn(function (IConfig $config) {
        // Safe to use services here
    });
}
```

---

## AP-4: Business Logic in Application.php

**Wrong:**
```php
class Application extends App implements IBootstrap {
    public function boot(IBootContext $context): void {
        $context->injectFn(function (IDBConnection $db) {
            // WRONG: Database queries in Application.php
            $result = $db->executeQuery('SELECT * FROM oc_myapp_config');
            foreach ($result->fetchAll() as $row) {
                // Process configuration...
            }
        });
    }
}
```

**Why it fails:** `Application.php` is loaded on EVERY request, not just requests to your app. Heavy initialization slows down the entire Nextcloud instance. Business logic belongs in `Service/` classes that are only instantiated when needed.

**Correct:**
```php
class Application extends App implements IBootstrap {
    public function boot(IBootContext $context): void {
        // Only lightweight registration, no heavy processing
    }
}
```

---

## AP-5: Using `database.xml` Instead of Migrations

**Wrong:**
```
myapp/
├── appinfo/
│   ├── info.xml
│   └── database.xml    # DEPRECATED
```

**Why it fails:** `database.xml` is the legacy schema definition format. It cannot handle complex migrations, data transformations, or conditional schema changes. New apps MUST use PHP migration classes.

**Correct:**
```
myapp/
├── lib/
│   └── Migration/
│       └── Version1000Date20240101120000.php
```

```php
<?php
namespace OCA\MyApp\Migration;

use Closure;
use OCP\DB\ISchemaWrapper;
use OCP\Migration\IOutput;
use OCP\Migration\SimpleMigrationStep;

class Version1000Date20240101120000 extends SimpleMigrationStep {
    public function changeSchema(IOutput $output, Closure $schemaClosure, array $options): ?ISchemaWrapper {
        /** @var ISchemaWrapper $schema */
        $schema = $schemaClosure();

        if (!$schema->hasTable('myapp_items')) {
            $table = $schema->createTable('myapp_items');
            $table->addColumn('id', 'integer', [
                'autoincrement' => true,
                'notnull' => true,
            ]);
            $table->addColumn('user_id', 'string', [
                'notnull' => true,
                'length' => 64,
            ]);
            $table->addColumn('title', 'string', [
                'notnull' => true,
                'length' => 255,
            ]);
            $table->setPrimaryKey(['id']);
            $table->addIndex(['user_id'], 'myapp_user_idx');
        }

        return $schema;
    }
}
```

---

## AP-6: Using Deprecated `requiremin`/`requiremax`

**Wrong:**
```xml
<info>
    <id>myapp</id>
    <requiremin>28</requiremin>
    <requiremax>32</requiremax>
</info>
```

**Why it fails:** `requiremin` and `requiremax` are deprecated and cause app store validation failure. They are ignored by modern Nextcloud versions.

**Correct:**
```xml
<dependencies>
    <nextcloud min-version="28" max-version="32"/>
</dependencies>
```

---

## AP-7: Wrong Namespace Casing

**Wrong:**
```xml
<namespace>myapp</namespace>    <!-- lowercase -->
<namespace>MYAPP</namespace>    <!-- all caps -->
<namespace>my_app</namespace>   <!-- underscores -->
```

```php
namespace OCA\myapp\Controller;  // Does not match
```

**Why it fails:** The `<namespace>` value is used as-is in the `OCA\{Namespace}\` prefix. Lowercase or non-PascalCase values break PSR-4 autoloading conventions and may cause class resolution failures on case-sensitive filesystems (Linux).

**Correct:**
```xml
<namespace>MyApp</namespace>
```

```php
namespace OCA\MyApp\Controller;  // Matches exactly
```

---

## AP-8: Not Implementing IBootstrap (NC 28+)

**Wrong:**
```php
class Application extends App {
    public function __construct() {
        parent::__construct('myapp');

        $container = $this->getContainer();
        // Legacy: registering in constructor
        $container->registerService(MyService::class, function ($c) {
            return new MyService($c->get(IDBConnection::class));
        });
    }
}
```

**Why it fails:** Constructor-based registration is the legacy pattern. It executes eagerly (not lazily), cannot participate in the two-phase bootstrap lifecycle, and does not work with `IRegistrationContext` features like `registerEventListener` or `registerSearchProvider`.

**Correct:**
```php
class Application extends App implements IBootstrap {
    public const APP_ID = 'myapp';

    public function __construct() {
        parent::__construct(self::APP_ID);
    }

    public function register(IRegistrationContext $context): void {
        // Lazy registration via context API
    }

    public function boot(IBootContext $context): void {
        // Post-registration initialization
    }
}
```

---

## AP-9: Mismatched App ID

**Wrong:**
```
my-app/                  # Directory name with hyphen
└── appinfo/
    └── info.xml
        <id>myapp</id>   # ID does not match directory name
```

**Why it fails:** The `<id>` in info.xml MUST match the app directory name exactly. A mismatch causes Nextcloud to fail to locate the app's files, resulting in broken routes, missing templates, and asset loading failures.

**Correct:**
```
myapp/                   # Directory name matches id
└── appinfo/
    └── info.xml
        <id>myapp</id>   # Exact match
```

---

## AP-10: Registering Event Listeners in `boot()` Instead of `register()`

**Wrong:**
```php
public function register(IRegistrationContext $context): void {
    // Empty
}

public function boot(IBootContext $context): void {
    $context->injectFn(function (IEventDispatcher $dispatcher) {
        // WRONG: Listeners registered here may miss early events
        $dispatcher->addServiceListener(
            UserCreatedEvent::class,
            UserCreatedListener::class
        );
    });
}
```

**Why it fails:** Events dispatched during the bootstrap phase (between `register()` and `boot()`) will be missed by listeners registered in `boot()`. The `register()` method guarantees listeners are active before any events fire.

**Correct:**
```php
public function register(IRegistrationContext $context): void {
    $context->registerEventListener(
        UserCreatedEvent::class,
        UserCreatedListener::class
    );
}
```

---

## AP-11: Including Sensitive Data in info.xml

**Wrong:**
```xml
<info>
    <id>myapp</id>
    <!-- NEVER put credentials in info.xml -->
    <default-api-key>sk-1234567890abcdef</default-api-key>
</info>
```

**Why it fails:** `info.xml` is publicly readable and often committed to version control. Secrets in this file are exposed to anyone with filesystem or repository access.

**Correct:** Store sensitive configuration via `OCP\IConfig::setAppValue()` or environment variables. NEVER embed secrets in XML manifests.

---

## AP-12: Using Non-HTTPS Screenshot URLs

**Wrong:**
```xml
<screenshot>http://example.com/screenshot.png</screenshot>
```

**Why it fails:** The app store requires HTTPS for all screenshot URLs. HTTP URLs will fail validation.

**Correct:**
```xml
<screenshot small-thumbnail="https://example.com/thumb.png">
    https://example.com/screenshot.png
</screenshot>
```
