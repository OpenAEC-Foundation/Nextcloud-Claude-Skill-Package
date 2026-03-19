# Database Error Scenarios with Fixes

## Scenario 1: Migration Silently Ignored on Upgrade

### Symptom
App version 1.1 adds a `priority` column. New installations have the column. Existing users who upgrade from 1.0 do NOT have the column. No errors in the log.

### Root Cause
The developer edited the existing `Version1000Date20240101000000` migration instead of creating a new one. Since that migration class name already exists in `oc_migrations`, Nextcloud skips it entirely.

### Wrong Approach
```php
// File: lib/Migration/Version1000Date20240101000000.php (EDITED after release)
class Version1000Date20240101000000 extends SimpleMigrationStep {
    public function changeSchema(...): ?ISchemaWrapper {
        $schema = $schemaClosure();
        $table = $schema->createTable('myapp_items');
        $table->addColumn('id', Types::BIGINT, ['autoincrement' => true, 'notnull' => true]);
        $table->addColumn('title', Types::STRING, ['notnull' => true, 'length' => 255]);
        $table->addColumn('priority', Types::INTEGER, ['notnull' => true, 'default' => 0]); // Added later
        $table->setPrimaryKey(['id']);
        return $schema;
    }
}
```

### Correct Fix
```php
// File: lib/Migration/Version1001Date20240215120000.php (NEW file)
class Version1001Date20240215120000 extends SimpleMigrationStep {
    public function changeSchema(IOutput $output, Closure $schemaClosure, array $options): ?ISchemaWrapper {
        $schema = $schemaClosure();
        $table = $schema->getTable('myapp_items');
        if (!$table->hasColumn('priority')) {
            $table->addColumn('priority', Types::INTEGER, ['notnull' => true, 'default' => 0]);
        }
        return $schema;
    }
}
```

---

## Scenario 2: Data Migration Reads NULL for New Column

### Symptom
Migration adds a `user_id` column and immediately tries to copy data from `uid` column into it. The copy query silently does nothing or fails with "column not found."

### Root Cause
Data queries inside `changeSchema()` run BEFORE the schema change is actually applied to the database.

### Wrong Approach
```php
public function changeSchema(IOutput $output, Closure $schemaClosure, array $options): ?ISchemaWrapper {
    $schema = $schemaClosure();
    $table = $schema->getTable('myapp_items');
    $table->addColumn('user_id', Types::STRING, ['notnull' => false, 'length' => 64]);

    // WRONG: Column does not exist yet in the actual database
    $qb = $this->db->getQueryBuilder();
    $qb->update('myapp_items')->set('user_id', 'uid')->executeStatement();

    return $schema;
}
```

### Correct Fix
```php
public function __construct(private IDBConnection $db) {}

public function changeSchema(IOutput $output, Closure $schemaClosure, array $options): ?ISchemaWrapper {
    $schema = $schemaClosure();
    $table = $schema->getTable('myapp_items');
    if (!$table->hasColumn('user_id')) {
        $table->addColumn('user_id', Types::STRING, ['notnull' => false, 'length' => 64]);
    }
    return $schema;
}

public function postSchemaChange(IOutput $output, Closure $schemaClosure, array $options): void {
    // NOW the column exists in the actual database
    $qb = $this->db->getQueryBuilder();
    $qb->update('myapp_items')
        ->set('user_id', 'uid')
        ->executeStatement();
}
```

---

## Scenario 3: Entity Returns Wrong Types

### Symptom
Controller receives an entity where `$item->getCount()` returns `"5"` (string) instead of `5` (int), and `$item->isActive()` returns `"1"` instead of `true`. JSON response sends string values.

### Root Cause
Missing `addType()` calls in the entity constructor. The database driver returns all values as strings by default.

### Wrong Approach
```php
class Item extends Entity {
    protected ?int $count = null;
    protected ?bool $active = null;
    protected ?\DateTime $createdAt = null;
    // No constructor — all values returned as strings
}
```

### Correct Fix
```php
class Item extends Entity {
    protected ?int $count = null;
    protected ?bool $active = null;
    protected ?\DateTime $createdAt = null;

    public function __construct() {
        $this->addType('count', 'integer');
        $this->addType('active', 'boolean');
        $this->addType('createdAt', 'datetime');
    }
}
```

---

## Scenario 4: Oracle Deployment Failure — Table Name Too Long

### Symptom
App installs successfully on MySQL and PostgreSQL. On Oracle, migration fails with `ORA-00972: identifier is too long`.

### Root Cause
Table name `myapp_project_collaborators` is 31 characters. With the `oc_` prefix, the total is 35, exceeding Oracle's 30-character limit.

### Wrong Approach
```php
$schema->createTable('myapp_project_collaborators'); // 31 chars + oc_ = 35 total
```

### Correct Fix
```php
$schema->createTable('myapp_proj_collabs'); // 18 chars + oc_ = 22 total
```

**Naming strategy**: Abbreviate the middle of descriptive names. Keep the app prefix and a recognizable suffix. Examples:
- `myapp_project_collaborators` → `myapp_proj_collabs` (18 chars)
- `myapp_notification_settings` → `myapp_notif_sets` (16 chars)
- `myapp_document_attachments` → `myapp_doc_attach` (16 chars)

---

## Scenario 5: Oracle Failure — Boolean NOT NULL

### Symptom
`INSERT` statements fail on Oracle with `ORA-01400: cannot insert NULL into ("OC_MYAPP_ITEMS"."IS_ACTIVE")`. The same code works on MySQL and PostgreSQL.

### Root Cause
Boolean column declared as `NOT NULL`. Oracle implements booleans as NUMBER(1) and does not support NOT NULL constraints on these columns.

### Wrong Approach
```php
$table->addColumn('is_active', Types::BOOLEAN, [
    'notnull' => true,
    'default' => false,
]);
```

### Correct Fix
```php
$table->addColumn('is_active', Types::BOOLEAN, [
    'notnull' => false,
    'default' => false,
]);
```

---

## Scenario 6: Connection Exhaustion from Unclosed Cursors

### Symptom
App works fine under low load. Under sustained traffic, database connections run out: "SQLSTATE[HY000] [1040] Too many connections" or similar. Server becomes unresponsive.

### Root Cause
Query results not closed with `closeCursor()`. Each unclosed result holds a database connection handle.

### Wrong Approach
```php
public function getActiveUsers(): array {
    $qb = $this->db->getQueryBuilder();
    $qb->select('*')->from('myapp_items')->where($qb->expr()->eq('active', $qb->createNamedParameter(true, IQueryBuilder::PARAM_BOOL)));
    $result = $qb->executeQuery();
    return $result->fetchAll();
    // Missing: $result->closeCursor()
}
```

### Correct Fix
```php
public function getActiveUsers(): array {
    $qb = $this->db->getQueryBuilder();
    $qb->select('*')->from('myapp_items')->where($qb->expr()->eq('active', $qb->createNamedParameter(true, IQueryBuilder::PARAM_BOOL)));
    $result = $qb->executeQuery();
    $rows = $result->fetchAll();
    $result->closeCursor();
    return $rows;
}
```

**Best practice**: Use `QBMapper::findEntity()` or `findEntities()` when working with entities — they close cursors automatically.

---

## Scenario 7: Galera Cluster Replication Failure

### Symptom
Data inserted on one Galera cluster node does not appear on other nodes. No error messages in the Nextcloud log. The table simply does not replicate.

### Root Cause
Table was created without a primary key. Galera Cluster requires primary keys on ALL tables for row-based replication.

### Wrong Approach
```php
$table = $schema->createTable('myapp_tags');
$table->addColumn('item_id', Types::BIGINT, ['notnull' => true]);
$table->addColumn('tag', Types::STRING, ['notnull' => true, 'length' => 64]);
// No primary key defined
```

### Correct Fix
```php
$table = $schema->createTable('myapp_tags');
$table->addColumn('id', Types::BIGINT, ['autoincrement' => true, 'notnull' => true]);
$table->addColumn('item_id', Types::BIGINT, ['notnull' => true]);
$table->addColumn('tag', Types::STRING, ['notnull' => true, 'length' => 64]);
$table->setPrimaryKey(['id']);
$table->addIndex(['item_id'], 'myapp_tags_item_idx');
```

---

## Scenario 8: Partial Data After Transaction Error

### Symptom
When creating two related records, the first record is saved but the second fails. The database is left in an inconsistent state with an orphaned first record.

### Root Cause
Manual `beginTransaction()` without try/catch/rollBack, or no transaction at all.

### Wrong Approach
```php
$this->db->beginTransaction();
$this->mapper->insert($parent);
$this->mapper->insert($child); // If this throws, $parent is already committed
$this->db->commit();
```

### Correct Fix
```php
use OCP\DB\TTransactional;

class MyService {
    use TTransactional;

    public function createParentAndChild(Entity $parent, Entity $child): void {
        $this->atomic(function () use ($parent, $child) {
            $this->mapper->insert($parent);
            $child->setParentId($parent->getId());
            $this->mapper->insert($child);
        }, $this->db);
        // If $child insert fails, $parent insert is automatically rolled back
    }
}
```

---

## Scenario 9: Duplicate Index Name Collision

### Symptom
`Index already exists` error during app installation. The index name collides with an index from another app.

### Root Cause
Generic index name (e.g., `user_id_idx`) used without app-specific prefix.

### Wrong Approach
```php
$table->addIndex(['user_id'], 'user_id_idx');           // Too generic
$table->addIndex(['status'], 'status_idx');               // Too generic
```

### Correct Fix
```php
$table->addIndex(['user_id'], 'myapp_items_uid_idx');     // App-prefixed, unique
$table->addIndex(['status'], 'myapp_items_status_idx');   // App-prefixed, unique
```

**Naming convention**: `{appname}_{table}_{column_abbreviations}_idx` for regular indices, `{appname}_{table}_{column_abbreviations}_uniq` for unique indices.

---

## Scenario 10: Lock Timeout in Transaction

### Symptom
Under concurrent usage, database operations fail with lock wait timeout or deadlock errors. Performance degrades significantly.

### Root Cause
An HTTP API call or heavy file processing was performed inside a database transaction, holding row locks for seconds.

### Wrong Approach
```php
$this->atomic(function () use ($itemId) {
    $item = $this->mapper->find($itemId, $this->userId);
    // SLOW: External API call while holding database locks
    $result = $this->httpClient->get('https://api.example.com/validate/' . $item->getExternalId());
    $item->setValidated($result->getStatusCode() === 200);
    $this->mapper->update($item);
}, $this->db);
```

### Correct Fix
```php
// Step 1: Read data (no transaction needed for single read)
$item = $this->mapper->find($itemId, $this->userId);

// Step 2: Slow work OUTSIDE the transaction
$result = $this->httpClient->get('https://api.example.com/validate/' . $item->getExternalId());
$isValid = $result->getStatusCode() === 200;

// Step 3: Fast database update inside transaction
$this->atomic(function () use ($itemId, $isValid) {
    $item = $this->mapper->find($itemId, $this->userId);
    $item->setValidated($isValid);
    $this->mapper->update($item);
}, $this->db);
```
