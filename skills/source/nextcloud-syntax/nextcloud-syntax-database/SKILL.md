---
name: nextcloud-syntax-database
description: >
  Use when creating database tables, writing migrations, implementing entities and mappers, or building queries.
  Prevents Oracle column name violations, missing migration version numbering, and raw SQL instead of query builder.
  Covers migrations with ISchemaWrapper, Entity definitions with auto-generated getters/setters, QBMapper CRUD operations, query builder with joins and expressions, TTransactional trait, column types, and Oracle/Galera constraints.
  Keywords: ISchemaWrapper, Entity, QBMapper, IQueryBuilder, migration, TTransactional, Oracle, Galera.
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

# nextcloud-syntax-database

## Quick Reference

### Column Types (`OCP\DB\Types`)

| Constant | SQL Type | Notes |
|----------|----------|-------|
| `Types::BIGINT` | BIGINT | ALWAYS use for `id` columns |
| `Types::INTEGER` | INT | Standard integer |
| `Types::FLOAT` | FLOAT | Floating point |
| `Types::BOOLEAN` | BOOLEAN | Oracle: CANNOT be `NOT NULL` |
| `Types::STRING` | VARCHAR | Max 4,000 chars (Oracle limit) |
| `Types::TEXT` | TEXT/CLOB | Large text |
| `Types::BLOB` | BLOB | Binary data |
| `Types::JSON` | JSON/TEXT | JSON data |
| `Types::DATE` | DATE | Date only |
| `Types::TIME` | TIME | Time only |
| `Types::DATETIME` | DATETIME | Date + time |
| `Types::DATETIME_TZ` | DATETIMETZ | Date + time + timezone |

### Database Constraints

| Constraint | Limit | Reason |
|------------|-------|--------|
| Table name | Max 23 characters | `oc_` prefix + Oracle 30-char limit |
| Column name | Max 30 characters | Oracle identifier limit |
| Index name | Max 30 characters | Oracle identifier limit |
| FK name | Max 30 characters | Oracle identifier limit |
| String column | Max 4,000 characters | Oracle VARCHAR2 limit |
| Primary key | REQUIRED on every table | Galera Cluster requirement |
| Boolean NOT NULL | NOT allowed | Oracle does not support it |
| NOT NULL string with empty default | NOT allowed | Oracle treats empty string as NULL |

### Entity Type Mapping

| Property Type | `addType()` Value | Column Type |
|---------------|-------------------|-------------|
| `?int` | `'integer'` | INTEGER/BIGINT |
| `?float` | `'float'` | FLOAT |
| `?bool` | `'boolean'` | BOOLEAN |
| `?string` | (default) | STRING/TEXT |
| `?\DateTime` | `'datetime'` | DATETIME |
| `?array` | `'json'` | JSON |

### QBMapper Methods

| Method | Returns | Throws |
|--------|---------|--------|
| `findEntity($qb)` | Single Entity | `DoesNotExistException`, `MultipleObjectsReturnedException` |
| `findEntities($qb)` | Entity array | -- |
| `insert($entity)` | Inserted Entity | -- |
| `update($entity)` | Updated Entity | -- |
| `delete($entity)` | Deleted Entity | -- |
| `insertOrUpdate($entity)` | Entity | -- |

### Migration Naming Convention

Format: `Version{MajorMinor}Date{YYYYMMDDHHmmss}`

| App Version | Migration Prefix |
|-------------|-----------------|
| 1.0.x | `Version1000` |
| 2.4.x | `Version2004` |
| 24.0.x | `Version24000` |

### Critical Warnings

**NEVER** modify an existing migration file -- create a new migration class instead. Nextcloud tracks which migrations have already executed and will NOT re-run modified migrations.

**NEVER** use raw SQL queries -- ALWAYS use the query builder for cross-database portability (MySQL, PostgreSQL, SQLite, Oracle).

**NEVER** create tables without a primary key -- Galera Cluster replication will fail silently.

**NEVER** exceed 23 characters for table names -- the `oc_` prefix plus Oracle's 30-character limit will cause creation failures.

**NEVER** forget to close cursors on select queries -- call `$result->closeCursor()` after processing. The `findEntity()` and `findEntities()` methods handle this automatically.

**NEVER** use `NOT NULL` on boolean columns if Oracle support is required.

**NEVER** use `NOT NULL` with empty string defaults on string columns -- Oracle treats empty string as NULL, causing constraint violations.

**ALWAYS** include an auto-incremented `id BIGINT` column on every table.

**ALWAYS** use `$qb->createNamedParameter()` for all query values -- never concatenate user input into queries.

**ALWAYS** use the `TTransactional` trait for multi-step operations that must be atomic.

**ALWAYS** pass the table name without the `oc_` prefix to QBMapper and query builder -- the prefix is added automatically.

---

## Decision Tree: Choosing a Database Pattern

```
Need to store data?
├── Simple CRUD with single table?
│   └── Use Entity + QBMapper pattern
│       ├── Define Entity class (extends Entity)
│       ├── Define Mapper class (extends QBMapper)
│       └── Create migration for table schema
├── Complex queries with joins?
│   └── Use query builder directly via IDBConnection
│       ├── $db->getQueryBuilder() for building queries
│       └── Use expressions for WHERE clauses
├── Multiple operations that must succeed/fail together?
│   └── Use TTransactional trait
│       └── Wrap operations in $this->atomic(fn, $db)
└── Schema changes needed?
    ├── New table or column?
    │   └── Create new migration class in lib/Migration/
    ├── Data transformation?
    │   └── Use postSchemaChange() in migration
    └── Add index to large existing table?
        └── Use AddMissingIndicesEvent listener (non-blocking)
```

---

## Essential Patterns

### Pattern 1: Complete Migration (Create Table)

```php
<?php
namespace OCA\MyApp\Migration;

use Closure;
use OCP\DB\ISchemaWrapper;
use OCP\DB\Types;
use OCP\Migration\IOutput;
use OCP\Migration\SimpleMigrationStep;

class Version1000Date20240101000000 extends SimpleMigrationStep {

    public function changeSchema(IOutput $output, Closure $schemaClosure, array $options): ?ISchemaWrapper {
        /** @var ISchemaWrapper $schema */
        $schema = $schemaClosure();

        if (!$schema->hasTable('myapp_items')) {
            $table = $schema->createTable('myapp_items');
            $table->addColumn('id', Types::BIGINT, [
                'autoincrement' => true,
                'notnull' => true,
            ]);
            $table->addColumn('user_id', Types::STRING, [
                'notnull' => true,
                'length' => 64,
            ]);
            $table->addColumn('title', Types::STRING, [
                'notnull' => true,
                'length' => 255,
            ]);
            $table->addColumn('content', Types::TEXT, [
                'notnull' => false,
                'default' => null,
            ]);
            $table->addColumn('created_at', Types::DATETIME, [
                'notnull' => true,
            ]);
            $table->setPrimaryKey(['id']);
            $table->addIndex(['user_id'], 'myapp_items_uid_idx');
        }

        return $schema;
    }
}
```

### Pattern 2: Entity Definition

```php
<?php
namespace OCA\MyApp\Db;

use OCP\AppFramework\Db\Entity;

class Item extends Entity {
    protected ?string $userId = null;
    protected ?string $title = null;
    protected ?string $content = null;
    protected ?int $category = null;
    protected ?bool $archived = null;
    protected ?\DateTime $createdAt = null;

    public function __construct() {
        $this->addType('category', 'integer');
        $this->addType('archived', 'boolean');
        $this->addType('createdAt', 'datetime');
    }
}
```

Property `$userId` auto-generates `getUserId()` / `setUserId()` and maps to column `user_id`.

### Pattern 3: QBMapper with CRUD

```php
<?php
namespace OCA\MyApp\Db;

use OCP\AppFramework\Db\DoesNotExistException;
use OCP\AppFramework\Db\MultipleObjectsReturnedException;
use OCP\AppFramework\Db\QBMapper;
use OCP\IDBConnection;

class ItemMapper extends QBMapper {

    public function __construct(IDBConnection $db) {
        parent::__construct($db, 'myapp_items', Item::class);
    }

    /**
     * @throws DoesNotExistException
     * @throws MultipleObjectsReturnedException
     */
    public function find(int $id, string $userId): Item {
        $qb = $this->db->getQueryBuilder();
        $qb->select('*')
            ->from($this->getTableName())
            ->where($qb->expr()->eq('id', $qb->createNamedParameter($id)))
            ->andWhere($qb->expr()->eq('user_id', $qb->createNamedParameter($userId)));
        return $this->findEntity($qb);
    }

    /**
     * @return Item[]
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

### Pattern 4: Query Builder with Joins

```php
$qb = $this->db->getQueryBuilder();
$qb->select('i.id', 'i.title', 'c.name AS category_name')
    ->from('myapp_items', 'i')
    ->join('i', 'myapp_categories', 'c',
        $qb->expr()->eq('i.category_id', 'c.id'))
    ->where($qb->expr()->eq('i.user_id', $qb->createNamedParameter($userId)))
    ->andWhere($qb->expr()->gte('i.created_at', $qb->createNamedParameter($since, IQueryBuilder::PARAM_DATE)))
    ->orderBy('i.created_at', 'DESC')
    ->setMaxResults(50);

$result = $qb->executeQuery();
$rows = $result->fetchAll();
$result->closeCursor();
```

### Pattern 5: TTransactional for Atomic Operations

```php
<?php
namespace OCA\MyApp\Service;

use OCP\DB\TTransactional;
use OCP\IDBConnection;

class ItemService {
    use TTransactional;

    public function __construct(
        private ItemMapper $mapper,
        private IDBConnection $db,
    ) {}

    public function moveItems(string $fromUser, string $toUser): void {
        $this->atomic(function () use ($fromUser, $toUser) {
            $items = $this->mapper->findAll($fromUser);
            foreach ($items as $item) {
                $item->setUserId($toUser);
                $this->mapper->update($item);
            }
        }, $this->db);
    }
}
```

### Pattern 6: AddMissingIndicesEvent (Non-Blocking Index Creation)

```php
<?php
namespace OCA\MyApp\Listener;

use OCP\DB\Events\AddMissingIndicesEvent;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;

class AddMissingIndicesListener implements IEventListener {

    public function handle(Event $event): void {
        if (!$event instanceof AddMissingIndicesEvent) {
            return;
        }

        $event->addMissingIndex(
            'myapp_items',
            'myapp_items_title_idx',
            ['title']
        );
    }
}
```

Register in `Application::register()`:
```php
$context->registerEventListener(
    AddMissingIndicesEvent::class,
    AddMissingIndicesListener::class
);
```

---

## Reference Links

- [references/methods.md](references/methods.md) -- Migration API, Entity API, QBMapper API, QueryBuilder API
- [references/examples.md](references/examples.md) -- Migration, entity, mapper, query builder patterns
- [references/anti-patterns.md](references/anti-patterns.md) -- Database mistakes, Oracle/Galera issues

### Official Sources

- https://docs.nextcloud.com/server/latest/developer_manual/digging_deeper/database.html
- https://docs.nextcloud.com/server/latest/developer_manual/basics/storage/database.html
- https://docs.nextcloud.com/server/latest/developer_manual/digging_deeper/classloader.html
