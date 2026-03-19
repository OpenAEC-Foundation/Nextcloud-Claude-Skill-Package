# Anti-Patterns Reference (Consolidated)

All anti-patterns organized by area with severity, detection pattern, and fix.

---

## Controller Anti-Patterns

### AP-C01: Missing Security Attributes
**Severity:** CRITICAL
**Detection:** Public controller method with zero PHP 8 attributes
**Impact:** Method defaults to admin-only -- regular users get 403
**Fix:** Add `#[NoAdminRequired]` for regular users or `#[PublicPage]` for anonymous access

### AP-C02: PublicPage + NoCSRFRequired on State Change
**Severity:** CRITICAL
**Detection:** Method has both `#[PublicPage]` and `#[NoCSRFRequired]` with POST/PUT/DELETE verb
**Impact:** Endpoint is completely unprotected against CSRF attacks
**Fix:** Remove `#[NoCSRFRequired]` or switch to OCSController (OCS-APIRequest header provides protection)

### AP-C03: Throttle on Success
**Severity:** WARNING
**Detection:** `$response->throttle()` called unconditionally or in success branch
**Impact:** Legitimate users experience increasing delays
**Fix:** Call `throttle()` ONLY in failure/error branches

### AP-C04: Missing Route Definition
**Severity:** CRITICAL
**Detection:** Public controller method without matching entry in `routes.php`
**Impact:** Method is unreachable -- no URL maps to it
**Fix:** Add route entry in `appinfo/routes.php`

### AP-C05: Legacy Annotations Instead of Attributes
**Severity:** WARNING
**Detection:** `@NoAdminRequired`, `@NoCSRFRequired`, `@PublicPage` in docblocks
**Impact:** Works but deprecated since NC 27 -- will be removed
**Fix:** Replace with PHP 8 attributes: `#[NoAdminRequired]`, `#[NoCSRFRequired]`, `#[PublicPage]`

---

## OCS Anti-Patterns

### AP-O01: Controller Instead of OCSController
**Severity:** CRITICAL
**Detection:** Route in `ocs` array pointing to class extending `Controller`
**Impact:** Response envelope broken -- clients receive raw data instead of OCS wrapper
**Fix:** Change base class to `OCSController`

### AP-O02: JSONResponse in OCS Endpoint
**Severity:** WARNING
**Detection:** OCSController method returning `JSONResponse` instead of `DataResponse`
**Impact:** Bypasses OCS response formatting -- no envelope, wrong status codes
**Fix:** Return `DataResponse` -- the responder system handles JSON/XML formatting

### AP-O03: Missing OCS-APIRequest Header
**Severity:** CRITICAL
**Detection:** OCS API call without `OCS-APIRequest: true` header
**Impact:** Request rejected by Nextcloud middleware
**Fix:** ALWAYS include `OCS-APIRequest: true` header in all OCS requests

### AP-O04: Using v1 Endpoints
**Severity:** WARNING
**Detection:** OCS URLs using `/ocs/v1.php/` prefix
**Impact:** HTTP status always 200 regardless of error -- masks failures
**Fix:** Use `/ocs/v2.php/` which mirrors OCS status codes to HTTP status codes

---

## Database Anti-Patterns

### AP-D01: Modified Existing Migration
**Severity:** CRITICAL
**Detection:** Git diff shows changes to existing `Version*Date*` migration file
**Impact:** Changes silently ignored on instances that already ran the migration
**Fix:** Create a new migration class for schema changes

### AP-D02: Table Without Primary Key
**Severity:** CRITICAL
**Detection:** `createTable()` without `setPrimaryKey()` call
**Impact:** Galera Cluster replication fails -- breaks high-availability deployments
**Fix:** ALWAYS add `$table->setPrimaryKey(['id'])` with a BIGINT autoincrement id column

### AP-D03: Raw SQL Queries
**Severity:** CRITICAL
**Detection:** `$this->db->executeQuery("SELECT ...")` or string concatenation in query building
**Impact:** SQL injection vulnerability and database portability broken (MySQL/PostgreSQL/SQLite/Oracle differences)
**Fix:** Use query builder with `createNamedParameter()` for all values

### AP-D04: Table Name Too Long
**Severity:** WARNING
**Detection:** Table name exceeds 23 characters (27 with `oc_` prefix)
**Impact:** Oracle database compatibility failure (30 char limit)
**Fix:** Shorten table name to max 23 characters

### AP-D05: Column Name Too Long
**Severity:** WARNING
**Detection:** Column or index name exceeds 30 characters
**Impact:** Oracle database compatibility failure
**Fix:** Shorten to max 30 characters

### AP-D06: Missing Index Names
**Severity:** INFO
**Detection:** `addIndex()` without explicit index name
**Impact:** Cannot reference index for future modification or deletion
**Fix:** ALWAYS provide explicit, unique index names: `$table->addIndex(['col'], 'myapp_col_idx')`

### AP-D07: Cursor Not Closed
**Severity:** WARNING
**Detection:** `executeQuery()` result without `closeCursor()` call
**Impact:** Database connection leak on some drivers
**Fix:** ALWAYS call `$result->closeCursor()` after processing rows (not needed for `findEntity`/`findEntities`)

---

## Dependency Injection Anti-Patterns

### AP-DI01: Server::get() Usage
**Severity:** CRITICAL
**Detection:** `\OCP\Server::get(SomeClass::class)` in app code
**Impact:** Service locator hides dependencies, breaks unit testing
**Fix:** Use constructor injection with type hints

### AP-DI02: Legacy \OC::$server Access
**Severity:** CRITICAL
**Detection:** `\OC::$server->get*()` calls in app code
**Impact:** Tightly couples to internal server API -- may break on upgrades
**Fix:** Use constructor injection with OCP interfaces

### AP-DI03: Deprecated ILogger
**Severity:** WARNING
**Detection:** `use OCP\ILogger` or `OCP\ILogger` type hint
**Impact:** Deprecated since NC 24 -- will be removed
**Fix:** Use `Psr\Log\LoggerInterface` instead

### AP-DI04: Missing Namespace in info.xml
**Severity:** CRITICAL
**Detection:** No `<namespace>` element in `appinfo/info.xml`
**Impact:** Auto-wiring silently fails -- all constructor injection breaks
**Fix:** Add `<namespace>MyApp</namespace>` to info.xml

### AP-DI05: Service Queries in register()
**Severity:** CRITICAL
**Detection:** Calling `$context->getServerContainer()->get()` inside `register()` method
**Impact:** Other apps may not be registered yet -- service resolution fails unpredictably
**Fix:** Move service queries to `boot()` method or use `$context->injectFn()` in boot

### AP-DI06: Side Effects in Constructor
**Severity:** WARNING
**Detection:** I/O operations, database queries, or event dispatching in `__construct()`
**Impact:** Breaks lazy instantiation -- service created when container resolves, not when needed
**Fix:** Move all side effects to dedicated methods called explicitly

---

## Frontend Anti-Patterns

### AP-F01: OC.generateUrl Usage
**Severity:** WARNING
**Detection:** `OC.generateUrl(` in JavaScript/TypeScript files
**Impact:** Legacy global -- may be removed in future NC versions
**Fix:** `import { generateUrl } from '@nextcloud/router'`

### AP-F02: Raw Axios/Fetch
**Severity:** WARNING
**Detection:** `import axios from 'axios'` (not `@nextcloud/axios`) or `fetch(` calls
**Impact:** Missing authentication headers, CSRF token, session expiry handling
**Fix:** `import axios from '@nextcloud/axios'`

### AP-F03: Hardcoded Colors
**Severity:** WARNING
**Detection:** CSS with `color: #xxx`, `background: #xxx`, or `rgb()` values
**Impact:** Breaks dark mode, custom themes, and accessibility high-contrast mode
**Fix:** Use `var(--color-main-text)`, `var(--color-main-background)`, etc.

### AP-F04: loadState Without Fallback
**Severity:** WARNING
**Detection:** `loadState('app', 'key')` with only two arguments
**Impact:** Throws `Error` if the key was not provided by the PHP backend
**Fix:** `loadState('app', 'key', defaultValue)` -- ALWAYS provide third argument

### AP-F05: Missing Dialog Styles
**Severity:** INFO
**Detection:** Using `showSuccess`/`showError` without `import '@nextcloud/dialogs/style.css'`
**Impact:** Toast notifications render without Nextcloud styling
**Fix:** Add `import '@nextcloud/dialogs/style.css'` in the entry point

### AP-F06: Barrel Import of @nextcloud/vue
**Severity:** INFO
**Detection:** `import { NcButton } from '@nextcloud/vue'` (barrel import)
**Impact:** Larger bundle size -- imports entire library
**Fix:** `import NcButton from '@nextcloud/vue/components/NcButton'` (direct import)

---

## File API Anti-Patterns

### AP-FA01: Missing NotFoundException Handling
**Severity:** CRITICAL
**Detection:** `$folder->get('path')` without try/catch for `NotFoundException`
**Impact:** Unhandled exception crashes the entire request
**Fix:** Wrap in try/catch: `catch (\OCP\Files\NotFoundException $e)`

### AP-FA02: getById() Treated as Single Result
**Severity:** CRITICAL
**Detection:** `$folder->getById($id)` result used directly as a node
**Impact:** Fatal error -- `getById()` returns array, not a single node
**Fix:** `$nodes = $folder->getById($id); $file = $nodes[0] ?? null;`

### AP-FA03: Hardcoded File Paths
**Severity:** WARNING
**Detection:** String paths like `/data/user/files/...` instead of Node API
**Impact:** Bypasses storage abstraction -- fails on external storage, encryption, versioning
**Fix:** Use `$rootFolder->getUserFolder($userId)->get('relative/path')`

### AP-FA04: Missing instanceof Check
**Severity:** WARNING
**Detection:** `get()` result used without checking `instanceof File` or `instanceof Folder`
**Impact:** Calling file methods on a folder (or vice versa) causes runtime errors
**Fix:** ALWAYS check: `if ($node instanceof \OCP\Files\File)`

---

## Event System Anti-Patterns

### AP-E01: Using GenericEvent
**Severity:** WARNING
**Detection:** `use OCP\EventDispatcher\GenericEvent` or `new GenericEvent()`
**Impact:** Deprecated since NC 22 -- will be removed. Not type-safe.
**Fix:** Create typed event class extending `OCP\EventDispatcher\Event`

### AP-E02: Legacy Hook System
**Severity:** CRITICAL
**Detection:** `$manager->listen('\OC\...')` or `\OC\Hooks\` references
**Impact:** Deprecated since NC 17 -- string-based, error-prone, may be removed
**Fix:** Use `IRegistrationContext::registerEventListener()` with typed events

### AP-E03: Missing instanceof in handle()
**Severity:** WARNING
**Detection:** `handle(Event $event)` without `if (!($event instanceof SpecificEvent))` check
**Impact:** Method receives base `Event` type -- accessing subclass methods causes errors
**Fix:** Add `if (!($event instanceof MyEvent)) { return; }` as first line

### AP-E04: Listener Registered in boot()
**Severity:** WARNING
**Detection:** `registerEventListener()` called inside `boot()` instead of `register()`
**Impact:** May miss events fired during early app loading phases
**Fix:** Move to `register()` method using `IRegistrationContext`

### AP-E05: Missing parent::__construct() in Custom Event
**Severity:** WARNING
**Detection:** Custom event class constructor without `parent::__construct()` call
**Impact:** Event base class not initialized -- may cause subtle bugs
**Fix:** Add `parent::__construct()` as first line in custom event constructor

### AP-E06: Event Dispatch in Constructor
**Severity:** WARNING
**Detection:** `$this->dispatcher->dispatchTyped()` called inside `__construct()`
**Impact:** Services may not be fully initialized when event fires
**Fix:** Dispatch events in service methods, not constructors

---

## Security Cross-Cutting Anti-Patterns

### AP-S01: Credentials in Log Output
**Severity:** CRITICAL
**Detection:** Logger calls containing `$password`, `$token`, `$secret`, or `$appPassword`
**Impact:** Credentials exposed in log files
**Fix:** NEVER log credential values -- log user IDs or masked references only

### AP-S02: SQL String Concatenation
**Severity:** CRITICAL
**Detection:** `"WHERE id = " . $id` or `"WHERE name = '$name'"` in database code
**Impact:** SQL injection vulnerability
**Fix:** Use `$qb->createNamedParameter($value)` for all dynamic values

### AP-S03: PublicPage on Admin Settings
**Severity:** CRITICAL
**Detection:** `#[PublicPage]` on controllers handling admin configuration
**Impact:** Anonymous users can view or modify admin settings
**Fix:** Remove `#[PublicPage]` -- admin endpoints should use default (admin-only) security

### AP-S04: Missing Input Validation
**Severity:** WARNING
**Detection:** Controller method parameters without type hints
**Impact:** Untyped string injection -- no automatic casting or validation
**Fix:** Add type hints to all parameters: `int $id`, `string $title`, `bool $active`
