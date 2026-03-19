# Database Layer — Anti-Patterns

## Migration Anti-Patterns

### AP-1: Modifying Existing Migration Files

**NEVER** edit a migration file after it has been committed or deployed.

Nextcloud stores executed migration class names in the `oc_migrations` table. If you modify an already-executed migration, the changes will NOT run. Users who installed your app before the change will have a different schema than new users.

**Wrong:**
```php
// Editing Version1000Date20240101000000 to add a column after release
class Version1000Date20240101000000 extends SimpleMigrationStep {
    public function changeSchema(...): ?ISchemaWrapper {
        $table = $schema->createTable('myapp_items');
        $table->addColumn('id', Types::BIGINT, ['autoincrement' => true, 'notnull' => true]);
        $table->addColumn('title', Types::STRING, ['notnull' => true, 'length' => 255]);
        $table->addColumn('priority', Types::INTEGER, ['notnull' => true, 'default' => 0]); // ADDED LATER — WRONG
        $table->setPrimaryKey(['id']);
        return $schema;
    }
}
```

**Correct:** Create a new migration class:
```php
class Version1001Date20240215000000 extends SimpleMigrationStep {
    public function changeSchema(...): ?ISchemaWrapper {
        $schema = $schemaClosure();
        $table = $schema->getTable('myapp_items');
        if (!$table->hasColumn('priority')) {
            $table->addColumn('priority', Types::INTEGER, ['notnull' => true, 'default' => 0]);
        }
        return $schema;
    }
}
```

### AP-2: Missing Existence Checks in Migrations

**NEVER** assume tables or columns do not already exist. Migrations may re-run during development or upgrades.

**Wrong:**
```php
$table = $schema->createTable('myapp_items'); // Crashes if table exists
```

**Correct:**
```php
if (!$schema->hasTable('myapp_items')) {
    $table = $schema->createTable('myapp_items');
    // ...
}
```

### AP-3: Data Migration in changeSchema()

**NEVER** run data queries inside `changeSchema()`. The schema has not been applied yet at that point.

**Wrong:**
```php
public function changeSchema(...): ?ISchemaWrapper {
    $schema = $schemaClosure();
    $table = $schema->getTable('myapp_items');
    $table->addColumn('new_col', Types::STRING, ['notnull' => false]);

    // WRONG: new_col does not exist yet in the actual database
    $this->db->getQueryBuilder()
        ->update('myapp_items')
        ->set('new_col', 'old_col')
        ->executeStatement();

    return $schema;
}
```

**Correct:** Use `postSchemaChange()` for data operations:
```php
public function changeSchema(...): ?ISchemaWrapper {
    $schema = $schemaClosure();
    $table = $schema->getTable('myapp_items');
    $table->addColumn('new_col', Types::STRING, ['notnull' => false]);
    return $schema;
}

public function postSchemaChange(...): void {
    $qb = $this->db->getQueryBuilder();
    $qb->update('myapp_items')
        ->set('new_col', 'old_col')
        ->executeStatement();
}
```

---

## Oracle Compatibility Anti-Patterns

### AP-4: Table Name Exceeds 23 Characters

**NEVER** use table names longer than 23 characters. With the `oc_` prefix (4 chars), the total becomes 27. Oracle has a 30-character limit for identifiers, leaving only 23 for the table name.

**Wrong:**
```php
$schema->createTable('myapp_project_collaborators'); // 31 chars with oc_ prefix
```

**Correct:**
```php
$schema->createTable('myapp_proj_collabs'); // 22 chars with oc_ prefix = 26
```

### AP-5: NOT NULL Boolean Columns

**NEVER** mark boolean columns as `NOT NULL` if you need Oracle compatibility. Oracle does not support `NOT NULL` constraints on boolean columns.

**Wrong:**
```php
$table->addColumn('is_active', Types::BOOLEAN, [
    'notnull' => true,  // Fails on Oracle
    'default' => false,
]);
```

**Correct:**
```php
$table->addColumn('is_active', Types::BOOLEAN, [
    'notnull' => false,  // Oracle-compatible
    'default' => false,
]);
```

### AP-6: NOT NULL String with Empty Default

**NEVER** combine `NOT NULL` with an empty string default on string columns. Oracle treats empty strings as NULL, causing constraint violations.

**Wrong:**
```php
$table->addColumn('label', Types::STRING, [
    'notnull' => true,
    'default' => '',     // Oracle: empty string = NULL → constraint violation
    'length' => 255,
]);
```

**Correct:**
```php
$table->addColumn('label', Types::STRING, [
    'notnull' => false,  // Allow NULL
    'default' => null,
    'length' => 255,
]);
```

### AP-7: Identifier Names Exceeding 30 Characters

**NEVER** use column, index, or foreign key names longer than 30 characters.

**Wrong:**
```php
$table->addColumn('last_notification_sent_timestamp', Types::DATETIME, [...]); // 35 chars
$table->addIndex(['user_id', 'status'], 'myapp_items_user_id_status_created_idx'); // 39 chars
```

**Correct:**
```php
$table->addColumn('last_notif_sent_at', Types::DATETIME, [...]); // 18 chars
$table->addIndex(['user_id', 'status'], 'myapp_items_uid_stat_idx'); // 24 chars
```

---

## Galera Cluster Anti-Patterns

### AP-8: Tables Without Primary Keys

**NEVER** create a table without a primary key. Galera Cluster uses row-based replication and requires primary keys on ALL tables to identify rows for replication.

**Wrong:**
```php
$table = $schema->createTable('myapp_logs');
$table->addColumn('id', Types::BIGINT, ['autoincrement' => true, 'notnull' => true]);
$table->addColumn('message', Types::TEXT, ['notnull' => false]);
// Missing: $table->setPrimaryKey(['id']);
```

**Correct:**
```php
$table = $schema->createTable('myapp_logs');
$table->addColumn('id', Types::BIGINT, ['autoincrement' => true, 'notnull' => true]);
$table->addColumn('message', Types::TEXT, ['notnull' => false]);
$table->setPrimaryKey(['id']);
```

---

## Query Anti-Patterns

### AP-9: Raw SQL Queries

**NEVER** use raw SQL strings. The query builder handles dialect differences between MySQL, PostgreSQL, SQLite, and Oracle.

**Wrong:**
```php
$sql = "SELECT * FROM oc_myapp_items WHERE user_id = '$userId'";
$result = $this->db->executeQuery($sql);
```

**Correct:**
```php
$qb = $this->db->getQueryBuilder();
$qb->select('*')
    ->from('myapp_items')
    ->where($qb->expr()->eq('user_id', $qb->createNamedParameter($userId)));
$result = $qb->executeQuery();
```

### AP-10: String Concatenation in Queries (SQL Injection)

**NEVER** concatenate variables into query strings. ALWAYS use named parameters.

**Wrong:**
```php
$qb->where("user_id = '$userId'"); // SQL injection vulnerability
$qb->where($qb->expr()->eq('user_id', "'$userId'")); // Still vulnerable
```

**Correct:**
```php
$qb->where($qb->expr()->eq('user_id', $qb->createNamedParameter($userId)));
```

### AP-11: Unclosed Result Cursors

**NEVER** forget to call `closeCursor()` after processing query results. Open cursors hold database connections and cause resource leaks.

**Wrong:**
```php
$result = $qb->executeQuery();
$rows = $result->fetchAll();
// Missing: $result->closeCursor();
return $rows;
```

**Correct:**
```php
$result = $qb->executeQuery();
$rows = $result->fetchAll();
$result->closeCursor();
return $rows;
```

Note: `QBMapper::findEntity()` and `QBMapper::findEntities()` close cursors automatically.

### AP-12: LIKE Without Escaping

**NEVER** pass user input directly into LIKE patterns without escaping. The `%` and `_` characters are wildcards in SQL.

**Wrong:**
```php
$qb->andWhere($qb->expr()->like('name',
    $qb->createNamedParameter('%' . $userInput . '%'))); // User input may contain % or _
```

**Correct:**
```php
$qb->andWhere($qb->expr()->iLike('name',
    $qb->createNamedParameter('%' . $this->db->escapeLikeParameter($userInput) . '%')));
```

---

## Entity/Mapper Anti-Patterns

### AP-13: Missing addType() for Non-String Properties

**NEVER** omit `addType()` for integer, boolean, float, datetime, or json properties. Without it, values are returned as strings from the database.

**Wrong:**
```php
class Item extends Entity {
    protected ?int $count = null;
    protected ?bool $active = null;
    // Missing addType calls — $count will be string "5", $active will be string "1"
}
```

**Correct:**
```php
class Item extends Entity {
    protected ?int $count = null;
    protected ?bool $active = null;

    public function __construct() {
        $this->addType('count', 'integer');
        $this->addType('active', 'boolean');
    }
}
```

### AP-14: Including oc_ Prefix in Table Names

**NEVER** include the `oc_` prefix when passing table names to QBMapper or the query builder. The prefix is added automatically.

**Wrong:**
```php
class ItemMapper extends QBMapper {
    public function __construct(IDBConnection $db) {
        parent::__construct($db, 'oc_myapp_items', Item::class); // WRONG: oc_ prefix included
    }
}
```

**Correct:**
```php
class ItemMapper extends QBMapper {
    public function __construct(IDBConnection $db) {
        parent::__construct($db, 'myapp_items', Item::class); // Correct: no prefix
    }
}
```

---

## Transaction Anti-Patterns

### AP-15: Manual Transaction Without Proper Error Handling

**NEVER** use manual `beginTransaction()`/`commit()` without a try/catch that calls `rollBack()`. Use `TTransactional` instead.

**Wrong:**
```php
$this->db->beginTransaction();
$this->mapper->insert($entity1);
$this->mapper->insert($entity2); // If this throws, the first insert is committed
$this->db->commit();
```

**Correct:**
```php
use OCP\DB\TTransactional;

class MyService {
    use TTransactional;

    public function createBoth(): void {
        $this->atomic(function () {
            $this->mapper->insert($entity1);
            $this->mapper->insert($entity2);
        }, $this->db);
    }
}
```

### AP-16: Long-Running Operations Inside Transactions

**NEVER** perform slow operations (API calls, file I/O, heavy computation) inside a transaction. Transactions hold database locks and long transactions cause contention and timeouts.

**Wrong:**
```php
$this->atomic(function () {
    $item = $this->mapper->find($id, $userId);
    $result = $this->httpClient->get('https://external-api.com/validate'); // SLOW
    $item->setStatus($result->getStatus());
    $this->mapper->update($item);
}, $this->db);
```

**Correct:**
```php
// Do slow work OUTSIDE the transaction
$result = $this->httpClient->get('https://external-api.com/validate');

$this->atomic(function () use ($result) {
    $item = $this->mapper->find($id, $userId);
    $item->setStatus($result->getStatus());
    $this->mapper->update($item);
}, $this->db);
```
