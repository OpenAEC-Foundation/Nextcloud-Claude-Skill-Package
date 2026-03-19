# nextcloud-core-architecture — Anti-Patterns

## Bootstrap Errors

### Querying Services in register()

**WRONG** -- Other apps may not have registered their services yet:

```php
public function register(IRegistrationContext $context): void {
    // WRONG: OtherApp may not be registered yet
    $otherService = $this->getContainer()->get(OtherAppService::class);
    $otherService->doSomething();
}
```

**CORRECT** -- Use `boot()` for cross-app service access:

```php
public function register(IRegistrationContext $context): void {
    // ONLY use IRegistrationContext methods here
    $context->registerEventListener(SomeEvent::class, MyListener::class);
}

public function boot(IBootContext $context): void {
    // All apps are registered — safe to query any service
    $context->injectFn(function (OtherAppService $service) {
        $service->doSomething();
    });
}
```

**Why**: `register()` is called during app loading in dependency order. Other apps' services are not guaranteed to be available yet. `boot()` runs after ALL apps have completed `register()`.

---

### Missing namespace in info.xml

**WRONG** -- Auto-wiring silently fails:

```xml
<info>
    <id>myapp</id>
    <name>My App</name>
    <!-- Missing <namespace>! -->
</info>
```

**CORRECT** -- ALWAYS include the namespace:

```xml
<info>
    <id>myapp</id>
    <name>My App</name>
    <namespace>MyApp</namespace>
</info>
```

**Why**: The DI container uses the namespace to map `OCA\{Namespace}\*` classes to the `lib/` directory. Without it, auto-wiring cannot find your classes and controllers will fail to resolve.

---

### Business Logic in Application.php

**WRONG** -- Application.php should only contain wiring:

```php
public function boot(IBootContext $context): void {
    $context->injectFn(function (IDBConnection $db) {
        // WRONG: Business logic in Application.php
        $qb = $db->getQueryBuilder();
        $qb->select('*')->from('myapp_items')
            ->where($qb->expr()->lt('expires', $qb->createNamedParameter(time())));
        $qb->executeStatement();
    });
}
```

**CORRECT** -- Keep logic in Service classes:

```php
public function register(IRegistrationContext $context): void {
    $context->registerEventListener(AppEnableEvent::class, CleanupListener::class);
}
```

**Why**: Application.php is loaded on every request. Heavy logic here degrades performance for ALL requests, even those unrelated to your app.

---

## Dependency Injection Mistakes

### Using Server::get() (Service Locator Anti-Pattern)

**WRONG** -- Breaks testability and hides dependencies:

```php
class MyService {
    public function doWork(): void {
        $db = \OCP\Server::get(IDBConnection::class);
        $config = \OCP\Server::get(IConfig::class);
        // Hidden dependencies — impossible to mock in tests
    }
}
```

**CORRECT** -- Use constructor injection:

```php
class MyService {
    public function __construct(
        private IDBConnection $db,
        private IConfig $config
    ) {
    }

    public function doWork(): void {
        // Dependencies are explicit and mockable
    }
}
```

**Why**: `Server::get()` is a service locator that hides dependencies, making classes untestable and their requirements invisible. Constructor injection makes dependencies explicit and enables unit testing with mocks.

---

### Using Deprecated ILogger

**WRONG** -- Deprecated since NC 24:

```php
use OCP\ILogger;

class MyService {
    public function __construct(private ILogger $logger) { }
}
```

**CORRECT** -- Use PSR-3 LoggerInterface:

```php
use Psr\Log\LoggerInterface;

class MyService {
    public function __construct(private LoggerInterface $logger) { }
}
```

**Why**: `OCP\ILogger` is deprecated since NC 24 and will be removed. `Psr\Log\LoggerInterface` is the PSR-3 standard, ensuring compatibility and future-proofing.

---

### Unnecessary Explicit Registration

**WRONG** -- Registering services that auto-wiring can resolve:

```php
public function register(IRegistrationContext $context): void {
    // WRONG: ItemService and ItemMapper are concrete classes
    // Auto-wiring handles this automatically
    $context->registerService(ItemService::class,
        function (ContainerInterface $c): ItemService {
            return new ItemService(
                $c->get(ItemMapper::class),
                $c->get(LoggerInterface::class)
            );
        }
    );
}
```

**CORRECT** -- Let auto-wiring handle concrete class resolution:

```php
// No registration needed — auto-wiring resolves ItemService automatically
// because all constructor parameters have type hints
```

Only use `registerService()` when:
1. The constructor has interface parameters without a single obvious implementation
2. Primitive parameters cannot be resolved by name
3. Complex factory logic is needed

---

### I/O in Constructors

**WRONG** -- Side effects during construction:

```php
class MyService {
    private array $cache;

    public function __construct(
        private IDBConnection $db,
        private LoggerInterface $logger
    ) {
        // WRONG: Database query in constructor
        $qb = $this->db->getQueryBuilder();
        $this->cache = $qb->select('*')->from('myapp_cache')->executeQuery()->fetchAll();
        $this->logger->info('MyService initialized with ' . count($this->cache) . ' items');
    }
}
```

**CORRECT** -- Constructors MUST only assign dependencies:

```php
class MyService {
    public function __construct(
        private IDBConnection $db,
        private LoggerInterface $logger
    ) {
        // Constructor only assigns — no I/O, no side effects
    }

    public function getCache(): array {
        // Lazy loading when actually needed
        $qb = $this->db->getQueryBuilder();
        return $qb->select('*')->from('myapp_cache')->executeQuery()->fetchAll();
    }
}
```

**Why**: Services may be instantiated by the DI container even when not ultimately used for the current request. Constructor I/O wastes resources and can cause errors during container resolution.

---

### Injecting Unused Dependencies

**WRONG** -- Injecting services "just in case":

```php
class PageController extends Controller {
    public function __construct(
        string $appName,
        IRequest $request,
        private ItemService $itemService,
        private IDBConnection $db,         // WRONG: never used directly
        private IConfig $config,           // WRONG: never used directly
        private IUserManager $userManager  // WRONG: never used directly
    ) {
        parent::__construct($appName, $request);
    }
}
```

**CORRECT** -- Only inject what the class uses:

```php
class PageController extends Controller {
    public function __construct(
        string $appName,
        IRequest $request,
        private ItemService $itemService
    ) {
        parent::__construct($appName, $request);
    }
}
```

**Why**: Unused injections increase instantiation cost and create misleading dependency graphs. The service layer should encapsulate lower-level dependencies.

---

## Frontend Anti-Patterns

### Using Legacy OC.generateUrl()

**WRONG**:

```javascript
const url = OC.generateUrl('/apps/myapp/api/items')
```

**CORRECT**:

```javascript
import { generateUrl } from '@nextcloud/router'
const url = generateUrl('/apps/myapp/api/items')
```

**Why**: `OC.*` globals are legacy API. The `@nextcloud/router` package is tree-shakeable, typed, and the standard for NC 28+.

---

### Using Raw fetch() or Plain axios

**WRONG** -- Missing auth headers and CSRF tokens:

```javascript
const response = await fetch('/apps/myapp/api/items')
```

**CORRECT** -- Use @nextcloud/axios with auto-authentication:

```javascript
import axios from '@nextcloud/axios'
import { generateUrl } from '@nextcloud/router'

const response = await axios.get(generateUrl('/apps/myapp/api/items'))
```

**Why**: `@nextcloud/axios` automatically includes authentication headers and CSRF tokens. Raw `fetch()` or plain `axios` will fail on authenticated endpoints.

---

### loadState() Without Fallback

**WRONG** -- Throws on missing key:

```javascript
const data = loadState('myapp', 'optional_data')
// Throws Error if 'optional_data' was not provided by PHP
```

**CORRECT** -- ALWAYS provide fallback for optional state:

```javascript
const data = loadState('myapp', 'optional_data', null)
```

**Why**: `loadState()` throws an `Error` if the key is not found in the DOM and no fallback is provided. This crashes the entire Vue app.
