# App Scaffolding Anti-Patterns

## AP-1: Missing namespace in info.xml

**Wrong:**
```xml
<info>
    <id>myapp</id>
    <name>My App</name>
    <!-- No <namespace> element -->
</info>
```

**Correct:**
```xml
<info>
    <id>myapp</id>
    <name>My App</name>
    <namespace>MyApp</namespace>
</info>
```

**Why:** Without `<namespace>`, the autoloader cannot map `OCA\MyApp\*` classes to the `lib/` directory. Auto-wiring silently fails, and controllers will not resolve their dependencies.

---

## AP-2: Legacy Application.php without IBootstrap

**Wrong:**
```php
class Application extends App {
    public function __construct() {
        parent::__construct('myapp');
        $container = $this->getContainer();
        $container->registerService(MyService::class, function ($c) {
            return new MyService($c->get(IDBConnection::class));
        });
    }
}
```

**Correct:**
```php
class Application extends App implements IBootstrap {
    public const APP_ID = 'myapp';

    public function __construct() {
        parent::__construct(self::APP_ID);
    }

    public function register(IRegistrationContext $context): void {
        // Registrations here
    }

    public function boot(IBootContext $context): void {
        // Post-registration init here
    }
}
```

**Why:** Legacy constructor-based registration bypasses the lazy loading system, causes performance issues, and prevents proper cross-app dependency resolution.

---

## AP-3: Using database.xml instead of migrations

**Wrong:**
```
appinfo/
└── database.xml    <-- DEPRECATED
```

**Correct:**
```
lib/
└── Migration/
    └── Version1000Date20260319120000.php
```

**Why:** `database.xml` is a legacy format that does not support data migration, conditional logic, or incremental schema changes. Migration classes are the ONLY supported approach for NC 28+.

---

## AP-4: Missing security attributes on controller methods

**Wrong:**
```php
class PageController extends Controller {
    // No attributes = admin-only, CSRF required
    public function index(): TemplateResponse {
        return new TemplateResponse('myapp', 'main');
    }
}
```

**Correct:**
```php
class PageController extends Controller {
    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function index(): TemplateResponse {
        return new TemplateResponse('myapp', 'main');
    }
}
```

**Why:** Without `#[NoAdminRequired]`, only admin users can access the page. Without `#[NoCSRFRequired]` on the initial page load, browser navigation to the app will fail with a CSRF error.

---

## AP-5: Hardcoded colors in CSS

**Wrong:**
```css
.my-component {
    color: #333333;
    background: #ffffff;
    border-color: #0082C9;
}
```

**Correct:**
```css
.my-component {
    color: var(--color-main-text);
    background: var(--color-main-background);
    border-color: var(--color-primary-element);
}
```

**Why:** Hardcoded colors break dark mode, custom themes, and accessibility features. Nextcloud provides CSS custom properties that automatically adapt to the active theme.

---

## AP-6: Using barrel imports from @nextcloud/vue

**Wrong:**
```javascript
import { NcButton, NcContent, NcAppContent } from '@nextcloud/vue'
```

**Correct:**
```javascript
import NcButton from '@nextcloud/vue/components/NcButton'
import NcContent from '@nextcloud/vue/components/NcContent'
import NcAppContent from '@nextcloud/vue/components/NcAppContent'
```

**Why:** Barrel imports pull in the ENTIRE component library, significantly increasing bundle size. Direct imports enable tree-shaking and produce smaller JavaScript bundles.

---

## AP-7: Using raw fetch/axios instead of @nextcloud/axios

**Wrong:**
```javascript
import axios from 'axios'

const response = await axios.get('/apps/myapp/api/items')
```

**Correct:**
```javascript
import axios from '@nextcloud/axios'
import { generateUrl } from '@nextcloud/router'

const response = await axios.get(generateUrl('/apps/myapp/api/items'))
```

**Why:** `@nextcloud/axios` automatically includes CSRF tokens and authentication headers. Raw `axios` or `fetch` will fail with 401/403 errors on authenticated endpoints.

---

## AP-8: Using OC.generateUrl() instead of @nextcloud/router

**Wrong:**
```javascript
const url = OC.generateUrl('/apps/myapp/api/items')
```

**Correct:**
```javascript
import { generateUrl } from '@nextcloud/router'
const url = generateUrl('/apps/myapp/api/items')
```

**Why:** `OC.*` globals are legacy API. They are not tree-shakeable, have no TypeScript support, and may be removed in future Nextcloud versions.

---

## AP-9: Using \OCP\Server::get() for dependency resolution

**Wrong:**
```php
class MyService {
    public function doWork(): void {
        $db = \OCP\Server::get(IDBConnection::class);
        // ...
    }
}
```

**Correct:**
```php
class MyService {
    public function __construct(
        private IDBConnection $db,
    ) {
    }

    public function doWork(): void {
        // Use $this->db
    }
}
```

**Why:** `Server::get()` is a service locator anti-pattern that hides dependencies, makes testing difficult, and bypasses the DI container's lifecycle management.

---

## AP-10: Table without primary key

**Wrong:**
```php
$table = $schema->createTable('myapp_items');
$table->addColumn('title', Types::STRING, ['notnull' => true, 'length' => 255]);
$table->addColumn('user_id', Types::STRING, ['notnull' => true, 'length' => 64]);
// No primary key set
```

**Correct:**
```php
$table = $schema->createTable('myapp_items');
$table->addColumn('id', Types::BIGINT, ['autoincrement' => true, 'notnull' => true]);
$table->addColumn('title', Types::STRING, ['notnull' => true, 'length' => 255]);
$table->addColumn('user_id', Types::STRING, ['notnull' => true, 'length' => 64]);
$table->setPrimaryKey(['id']);
```

**Why:** Galera Cluster (used in many production Nextcloud deployments) requires all tables to have primary keys. Tables without them cause replication failures.

---

## AP-11: Using deprecated OCP\ILogger

**Wrong:**
```php
use OCP\ILogger;

class MyService {
    public function __construct(private ILogger $logger) {}
}
```

**Correct:**
```php
use Psr\Log\LoggerInterface;

class MyService {
    public function __construct(private LoggerInterface $logger) {}
}
```

**Why:** `OCP\ILogger` is deprecated since NC 24. The PSR-3 `LoggerInterface` is the standard, supports structured logging contexts, and is compatible with all PHP logging frameworks.

---

## AP-12: Registering event listeners in boot()

**Wrong:**
```php
public function boot(IBootContext $context): void {
    $context->injectFn(function (IEventDispatcher $dispatcher) {
        $dispatcher->addListener(NodeCreatedEvent::class, function ($event) {
            // handle event
        });
    });
}
```

**Correct:**
```php
public function register(IRegistrationContext $context): void {
    $context->registerEventListener(
        NodeCreatedEvent::class,
        NodeCreatedListener::class
    );
}
```

**Why:** Listeners registered in `boot()` bypass lazy loading, causing the listener class to be instantiated immediately. Using `registerEventListener()` in `register()` defers class instantiation until the event is actually dispatched.

---

## AP-13: Missing declare(strict_types=1)

**Wrong:**
```php
<?php

namespace OCA\MyApp\Service;
```

**Correct:**
```php
<?php

declare(strict_types=1);

namespace OCA\MyApp\Service;
```

**Why:** Without strict types, PHP performs implicit type coercion that can hide bugs. Strict types enforce explicit type checking on function arguments and return values, catching errors early.

---

## AP-14: Table name exceeding Oracle limit

**Wrong:**
```php
parent::__construct($db, 'myapp_very_long_descriptive_table_name');
// 'oc_myapp_very_long_descriptive_table_name' = 41 chars, exceeds Oracle 30-char limit
```

**Correct:**
```php
parent::__construct($db, 'myapp_items');
// 'oc_myapp_items' = 14 chars, well within limits
```

**Why:** Table names in Nextcloud get the `oc_` prefix (3 chars). Oracle databases have a 30-character limit on table names. The effective app table name limit is 27 characters. ALWAYS keep table names under 23 characters to be safe.

---

## AP-15: Missing @nextcloud/dialogs/style.css import

**Wrong:**
```javascript
import { showError, showSuccess } from '@nextcloud/dialogs'

showSuccess('Item saved')  // Toast appears without styling
```

**Correct:**
```javascript
import { showError, showSuccess } from '@nextcloud/dialogs'
import '@nextcloud/dialogs/style.css'

showSuccess('Item saved')  // Toast renders correctly
```

**Why:** The dialogs package does not auto-import its CSS. Without the style import, toast notifications render as unstyled HTML elements.

---

## AP-16: Route name mismatch with controller

**Wrong:**
```php
// routes.php
['name' => 'items#index', 'url' => '/api/items', 'verb' => 'GET'],

// But controller is named TaskController, not ItemsController
```

**Correct:**
```php
// routes.php
['name' => 'task#index', 'url' => '/api/tasks', 'verb' => 'GET'],

// Controller: TaskController::index()
```

**Why:** Route name `task#index` resolves to `TaskController::index()`. The part before `#` is singularized and PascalCased to match the controller class. A mismatch causes 404 errors.

---

## AP-17: Performing I/O in constructors

**Wrong:**
```php
class MyService {
    private array $cache;

    public function __construct(private IDBConnection $db) {
        // Loading data in constructor - BAD
        $qb = $this->db->getQueryBuilder();
        $this->cache = $qb->select('*')->from('myapp_items')->executeQuery()->fetchAllAssociative();
    }
}
```

**Correct:**
```php
class MyService {
    public function __construct(private IDBConnection $db) {
        // Constructor only assigns dependencies
    }

    public function getItems(): array {
        $qb = $this->db->getQueryBuilder();
        return $qb->select('*')->from('myapp_items')->executeQuery()->fetchAllAssociative();
    }
}
```

**Why:** Constructors run during DI resolution, which happens on every request. I/O in constructors slows app loading, may fail during bootstrap, and makes the service untestable.

---

## AP-18: Forgetting parent::setUp() in tests

**Wrong:**
```php
class MyServiceTest extends TestCase {
    protected function setUp(): void {
        // Missing parent::setUp() call
        $this->service = new MyService($this->createMock(IDBConnection::class));
    }
}
```

**Correct:**
```php
class MyServiceTest extends TestCase {
    protected function setUp(): void {
        parent::setUp();
        $this->service = new MyService($this->createMock(IDBConnection::class));
    }
}
```

**Why:** Nextcloud's `TestCase` parent class performs cleanup and initialization in `setUp()`. Skipping it causes test pollution where state leaks between test methods.
