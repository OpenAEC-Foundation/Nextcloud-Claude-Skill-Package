# Error Scenarios with Fixes

## Scenario 1: App Fails to Load After Enable

### Symptom
```
occ app:enable myapp
# App appears enabled but pages return 500 error
# Log: "Class 'OCA\Myapp\AppInfo\Application' not found"
```

### Root Cause
The `<namespace>` in info.xml uses wrong casing. `<namespace>Myapp</namespace>` maps to `OCA\Myapp\*` but the actual files use `OCA\MyApp\*`.

### Fix
```xml
<!-- WRONG -->
<namespace>Myapp</namespace>

<!-- CORRECT — must match PHP namespace exactly -->
<namespace>MyApp</namespace>
```

Then verify that `lib/AppInfo/Application.php` declares:
```php
namespace OCA\MyApp\AppInfo;
```

---

## Scenario 2: Controller Returns 404 Despite Route Existing

### Symptom
```
GET /index.php/apps/myapp/api/items → 404 Not Found
```

### Root Cause
Route name `api#items` expects `ApiController::items()` but the class is named `ItemApiController`.

### Fix
Route names map to controllers via the pattern `{name}#{method}` → `{Name}Controller::{method}()`:

```php
// routes.php
return ['routes' => [
    // WRONG: 'api#items' maps to ApiController::items()
    ['name' => 'api#items', 'url' => '/api/items', 'verb' => 'GET'],

    // CORRECT: 'item_api#index' maps to ItemApiController::index()
    ['name' => 'item_api#index', 'url' => '/api/items', 'verb' => 'GET'],
]];
```

---

## Scenario 3: Migration Fails on Production

### Symptom
```
occ upgrade
# Error: Column "title" already exists in table "oc_myapp_items"
```

### Root Cause
Developer modified an existing migration to add a column, but that migration already ran in production. Nextcloud skips already-executed migrations.

### Fix
Create a NEW migration file:

```php
// lib/Migration/Version1000Date20240201000000.php (NEW file)
class Version1000Date20240201000000 extends SimpleMigrationStep {
    public function changeSchema(IOutput $output, Closure $schemaClosure, array $options) {
        $schema = $schemaClosure();
        $table = $schema->getTable('myapp_items');

        // ALWAYS guard with hasColumn check
        if (!$table->hasColumn('title')) {
            $table->addColumn('title', Types::STRING, [
                'notnull' => false,
                'length' => 255,
            ]);
        }

        return $schema;
    }
}
```

---

## Scenario 4: Service Randomly Unavailable

### Symptom
```
# Works sometimes, fails other times depending on app load order
QueryException: Could not resolve OCA\OtherApp\Service\PartnerService
```

### Root Cause
Service from another app is queried in `register()` before that app has registered.

### Fix
Move cross-app service usage to `boot()`:

```php
class Application extends App implements IBootstrap {
    public function register(IRegistrationContext $context): void {
        // ONLY use $context methods here
        $context->registerEventListener(SomeEvent::class, MyListener::class);
    }

    public function boot(IBootContext $context): void {
        // Safe: all apps have completed register()
        $context->injectFn(function (IPartnerManager $manager) {
            $manager->addProvider(MyProvider::class);
        });
    }
}
```

---

## Scenario 5: DI Fails for Constructor with Mixed Parameters

### Symptom
```
QueryException: Could not resolve parameter $maxRetries of MyService
```

### Root Cause
`int $maxRetries` is a primitive parameter that auto-wiring cannot resolve.

### Fix

**Option A: Register the parameter:**
```php
public function register(IRegistrationContext $context): void {
    $context->registerParameter('maxRetries', 3);
}
```

**Option B: Use a factory:**
```php
public function register(IRegistrationContext $context): void {
    $context->registerService(MyService::class, function (ContainerInterface $c) {
        return new MyService(
            $c->get(ItemMapper::class),
            $c->get(LoggerInterface::class),
            3  // maxRetries
        );
    });
}
```

**Option C: Use IAppConfig instead (recommended for configurable values):**
```php
class MyService {
    public function __construct(
        private ItemMapper $mapper,
        private IAppConfig $appConfig,
    ) { }

    private function getMaxRetries(): int {
        return $this->appConfig->getValueInt('myapp', 'max_retries', 3);
    }
}
```

---

## Scenario 6: Deprecated ILogger Causes Warnings

### Symptom
```
# nextcloud.log:
"OCP\ILogger is deprecated since Nextcloud 24, use Psr\Log\LoggerInterface"
```

### Root Cause
Constructor injects deprecated `OCP\ILogger` instead of the PSR-3 standard.

### Fix
```php
// BEFORE (deprecated)
use OCP\ILogger;

class MyService {
    public function __construct(private ILogger $logger) { }

    public function run(): void {
        $this->logger->error('Failed', ['app' => 'myapp']);
    }
}

// AFTER (correct)
use Psr\Log\LoggerInterface;

class MyService {
    public function __construct(private LoggerInterface $logger) { }

    public function run(): void {
        $this->logger->error('Failed', ['exception' => $e]);
    }
}
```

**Key difference:** PSR-3 LoggerInterface does NOT require the `app` context key -- Nextcloud automatically adds it based on the calling namespace.

---

## Scenario 7: Event Listener Never Fires

### Symptom
Event listener registered but never invoked despite the triggering action occurring.

### Root Cause A: Registered in boot() instead of register()

```php
// WRONG: Listener registered too late
public function boot(IBootContext $context): void {
    $context->injectFn(function (IEventDispatcher $dispatcher) {
        $dispatcher->addListener(NodeCreatedEvent::class, function ($event) {
            // Never called for events during boot phase
        });
    });
}

// CORRECT: Use register() for event listeners
public function register(IRegistrationContext $context): void {
    $context->registerEventListener(NodeCreatedEvent::class, MyListener::class);
}
```

### Root Cause B: Missing instanceof Check in Listener

```php
class MyListener implements IEventListener {
    public function handle(Event $event): void {
        // WRONG: No type check — may receive unexpected event types
        $event->getNode();  // Fatal if wrong event type

        // CORRECT: Always check instanceof
        if (!($event instanceof NodeCreatedEvent)) {
            return;
        }
        $node = $event->getNode();
    }
}
```

---

## Scenario 8: App Store Rejects info.xml

### Symptom
```
Upload to apps.nextcloud.com fails with validation error
```

### Common Fixes

**Missing max-version:**
```xml
<!-- WRONG -->
<dependencies>
    <nextcloud min-version="28"/>
</dependencies>

<!-- CORRECT -->
<dependencies>
    <nextcloud min-version="28" max-version="32"/>
</dependencies>
```

**Invalid screenshot URL:**
```xml
<!-- WRONG: HTTP -->
<screenshot>http://example.com/screenshot.png</screenshot>

<!-- CORRECT: HTTPS required -->
<screenshot>https://example.com/screenshot.png</screenshot>
```

**Invalid licence identifier:**
```xml
<!-- WRONG: Not an SPDX identifier -->
<licence>GPL</licence>

<!-- CORRECT: Use SPDX format -->
<licence>AGPL-3.0-or-later</licence>
```

---

## Scenario 9: Composer Dependencies Not Found

### Symptom
```
Class 'Vendor\Library\SomeClass' not found
```

### Root Cause
Composer autoloader not included in Application.php.

### Fix
```php
class Application extends App implements IBootstrap {
    public function register(IRegistrationContext $context): void {
        // Include Composer autoloader FIRST
        include_once __DIR__ . '/../../vendor/autoload.php';

        // Then register services
        $context->registerEventListener(/* ... */);
    }
}
```

**ALWAYS** place the Composer autoload include at the top of `register()`, before any other registrations that depend on vendored classes.

---

## Scenario 10: OCS Endpoint Returns HTML Instead of JSON

### Symptom
OCS API endpoint returns an HTML login page or error instead of JSON/XML envelope.

### Root Cause
The controller extends `Controller` instead of `OCSController`, or the route is in the `routes` array instead of `ocs`.

### Fix
```php
// WRONG: Regular controller on OCS route
class ApiController extends Controller { }

// CORRECT: Must use OCSController for OCS routes
class ApiController extends OCSController { }
```

```php
// routes.php
return [
    // WRONG: OCS endpoint in 'routes' array
    'routes' => [
        ['name' => 'api#getData', 'url' => '/api/v1/data', 'verb' => 'GET'],
    ],

    // CORRECT: OCS endpoint in 'ocs' array
    'ocs' => [
        ['name' => 'api#getData', 'url' => '/api/v1/data', 'verb' => 'GET'],
    ],
];
```
