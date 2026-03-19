# Anti-Patterns — App Development Workflow Mistakes

## AP-1: Missing Namespace in info.xml

**Wrong:**
```xml
<info>
    <id>myapp</id>
    <name>My App</name>
    <!-- No <namespace> element -->
</info>
```

**Impact:** Auto-wiring silently fails. Controllers cannot be resolved. The app loads but no routes work, producing 404 errors with no clear error message.

**Correct:**
```xml
<info>
    <id>myapp</id>
    <name>My App</name>
    <namespace>MyApp</namespace>
</info>
```

**Rule:** ALWAYS declare `<namespace>` in `info.xml`. The value determines the `OCA\{Namespace}\` PHP namespace prefix.

---

## AP-2: Using Server::get() Instead of Constructor Injection

**Wrong:**
```php
class TaskService {
    public function findAll(): array {
        $mapper = \OCP\Server::get(TaskMapper::class);
        return $mapper->findAll();
    }
}
```

**Impact:** Untestable code. Cannot mock dependencies in unit tests. Hides class dependencies.

**Correct:**
```php
class TaskService {
    public function __construct(
        private TaskMapper $mapper,
    ) {
    }

    public function findAll(): array {
        return $this->mapper->findAll();
    }
}
```

**Rule:** ALWAYS use constructor injection. NEVER use `\OCP\Server::get()` or `\OC::$server->get()`.

---

## AP-3: Querying Other Apps' Services in register()

**Wrong:**
```php
public function register(IRegistrationContext $context): void {
    $otherService = \OCP\Server::get(OtherApp\Service::class);
    // This may fail -- OtherApp may not be registered yet
}
```

**Impact:** Race condition. If OtherApp loads after your app, the service resolution fails silently or throws.

**Correct:**
```php
public function register(IRegistrationContext $context): void {
    // Only use IRegistrationContext methods here
    $context->registerEventListener(SomeEvent::class, MyListener::class);
}

public function boot(IBootContext $context): void {
    // Safe to query other apps' services here
    $context->injectFn(function (OtherApp\Service $service) {
        $service->registerSomething();
    });
}
```

**Rule:** NEVER query services in `register()`. Use `boot()` for cross-app initialization.

---

## AP-4: Forgetting Security Attributes on Controllers

**Wrong:**
```php
class TaskApiController extends OCSController {
    // No attributes -- defaults to admin-only!
    public function index(): DataResponse {
        return new DataResponse($this->service->findAll($this->userId));
    }
}
```

**Impact:** Regular users get 403 Forbidden. Only admins can access the endpoint. This is the Nextcloud default security posture.

**Correct:**
```php
class TaskApiController extends OCSController {
    #[NoAdminRequired]
    public function index(): DataResponse {
        return new DataResponse($this->service->findAll($this->userId));
    }
}
```

**Rule:** ALWAYS add `#[NoAdminRequired]` for endpoints accessible by regular users. The default is admin-only.

---

## AP-5: Using Raw fetch() or Plain axios

**Wrong:**
```javascript
// Missing CSRF token, missing auth headers
const response = await fetch('/apps/myapp/api/tasks')

// Or plain axios without Nextcloud wrapper
import axios from 'axios'
const response = await axios.get('/apps/myapp/api/tasks')
```

**Impact:** Request fails with 401 (no auth) or 403 (no CSRF token). The response is a login redirect HTML page instead of JSON.

**Correct:**
```javascript
import axios from '@nextcloud/axios'
import { generateUrl } from '@nextcloud/router'

const url = generateUrl('/apps/myapp/api/tasks')
const response = await axios.get(url)
```

**Rule:** ALWAYS use `@nextcloud/axios` -- it automatically includes authentication headers and CSRF tokens.

---

## AP-6: Hardcoding URLs Instead of Using Router

**Wrong:**
```javascript
const response = await axios.get('/ocs/v2.php/apps/myapp/api/v1/tasks')
```

**Impact:** Breaks when Nextcloud is installed in a subdirectory (e.g., `/nextcloud/ocs/v2.php/...`).

**Correct:**
```javascript
import { generateOcsUrl } from '@nextcloud/router'

const url = generateOcsUrl('/apps/myapp/api/v1/tasks')
const response = await axios.get(url)
```

**Rule:** ALWAYS use `generateUrl()` for regular routes and `generateOcsUrl()` for OCS routes. NEVER hardcode URL paths.

---

## AP-7: loadState() Without Fallback

**Wrong:**
```javascript
// Throws Error if 'config' was not provided by PHP
const config = loadState('myapp', 'config')
```

**Impact:** JavaScript error crashes the entire Vue app if the PHP controller did not call `provideInitialState('config', ...)`.

**Correct:**
```javascript
const config = loadState('myapp', 'config', { defaultKey: 'defaultValue' })
```

**Rule:** ALWAYS provide a fallback value as the third argument to `loadState()` for any data that might not be present.

---

## AP-8: Injecting Data via Global Variables

**Wrong:**
```php
// templates/main.php
<script>
var MYAPP_CONFIG = <?php echo json_encode($config); ?>;
</script>
```

**Impact:** Bypasses Nextcloud's Content Security Policy (inline scripts blocked). XSS vulnerability if data is not properly escaped. Not discoverable by other code.

**Correct:**
```php
// In controller
$this->initialState->provideInitialState('config', $config);
```
```javascript
// In JavaScript
const config = loadState('myapp', 'config', {})
```

**Rule:** ALWAYS use the initial state bridge (`provideInitialState` / `loadState`). NEVER inject data via inline scripts or global variables.

---

## AP-9: Modifying Existing Database Migrations

**Wrong:**
```php
// Editing Version1000Date20240101000000.php to add a column
// This file has already been executed on production servers
```

**Impact:** The migration will NOT re-run. Nextcloud tracks executed migrations by class name. Existing installations will be missing the new column, causing runtime SQL errors.

**Correct:**
```php
// Create a NEW migration file
// lib/Migration/Version1000Date20240215000000.php
class Version1000Date20240215000000 extends SimpleMigrationStep {
    public function changeSchema(IOutput $output, Closure $schemaClosure, array $options) {
        $schema = $schemaClosure();
        if ($schema->hasTable('myapp_tasks')) {
            $table = $schema->getTable('myapp_tasks');
            if (!$table->hasColumn('new_column')) {
                $table->addColumn('new_column', Types::STRING, [
                    'notnull' => false, 'length' => 255,
                ]);
            }
        }
        return $schema;
    }
}
```

**Rule:** NEVER modify existing migrations. ALWAYS create new migration classes for schema changes.

---

## AP-10: Hardcoding Colors in CSS

**Wrong:**
```css
.my-component {
    background-color: #ffffff;
    color: #222222;
    border: 1px solid #0082c9;
}
```

**Impact:** Breaks dark mode. Breaks custom themes. Users see white backgrounds in dark mode, making text unreadable.

**Correct:**
```css
.my-component {
    background-color: var(--color-main-background);
    color: var(--color-main-text);
    border: 1px solid var(--color-primary-element);
}
```

**Rule:** ALWAYS use CSS custom properties (`--color-*`) for all colors. NEVER hardcode color values.

---

## AP-11: Barrel Imports from @nextcloud/vue

**Wrong:**
```javascript
import { NcButton, NcContent, NcAppContent } from '@nextcloud/vue'
```

**Impact:** Imports the entire component library. Bundle size increases dramatically (hundreds of KB of unused components).

**Correct:**
```javascript
import NcButton from '@nextcloud/vue/components/NcButton'
import NcContent from '@nextcloud/vue/components/NcContent'
import NcAppContent from '@nextcloud/vue/components/NcAppContent'
```

**Rule:** ALWAYS use direct component imports from `@nextcloud/vue/components/{Name}`. NEVER use barrel imports in production code.

---

## AP-12: Using OCP\ILogger

**Wrong:**
```php
use OCP\ILogger;

class MyService {
    public function __construct(private ILogger $logger) { }
}
```

**Impact:** Deprecated since NC 24. Will be removed in a future version. Does not follow PSR-3 standard.

**Correct:**
```php
use Psr\Log\LoggerInterface;

class MyService {
    public function __construct(private LoggerInterface $logger) { }
}
```

**Rule:** ALWAYS use `Psr\Log\LoggerInterface`. NEVER use `OCP\ILogger`.

---

## AP-13: Missing Dialogs Style Import

**Wrong:**
```javascript
import { showSuccess, showError } from '@nextcloud/dialogs'
// Forgot to import styles
showSuccess('Saved!')
```

**Impact:** Toast notifications render without any styling -- invisible or broken layout.

**Correct:**
```javascript
import { showSuccess, showError } from '@nextcloud/dialogs'
import '@nextcloud/dialogs/style.css'

showSuccess('Saved!')
```

**Rule:** ALWAYS import `@nextcloud/dialogs/style.css` when using dialog/toast functions.

---

## AP-14: Using Controller for OCS Routes

**Wrong:**
```php
// Using regular Controller with OCS routes
class ApiController extends Controller {
    public function getData(): DataResponse {
        return new DataResponse(['key' => 'value']);
    }
}
```
```php
'ocs' => [
    ['name' => 'api#getData', 'url' => '/api/v1/data', 'verb' => 'GET'],
],
```

**Impact:** The OCS response envelope is not generated. Clients expecting `{ ocs: { data: ... } }` get raw data instead.

**Correct:**
```php
class ApiController extends OCSController {
    public function getData(): DataResponse {
        return new DataResponse(['key' => 'value']);
    }
}
```

**Rule:** ALWAYS extend `OCSController` for endpoints defined in the `ocs` routes array. NEVER use regular `Controller` with OCS routes.

---

## AP-15: Tables Without Primary Keys

**Wrong:**
```php
$table = $schema->createTable('myapp_data');
$table->addColumn('key', Types::STRING, ['notnull' => true, 'length' => 64]);
$table->addColumn('value', Types::TEXT, ['notnull' => false]);
// No primary key defined
```

**Impact:** Fails on Galera Cluster (used by many production Nextcloud deployments). May cause replication issues on MySQL.

**Correct:**
```php
$table = $schema->createTable('myapp_data');
$table->addColumn('id', Types::BIGINT, ['autoincrement' => true, 'notnull' => true]);
$table->addColumn('key', Types::STRING, ['notnull' => true, 'length' => 64]);
$table->addColumn('value', Types::TEXT, ['notnull' => false]);
$table->setPrimaryKey(['id']);
```

**Rule:** ALWAYS define a primary key on every table. ALWAYS include an auto-increment `BIGINT` id column.
