# Validation Methods Reference

Complete checklist with code patterns for each validation area. Use this as the detailed companion to the SKILL.md quick-reference tables.

---

## M-01: Controller Security Attribute Scan

### What to Check
Scan every PHP file in `lib/Controller/` for public methods. Each public method on a class extending `Controller`, `OCSController`, or `ApiController` MUST have explicit security attributes.

### How to Verify

```php
// STEP 1: Find all controller classes
// Look for: extends Controller, extends OCSController, extends ApiController

// STEP 2: For each public method, check for these attributes:
#[NoAdminRequired]        // Regular user access
#[PublicPage]             // Anonymous access
#[NoCSRFRequired]         // API endpoint (no browser CSRF)
#[BruteForceProtection]   // Auth endpoints
#[UserRateLimit]          // Rate limiting
#[AnonRateLimit]          // Anonymous rate limiting
```

### Expected State
- Every public method has at least ONE security attribute, OR is intentionally admin-only (document with comment)
- `__construct()` is excluded from this check
- Methods inherited from parent are excluded

### Validation Pattern

```php
// PASS: Explicit attribute
#[NoAdminRequired]
public function index(): TemplateResponse { }

// PASS: Intentionally admin-only (documented)
/** @admin-only Manages system settings */
public function updateSystemConfig(): JSONResponse { }

// FAIL: No attributes, silently admin-only
public function listItems(): JSONResponse { }
```

---

## M-02: CSRF + PublicPage Combination Check

### What to Check
Find any method that has BOTH `#[PublicPage]` AND `#[NoCSRFRequired]`. If the method handles state changes (POST, PUT, DELETE), this is a CRITICAL violation.

### How to Verify

```php
// STEP 1: Find methods with both attributes
#[PublicPage]
#[NoCSRFRequired]

// STEP 2: Check the route verb in routes.php
// If verb is POST, PUT, or DELETE → CRITICAL

// STEP 3: Check if alternative protection exists
// Acceptable alternatives:
// - Bearer token authentication
// - API key validation in method body
// - OCS-APIRequest header requirement (OCSController handles this)
```

### Expected State
- `#[PublicPage]` + `#[NoCSRFRequired]` NEVER on POST/PUT/DELETE without alternative auth
- GET endpoints with both attributes are acceptable (read-only public data)
- OCSController methods are partially exempt (OCS-APIRequest header provides some CSRF protection)

---

## M-03: OCS Controller Validation

### What to Check
Every route in the `ocs` array of `routes.php` MUST point to a controller extending `OCSController`.

### How to Verify

```php
// STEP 1: Read appinfo/routes.php
// STEP 2: For each entry in 'ocs' array:
//   - Resolve controller class from route name
//   - Verify class extends OCSController
//   - Verify methods return DataResponse

// Route name resolution:
// 'item_api#index' → ItemApiController::index()
// 'api#getData'    → ApiController::getData()
```

### Expected State
- All `ocs` route targets extend `OCSController`
- All OCS methods return `DataResponse` (not `JSONResponse`)
- No `Controller` subclasses in the `ocs` routes array

---

## M-04: Migration File Integrity

### What to Check
Verify migration files follow naming conventions, are never modified after deployment, and include required schema elements.

### How to Verify

```php
// STEP 1: Check naming pattern
// Class name: Version{MajorMinor}Date{YYYYMMDDHHmmss}
// Example: Version1000Date20240115120000
// Major.Minor mapping: 1.0.x → 1000, 2.4.x → 2004

// STEP 2: Check for modified migrations (git)
// git log --follow lib/Migration/Version*

// STEP 3: Verify schema requirements
// Every createTable() MUST have:
$table->addColumn('id', Types::BIGINT, [
    'autoincrement' => true,
    'notnull' => true,
]);
$table->setPrimaryKey(['id']);

// STEP 4: Check table name length
// strlen('myapp_tablename') <= 23
// (oc_ prefix added by Nextcloud = 27 total, Oracle max = 30)

// STEP 5: Check column/index name length
// strlen('column_name') <= 30 (Oracle limit)
```

### Expected State
- Naming pattern matches `Version{MajorMinor}Date{Timestamp}`
- No existing migration files have been modified (check git history)
- Every table has a BIGINT autoincrement primary key
- Table names max 23 characters
- Column and index names max 30 characters
- All indices have explicit names

---

## M-05: Dependency Injection Scan

### What to Check
Verify no service locator usage exists and all dependencies use constructor injection.

### How to Verify

```php
// STEP 1: Search for service locator anti-pattern
// Grep for: \OCP\Server::get(
// Grep for: \OC::$server->
// Grep for: $container->query(  (legacy)

// STEP 2: Verify constructor injection pattern
class MyService {
    public function __construct(
        private ItemMapper $mapper,           // ✓ Type-hinted
        private LoggerInterface $logger,      // ✓ PSR-3 logger
        private ?OptionalService $optional,   // ✓ Nullable for optional
    ) {
    }
}

// STEP 3: Check for deprecated logger
// Grep for: OCP\ILogger
// Grep for: use OCP\ILogger
// Must be: use Psr\Log\LoggerInterface
```

### Expected State
- Zero occurrences of `\OCP\Server::get()` in app code
- Zero occurrences of `\OC::$server->` in app code
- Zero imports of `OCP\ILogger`
- All services injected via constructor type hints
- `<namespace>` present in `appinfo/info.xml`

---

## M-06: Frontend Package Validation

### What to Check
Verify frontend code uses official @nextcloud/* packages instead of legacy globals.

### How to Verify

```javascript
// STEP 1: Search for legacy globals
// Grep for: OC.generateUrl
// Grep for: OC.requestToken
// Grep for: OC.Notification
// Grep for: OC.dialogs

// STEP 2: Search for raw HTTP clients
// Grep for: import axios from 'axios'  (not @nextcloud/axios)
// Grep for: fetch(

// STEP 3: Verify @nextcloud/* imports
import axios from '@nextcloud/axios'              // ✓
import { generateUrl } from '@nextcloud/router'   // ✓
import { loadState } from '@nextcloud/initial-state'  // ✓
import { showSuccess } from '@nextcloud/dialogs'  // ✓

// STEP 4: Check loadState usage
loadState('myapp', 'key')              // FAIL: no fallback
loadState('myapp', 'key', defaultVal)  // PASS: has fallback

// STEP 5: Check CSS for hardcoded colors
// Grep for: color: #   (hardcoded hex colors)
// Grep for: background: #
// Must use: var(--color-*)
```

### Expected State
- Zero legacy `OC.*` global usage in new code
- All HTTP requests via `@nextcloud/axios`
- All URL generation via `@nextcloud/router`
- All `loadState()` calls have fallback argument
- CSS uses `var(--color-*)` variables exclusively

---

## M-07: File API Safety Checks

### What to Check
Verify all file operations handle errors and use correct API patterns.

### How to Verify

```php
// STEP 1: Find all get() calls on Folder objects
// Every $folder->get('path') MUST be in try/catch

try {
    $file = $userFolder->get('document.txt');
} catch (\OCP\Files\NotFoundException $e) {
    // Handle missing file
}

// STEP 2: Find all getById() calls
// getById() returns array, NEVER assume single result

$nodes = $userFolder->getById($fileId);
if (empty($nodes)) {
    throw new NotFoundException();
}
$file = $nodes[0];  // ✓ Access first element of array

// WRONG:
$file = $userFolder->getById($fileId);  // Returns array, not node!

// STEP 3: Verify instanceof checks
$node = $userFolder->get('path');
if ($node instanceof \OCP\Files\File) {
    $content = $node->getContent();  // ✓ Safe
}

// STEP 4: Verify IRootFolder injection (not IUserFolder)
public function __construct(private IRootFolder $rootFolder) {}
// Then: $this->rootFolder->getUserFolder($userId)
```

### Expected State
- Every `get()` call has NotFoundException catch
- Every `getById()` result treated as array
- Every node checked with `instanceof` before type-specific operations
- `IRootFolder` injected, `getUserFolder()` called at runtime

---

## M-08: Event System Validation

### What to Check
Verify events use typed classes and listeners follow registration conventions.

### How to Verify

```php
// STEP 1: Search for deprecated patterns
// Grep for: GenericEvent         (deprecated since NC 22)
// Grep for: ->listen(            (deprecated hooks)
// Grep for: \OC\Hooks            (legacy hook system)

// STEP 2: Verify listener registration
// MUST be in register(), not boot():
public function register(IRegistrationContext $context): void {
    $context->registerEventListener(
        NodeCreatedEvent::class,
        NodeCreatedListener::class
    );
}

// STEP 3: Verify handle() has instanceof check
public function handle(Event $event): void {
    if (!($event instanceof NodeCreatedEvent)) {
        return;  // ✓ Type guard
    }
    // Process event
}

// STEP 4: Verify custom events call parent constructor
class ItemCreatedEvent extends Event {
    public function __construct(private string $itemId) {
        parent::__construct();  // ✓ REQUIRED
    }
}
```

### Expected State
- Zero uses of `GenericEvent`
- Zero uses of legacy hook system (`->listen()`, `\OC\Hooks`)
- All listeners registered in `register()` method
- All `handle()` methods include `instanceof` check
- All custom events call `parent::__construct()`

---

## M-09: SQL Injection Prevention

### What to Check
Verify all database queries use parameterized values through the query builder.

### How to Verify

```php
// FAIL: String concatenation in query
$qb->where("user_id = '" . $userId . "'");

// FAIL: Raw SQL
$this->db->executeQuery("SELECT * FROM oc_items WHERE id = $id");

// PASS: Named parameter
$qb->where($qb->expr()->eq('user_id', $qb->createNamedParameter($userId)));

// PASS: Positional parameter
$qb->where($qb->expr()->eq('id', $qb->createPositionalParameter($id)));
```

### Expected State
- Zero raw SQL queries
- All values passed through `createNamedParameter()` or `createPositionalParameter()`
- No string concatenation in `where()`, `set()`, or `having()` clauses

---

## M-10: Cross-Area Consistency Checks

### What to Check
Verify cross-file consistency between routes, controllers, and services.

### How to Verify

```
// STEP 1: Route-to-controller mapping
// Every route in routes.php MUST have a matching controller method
// Route: 'item#create' → ItemController::create() must exist

// STEP 2: Controller-to-route mapping
// Every public controller method SHOULD have a route
// Orphan methods are unreachable

// STEP 3: Entity-to-migration mapping
// Every Entity property MUST have a corresponding database column
// Entity: protected ?string $title → Migration: addColumn('title', ...)

// STEP 4: Mapper table name
// QBMapper constructor table name MUST match migration table name
// parent::__construct($db, 'myapp_items') ↔ $schema->createTable('myapp_items')
```

### Expected State
- 1:1 mapping between routes and controller methods
- Entity properties match migration column definitions
- Mapper table names match migration table names
- No orphaned controller methods without routes
