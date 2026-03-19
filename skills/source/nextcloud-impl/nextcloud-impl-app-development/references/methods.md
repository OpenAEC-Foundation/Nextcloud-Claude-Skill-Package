# Full-Stack Development Patterns — Method Reference

## Backend Layer Chain

### Entity → Mapper → Service → Controller

Every Nextcloud app follows this data flow:

```
HTTP Request
    → Controller (validates input, delegates to service)
        → Service (business logic, error handling)
            → Mapper (database queries via QBMapper)
                → Entity (data model with auto getters/setters)
                    → Database
```

---

## Entity Definition

Entities extend `OCP\AppFramework\Db\Entity`. Properties use `camelCase` and map automatically to `snake_case` database columns.

```php
<?php
namespace OCA\MyApp\Db;

use OCP\AppFramework\Db\Entity;

class Task extends Entity implements \JsonSerializable {
    protected ?string $title = null;
    protected ?string $description = null;
    protected ?string $userId = null;
    protected ?string $status = null;
    protected ?int $priority = null;
    protected ?string $createdAt = null;
    protected ?string $updatedAt = null;

    public function __construct() {
        $this->addType('priority', 'integer');
    }

    public function jsonSerialize(): array {
        return [
            'id' => $this->id,
            'title' => $this->title,
            'description' => $this->description,
            'userId' => $this->userId,
            'status' => $this->status,
            'priority' => $this->priority,
            'createdAt' => $this->createdAt,
            'updatedAt' => $this->updatedAt,
        ];
    }
}
```

### Entity Rules

- **ALWAYS** implement `\JsonSerializable` when the entity is returned in API responses
- **ALWAYS** use `addType()` in the constructor for non-string fields (`integer`, `boolean`, `float`)
- Property `$userId` maps to column `user_id` automatically
- The `$id` property is inherited from `Entity` -- NEVER redeclare it
- Override `columnToProperty()` / `propertyToColumn()` only for non-standard column naming

### Supported Column Types (`OCP\DB\Types`)

| Type Constant | PHP Type | Use Case |
|--------------|----------|----------|
| `BIGINT` | `int` | Primary keys, foreign keys |
| `INTEGER` | `int` | Counts, flags |
| `STRING` | `string` | Short text (max 4000 for Oracle) |
| `TEXT` | `string` | Long text |
| `BOOLEAN` | `bool` | Flags |
| `FLOAT` | `float` | Decimal values |
| `JSON` | `array` | Structured data |
| `DATETIME` | `string` | Timestamps |

---

## Mapper (QBMapper)

The mapper handles all database queries. Extend `QBMapper` and pass the table name WITHOUT the `oc_` prefix.

```php
<?php
namespace OCA\MyApp\Db;

use OCP\AppFramework\Db\DoesNotExistException;
use OCP\AppFramework\Db\MultipleObjectsReturnedException;
use OCP\AppFramework\Db\QBMapper;
use OCP\IDBConnection;

class TaskMapper extends QBMapper {
    public function __construct(IDBConnection $db) {
        parent::__construct($db, 'myapp_tasks', Task::class);
    }

    /**
     * @throws DoesNotExistException
     * @throws MultipleObjectsReturnedException
     */
    public function find(int $id, string $userId): Task {
        $qb = $this->db->getQueryBuilder();
        $qb->select('*')
            ->from($this->getTableName())
            ->where($qb->expr()->eq('id', $qb->createNamedParameter($id)))
            ->andWhere($qb->expr()->eq('user_id', $qb->createNamedParameter($userId)));
        return $this->findEntity($qb);
    }

    /**
     * @return Task[]
     */
    public function findAll(string $userId): array {
        $qb = $this->db->getQueryBuilder();
        $qb->select('*')
            ->from($this->getTableName())
            ->where($qb->expr()->eq('user_id', $qb->createNamedParameter($userId)));
        return $this->findEntities($qb);
    }
}
```

### Mapper Rules

- **ALWAYS** pass three arguments to parent: `$db`, table name (without `oc_` prefix), entity class
- **ALWAYS** use `$qb->createNamedParameter()` for ALL user input -- NEVER concatenate values into queries
- `findEntity()` throws `DoesNotExistException` if no row found, `MultipleObjectsReturnedException` if >1
- `findEntities()` returns an empty array if no rows match
- Inherited methods: `insert($entity)`, `update($entity)`, `delete($entity)` -- no need to implement these

---

## Service Layer

Services contain business logic and handle exceptions from the mapper layer.

```php
<?php
namespace OCA\MyApp\Service;

use OCA\MyApp\Db\Task;
use OCA\MyApp\Db\TaskMapper;
use OCP\AppFramework\Db\DoesNotExistException;
use OCP\AppFramework\Db\MultipleObjectsReturnedException;
use Psr\Log\LoggerInterface;

class TaskService {
    public function __construct(
        private TaskMapper $mapper,
        private LoggerInterface $logger,
    ) {
    }

    /**
     * @return Task[]
     */
    public function findAll(string $userId): array {
        return $this->mapper->findAll($userId);
    }

    /**
     * @throws NotFoundException
     */
    public function find(int $id, string $userId): Task {
        try {
            return $this->mapper->find($id, $userId);
        } catch (DoesNotExistException | MultipleObjectsReturnedException $e) {
            $this->logger->warning('Task not found', [
                'id' => $id,
                'userId' => $userId,
                'exception' => $e,
            ]);
            throw new NotFoundException('Task not found');
        }
    }

    public function create(string $title, string $description, string $userId): Task {
        $task = new Task();
        $task->setTitle($title);
        $task->setDescription($description);
        $task->setUserId($userId);
        $task->setStatus('open');
        $task->setPriority(0);
        $task->setCreatedAt(date('Y-m-d H:i:s'));
        return $this->mapper->insert($task);
    }

    /**
     * @throws NotFoundException
     */
    public function update(int $id, string $title, string $description,
                           string $status, int $priority, string $userId): Task {
        $task = $this->find($id, $userId);
        $task->setTitle($title);
        $task->setDescription($description);
        $task->setStatus($status);
        $task->setPriority($priority);
        $task->setUpdatedAt(date('Y-m-d H:i:s'));
        return $this->mapper->update($task);
    }

    /**
     * @throws NotFoundException
     */
    public function delete(int $id, string $userId): Task {
        $task = $this->find($id, $userId);
        $this->mapper->delete($task);
        return $task;
    }
}
```

### Service Rules

- **ALWAYS** catch mapper exceptions and rethrow as domain exceptions (e.g., `NotFoundException`)
- **ALWAYS** use `Psr\Log\LoggerInterface` -- NEVER use `OCP\ILogger`
- **NEVER** put HTTP-specific logic (request, response) in services -- that belongs in controllers
- **NEVER** perform I/O in constructors -- constructors should only assign dependencies

---

## Controller Types

### Regular Controller (Page Rendering + Internal AJAX)

```php
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\AppFramework\Http\JSONResponse;
```

- Base URL: `/index.php/apps/{appid}/`
- Returns `TemplateResponse` for pages, `JSONResponse` for AJAX

### OCSController (Structured API)

```php
use OCP\AppFramework\OCSController;
use OCP\AppFramework\Http\DataResponse;
```

- Base URL: `/ocs/v2.php/apps/{appid}/`
- Returns `DataResponse` wrapped in OCS envelope automatically
- Supports format negotiation (JSON/XML)
- External clients send `OCS-APIRequest: true` header

### ApiController (REST with CORS)

```php
use OCP\AppFramework\ApiController;
```

- Extends `Controller` with CORS support
- Use for cross-origin REST APIs

---

## Route Definition Patterns

### Standard Routes

```php
'routes' => [
    ['name' => 'page#index', 'url' => '/', 'verb' => 'GET'],
    ['name' => 'task#create', 'url' => '/tasks', 'verb' => 'POST'],
    ['name' => 'task#update', 'url' => '/tasks/{id}', 'verb' => 'PUT'],
],
```

### OCS Routes

```php
'ocs' => [
    ['name' => 'task_api#index', 'url' => '/api/v1/tasks', 'verb' => 'GET'],
],
```

### Resource Routes (Auto-CRUD)

```php
'resources' => [
    'task' => ['url' => '/tasks'],
],
```

Generates: `index()`, `show(int $id)`, `create()`, `update(int $id)`, `destroy(int $id)`.

---

## Security Attributes

| Attribute | When to Use |
|-----------|------------|
| `#[NoAdminRequired]` | ALWAYS add for endpoints accessible by regular users |
| `#[NoCSRFRequired]` | ONLY for the page-rendering controller that returns `TemplateResponse` |
| `#[PublicPage]` | ONLY for endpoints that must work without any authentication |
| `#[UserRateLimit(limit: N, period: S)]` | Add to sensitive operations (create, delete) |
| `#[BruteForceProtection(action: 'name')]` | Add to authentication-related endpoints |

---

## Initial State API

### PHP Side

```php
use OCP\AppFramework\Services\IInitialState;

// Eager -- always serialized into the HTML page
$this->initialState->provideInitialState('key', $value);

// Lazy -- serialized only when JS calls loadState()
$this->initialState->provideLazyInitialState('key', fn () => $expensiveData);
```

### JavaScript Side

```javascript
import { loadState } from '@nextcloud/initial-state'

// With fallback (safe)
const data = loadState('appid', 'key', defaultValue)

// Without fallback (throws Error if key missing)
const data = loadState('appid', 'key')
```

**ALWAYS** use `provideLazyInitialState()` for large datasets or data that is not always needed.

---

## Frontend URL Generation

```javascript
import { generateUrl } from '@nextcloud/router'
import { generateOcsUrl } from '@nextcloud/router'

// Regular route
const url = generateUrl('/apps/myapp/tasks/{id}', { id: 42 })

// OCS route
const ocsUrl = generateOcsUrl('/apps/myapp/api/v1/tasks')
```

**ALWAYS** use `generateOcsUrl()` for OCS endpoints -- it correctly includes `/ocs/v2.php`.

**ALWAYS** use `generateUrl()` for regular routes -- it correctly includes `/index.php`.

---

## Database Migration

```php
<?php
namespace OCA\MyApp\Migration;

use Closure;
use OCP\DB\ISchemaWrapper;
use OCP\DB\Types;
use OCP\Migration\IOutput;
use OCP\Migration\SimpleMigrationStep;

class Version1000Date20240101000000 extends SimpleMigrationStep {
    public function changeSchema(IOutput $output, Closure $schemaClosure, array $options) {
        /** @var ISchemaWrapper $schema */
        $schema = $schemaClosure();

        if (!$schema->hasTable('myapp_tasks')) {
            $table = $schema->createTable('myapp_tasks');
            $table->addColumn('id', Types::BIGINT, [
                'autoincrement' => true,
                'notnull' => true,
            ]);
            $table->addColumn('title', Types::STRING, [
                'notnull' => true,
                'length' => 255,
            ]);
            $table->addColumn('description', Types::TEXT, [
                'notnull' => false,
                'default' => '',
            ]);
            $table->addColumn('user_id', Types::STRING, [
                'notnull' => true,
                'length' => 64,
            ]);
            $table->addColumn('status', Types::STRING, [
                'notnull' => true,
                'length' => 20,
                'default' => 'open',
            ]);
            $table->addColumn('priority', Types::INTEGER, [
                'notnull' => true,
                'default' => 0,
            ]);
            $table->addColumn('created_at', Types::DATETIME, [
                'notnull' => true,
            ]);
            $table->addColumn('updated_at', Types::DATETIME, [
                'notnull' => false,
            ]);
            $table->setPrimaryKey(['id']);
            $table->addIndex(['user_id'], 'myapp_tasks_user_idx');
        }

        return $schema;
    }
}
```

### Migration Rules

- **ALWAYS** use `if (!$schema->hasTable(...))` before creating tables
- **ALWAYS** include a `BIGINT` auto-increment `id` column as primary key
- **ALWAYS** define explicit primary keys (Galera Cluster requires it)
- **ALWAYS** use globally unique index names (prefix with app name)
- **NEVER** modify existing migration files -- create new migration classes
- Table names: max 23 characters (27 total with `oc_` prefix for Oracle compatibility)
