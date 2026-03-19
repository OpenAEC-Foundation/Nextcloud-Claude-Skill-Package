# Review Scenarios Reference

Real-world review scenarios showing bad code, why it fails, and the correct fix.

---

## Scenario 1: Controller Missing Security Attributes

### Bad Code

```php
namespace OCA\MyApp\Controller;

use OCP\AppFramework\Controller;
use OCP\AppFramework\Http\JSONResponse;
use OCP\IRequest;

class ItemController extends Controller {
    public function __construct(
        string $appName,
        IRequest $request,
        private ItemService $service,
    ) {
        parent::__construct($appName, $request);
    }

    public function index(): JSONResponse {
        // BUG: No security attributes -- defaults to admin-only
        return new JSONResponse($this->service->findAll());
    }

    public function create(string $title): JSONResponse {
        // BUG: No security attributes -- defaults to admin-only
        return new JSONResponse($this->service->create($title));
    }
}
```

### Why It Fails
Both methods default to admin-only access. Regular authenticated users receive 403 Forbidden. This is the most common Nextcloud controller mistake.

### Fixed Code

```php
namespace OCA\MyApp\Controller;

use OCP\AppFramework\Controller;
use OCP\AppFramework\Http\Attribute\NoAdminRequired;
use OCP\AppFramework\Http\Attribute\NoCSRFRequired;
use OCP\AppFramework\Http\JSONResponse;
use OCP\IRequest;

class ItemController extends Controller {
    public function __construct(
        string $appName,
        IRequest $request,
        private ItemService $service,
    ) {
        parent::__construct($appName, $request);
    }

    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function index(): JSONResponse {
        return new JSONResponse($this->service->findAll());
    }

    #[NoAdminRequired]
    public function create(string $title): JSONResponse {
        // NoCSRFRequired NOT added -- POST needs CSRF protection
        return new JSONResponse($this->service->create($title));
    }
}
```

### Review Verdict
- `index()`: CRITICAL -- missing attributes added
- `create()`: CRITICAL -- attributes added, CSRF protection preserved for POST

---

## Scenario 2: Unprotected Public State-Changing Endpoint

### Bad Code

```php
#[PublicPage]
#[NoCSRFRequired]
public function submitForm(string $name, string $email): JSONResponse {
    $this->service->saveSubmission($name, $email);
    return new JSONResponse(['status' => 'ok']);
}
```

### Why It Fails
This endpoint is completely unprotected: no login required AND no CSRF validation. Any website can submit a form to this endpoint using the visitor's browser, enabling CSRF attacks.

### Fixed Code

```php
#[PublicPage]
public function submitForm(string $name, string $email): JSONResponse {
    // CSRF token validated by default (NoCSRFRequired removed)
    // Frontend MUST include requesttoken in the form
    $this->service->saveSubmission($name, $email);
    return new JSONResponse(['status' => 'ok']);
}
```

### Alternative Fix (API endpoint)

```php
// Use OCSController -- OCS-APIRequest header provides CSRF protection
class FormApiController extends OCSController {
    #[PublicPage]
    #[NoCSRFRequired]
    public function submitForm(string $name, string $email): DataResponse {
        // OCS-APIRequest: true header required by OCSController
        $this->service->saveSubmission($name, $email);
        return new DataResponse(['status' => 'ok']);
    }
}
```

---

## Scenario 3: Wrong Controller Base Class for OCS

### Bad Code

```php
// routes.php
return [
    'ocs' => [
        ['name' => 'api#getItems', 'url' => '/api/v1/items', 'verb' => 'GET'],
    ],
];

// ApiController.php
class ApiController extends Controller {  // WRONG base class
    public function getItems(): JSONResponse {  // WRONG response type
        return new JSONResponse($this->service->findAll());
    }
}
```

### Why It Fails
Using `Controller` instead of `OCSController` for OCS routes breaks the response envelope. Clients expecting the OCS `{ ocs: { meta: {}, data: {} } }` structure receive raw JSON instead.

### Fixed Code

```php
class ApiController extends OCSController {
    public function __construct(
        string $appName,
        IRequest $request,
        private ItemService $service,
    ) {
        parent::__construct($appName, $request);
    }

    #[NoAdminRequired]
    public function getItems(): DataResponse {
        return new DataResponse($this->service->findAll());
    }
}
```

---

## Scenario 4: Modified Existing Migration

### Bad Code

```php
// BEFORE (already deployed and executed on production):
class Version1000Date20240101000000 extends SimpleMigrationStep {
    public function changeSchema(IOutput $output, Closure $schemaClosure, array $options) {
        $schema = $schemaClosure();
        $table = $schema->createTable('myapp_items');
        $table->addColumn('id', Types::BIGINT, ['autoincrement' => true, 'notnull' => true]);
        $table->addColumn('title', Types::STRING, ['notnull' => true, 'length' => 255]);
        $table->setPrimaryKey(['id']);
        return $schema;
    }
}

// AFTER (developer modified to add column):
class Version1000Date20240101000000 extends SimpleMigrationStep {
    public function changeSchema(IOutput $output, Closure $schemaClosure, array $options) {
        $schema = $schemaClosure();
        $table = $schema->createTable('myapp_items');
        $table->addColumn('id', Types::BIGINT, ['autoincrement' => true, 'notnull' => true]);
        $table->addColumn('title', Types::STRING, ['notnull' => true, 'length' => 255]);
        $table->addColumn('status', Types::STRING, ['notnull' => false, 'length' => 32]); // ADDED
        $table->setPrimaryKey(['id']);
        return $schema;
    }
}
```

### Why It Fails
Nextcloud tracks executed migrations by class name. Once `Version1000Date20240101000000` has run, it is NEVER re-executed. The new `status` column is silently missing on all existing installations.

### Fixed Code

```php
// Original migration: UNCHANGED
class Version1000Date20240101000000 extends SimpleMigrationStep { /* ... */ }

// NEW migration for the new column:
class Version1000Date20240315120000 extends SimpleMigrationStep {
    public function changeSchema(IOutput $output, Closure $schemaClosure, array $options) {
        $schema = $schemaClosure();
        if ($schema->hasTable('myapp_items')) {
            $table = $schema->getTable('myapp_items');
            if (!$table->hasColumn('status')) {
                $table->addColumn('status', Types::STRING, [
                    'notnull' => false,
                    'length' => 32,
                ]);
            }
        }
        return $schema;
    }
}
```

---

## Scenario 5: Service Locator Anti-Pattern

### Bad Code

```php
namespace OCA\MyApp\Service;

class ItemService {
    public function findAll(): array {
        // BUG: Service locator anti-pattern
        $mapper = \OCP\Server::get(ItemMapper::class);
        $logger = \OCP\Server::get(\Psr\Log\LoggerInterface::class);

        $logger->info('Finding all items');
        return $mapper->findAll();
    }
}
```

### Why It Fails
`Server::get()` is a service locator that hides dependencies, making the class impossible to unit test without bootstrapping the entire Nextcloud server. Constructor injection makes dependencies explicit and testable.

### Fixed Code

```php
namespace OCA\MyApp\Service;

use OCA\MyApp\Db\ItemMapper;
use Psr\Log\LoggerInterface;

class ItemService {
    public function __construct(
        private ItemMapper $mapper,
        private LoggerInterface $logger,
    ) {
    }

    public function findAll(): array {
        $this->logger->info('Finding all items');
        return $this->mapper->findAll();
    }
}
```

---

## Scenario 6: Incorrect getById() Usage

### Bad Code

```php
public function getFile(int $fileId): string {
    $userFolder = $this->rootFolder->getUserFolder($this->userId);
    $file = $userFolder->getById($fileId);  // BUG: returns array
    return $file->getContent();  // CRASH: calling getContent() on array
}
```

### Why It Fails
`getById()` returns an array of matching nodes (a file can appear in multiple mount points). Calling `getContent()` on the array causes a fatal error.

### Fixed Code

```php
public function getFile(int $fileId): string {
    $userFolder = $this->rootFolder->getUserFolder($this->userId);
    $nodes = $userFolder->getById($fileId);

    if (empty($nodes)) {
        throw new NotFoundException('File not found');
    }

    $file = $nodes[0];
    if (!($file instanceof \OCP\Files\File)) {
        throw new NotFoundException('Not a file');
    }

    return $file->getContent();
}
```

---

## Scenario 7: Legacy Frontend Globals

### Bad Code

```javascript
// Using legacy OC globals
const url = OC.generateUrl('/apps/myapp/api/items')
const response = await $.ajax({
    url: url,
    type: 'GET',
    headers: {
        'requesttoken': OC.requestToken,
    },
})
```

### Why It Fails
`OC.generateUrl` and `OC.requestToken` are legacy globals that may be removed. jQuery `$.ajax` does not handle Nextcloud authentication automatically. This pattern fails with app passwords and does not handle expired sessions.

### Fixed Code

```javascript
import axios from '@nextcloud/axios'
import { generateUrl } from '@nextcloud/router'

const url = generateUrl('/apps/myapp/api/items')
const response = await axios.get(url)
// Auth headers and CSRF token handled automatically
```

---

## Scenario 8: Deprecated Event Hooks

### Bad Code

```php
// In Application boot():
public function boot(IBootContext $context): void {
    $userManager = $context->getServerContainer()->get(IUserManager::class);
    $userManager->listen('\OC\User', 'postDelete', function ($user) {
        // Clean up user data
    });
}
```

### Why It Fails
The `->listen()` hook system is deprecated since NC 17. It uses string-based event names that are error-prone and not type-safe. Additionally, registering in `boot()` instead of `register()` may miss events fired during early app loading.

### Fixed Code

```php
// In Application register():
public function register(IRegistrationContext $context): void {
    $context->registerEventListener(
        UserDeletedEvent::class,
        UserDeletedListener::class
    );
}

// Listener class:
class UserDeletedListener implements IEventListener {
    public function __construct(private CleanupService $cleanup) {}

    public function handle(Event $event): void {
        if (!($event instanceof UserDeletedEvent)) {
            return;
        }
        $this->cleanup->removeUserData($event->getUser()->getUID());
    }
}
```

---

## Scenario 9: Migration Without Primary Key

### Bad Code

```php
public function changeSchema(IOutput $output, Closure $schemaClosure, array $options) {
    $schema = $schemaClosure();
    $table = $schema->createTable('myapp_log');
    $table->addColumn('timestamp', Types::DATETIME, ['notnull' => true]);
    $table->addColumn('message', Types::TEXT, ['notnull' => true]);
    $table->addColumn('level', Types::INTEGER, ['notnull' => true]);
    // BUG: No primary key
    return $schema;
}
```

### Why It Fails
Tables without primary keys cause replication failures on Galera Cluster (used by many production Nextcloud deployments). MySQL Galera requires every table to have a primary key for row-level replication.

### Fixed Code

```php
public function changeSchema(IOutput $output, Closure $schemaClosure, array $options) {
    $schema = $schemaClosure();
    $table = $schema->createTable('myapp_log');
    $table->addColumn('id', Types::BIGINT, [
        'autoincrement' => true,
        'notnull' => true,
    ]);
    $table->addColumn('timestamp', Types::DATETIME, ['notnull' => true]);
    $table->addColumn('message', Types::TEXT, ['notnull' => true]);
    $table->addColumn('level', Types::INTEGER, ['notnull' => true]);
    $table->setPrimaryKey(['id']);
    $table->addIndex(['timestamp'], 'myapp_log_ts_idx');
    return $schema;
}
```

---

## Scenario 10: Good Code (Full Stack Example)

A correctly implemented Nextcloud app endpoint passing all review checks:

### Controller

```php
namespace OCA\MyApp\Controller;

use OCP\AppFramework\Http\Attribute\NoAdminRequired;
use OCP\AppFramework\Http\DataResponse;
use OCP\AppFramework\OCSController;
use OCP\IRequest;

class ItemApiController extends OCSController {
    public function __construct(
        string $appName,
        IRequest $request,
        private ItemService $service,
        private ?string $userId,
    ) {
        parent::__construct($appName, $request);
    }

    #[NoAdminRequired]
    public function index(): DataResponse {
        return new DataResponse($this->service->findAll($this->userId));
    }

    #[NoAdminRequired]
    public function create(string $title, string $content = ''): DataResponse {
        return new DataResponse(
            $this->service->create($title, $content, $this->userId)
        );
    }
}
```

### Routes

```php
return [
    'ocs' => [
        ['name' => 'item_api#index', 'url' => '/api/v1/items', 'verb' => 'GET'],
        ['name' => 'item_api#create', 'url' => '/api/v1/items', 'verb' => 'POST'],
    ],
];
```

### Service

```php
namespace OCA\MyApp\Service;

use OCA\MyApp\Db\ItemMapper;
use OCP\AppFramework\Db\DoesNotExistException;
use Psr\Log\LoggerInterface;

class ItemService {
    public function __construct(
        private ItemMapper $mapper,
        private LoggerInterface $logger,
    ) {
    }

    public function findAll(string $userId): array {
        return $this->mapper->findAll($userId);
    }

    public function create(string $title, string $content, string $userId): Item {
        $item = new Item();
        $item->setTitle($title);
        $item->setContent($content);
        $item->setUserId($userId);
        return $this->mapper->insert($item);
    }
}
```

### Frontend

```javascript
import axios from '@nextcloud/axios'
import { generateOcsUrl } from '@nextcloud/router'
import { showSuccess, showError } from '@nextcloud/dialogs'
import '@nextcloud/dialogs/style.css'

const baseUrl = generateOcsUrl('/apps/myapp/api/v1/items')

export async function fetchItems() {
    const { data } = await axios.get(baseUrl)
    return data.ocs.data
}

export async function createItem(title, content) {
    try {
        const { data } = await axios.post(baseUrl, { title, content })
        showSuccess('Item created')
        return data.ocs.data
    } catch (error) {
        showError('Failed to create item')
        throw error
    }
}
```

### Review Result

```
## Nextcloud Code Review

### Summary
- Files reviewed: 4
- Critical: 0
- Warnings: 0
- Info: 0

### Verdict: PASS
```
