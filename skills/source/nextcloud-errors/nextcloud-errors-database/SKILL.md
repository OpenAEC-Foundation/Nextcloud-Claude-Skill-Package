---
name: nextcloud-errors-database
description: "Diagnoses and resolves Nextcloud database errors including migration failures, query builder mistakes, entity mapping issues, type mismatches, Oracle and Galera cluster constraints, index problems, and table naming violations. Activates when encountering database errors, migration problems, or query failures."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

# nextcloud-errors-database

## Quick Diagnostic Reference

### Error Category Index

| Symptom | Category | Jump To |
|---------|----------|---------|
| Migration runs but nothing changes | Migration | [E-01](#e-01-modified-existing-migration) |
| `Table already exists` exception | Migration | [E-02](#e-02-missing-existence-check) |
| Data migration reads NULL for new column | Migration | [E-03](#e-03-data-migration-in-changeschema) |
| `Migration name does not match` warning | Migration | [E-04](#e-04-wrong-migration-naming) |
| SQL syntax error on Oracle/PostgreSQL | Query | [E-05](#e-05-raw-sql-instead-of-query-builder) |
| SQL injection vulnerability detected | Query | [E-06](#e-06-string-concatenation-in-queries) |
| Database connection exhausted / timeouts | Query | [E-07](#e-07-unclosed-result-cursors) |
| LIKE query returns unexpected results | Query | [E-08](#e-08-unescaped-like-parameters) |
| Entity property returns string instead of int | Entity | [E-09](#e-09-missing-addtype-in-entity) |
| Column not found for entity property | Entity | [E-10](#e-10-camelcase-snake_case-mismatch) |
| `Table not found: oc_oc_myapp_items` | Entity | [E-11](#e-11-oc_-prefix-included-in-table-name) |
| `ORA-00972: identifier is too long` | Oracle | [E-12](#e-12-table-name-exceeds-23-characters) |
| `ORA-01400: cannot insert NULL` on boolean | Oracle | [E-13](#e-13-not-null-boolean-column) |
| `ORA-01400: cannot insert NULL` on string | Oracle | [E-14](#e-14-not-null-string-with-empty-default) |
| `ORA-00972` on column/index/FK name | Oracle | [E-15](#e-15-identifier-exceeds-30-characters) |
| `ORA-01461: can bind LONG value only` | Oracle | [E-16](#e-16-string-exceeds-4000-characters) |
| Replication fails silently | Galera | [E-17](#e-17-table-without-primary-key) |
| Duplicate index name across apps | Index | [E-18](#e-18-non-unique-index-names) |
| Partial insert committed on error | Transaction | [E-19](#e-19-missing-transaction-rollback) |
| Lock timeout / deadlock in transaction | Transaction | [E-20](#e-20-slow-operations-inside-transaction) |

---

## Migration Errors

### E-01: Modified Existing Migration

**Symptom**: Migration runs without errors but schema changes do not appear. New installations work correctly but upgrades do not.

**Cause**: An already-executed migration file was edited. Nextcloud stores executed migration class names in `oc_migrations` and NEVER re-runs them.

**Fix**: ALWAYS create a new migration class for any schema change after the original migration has been committed.

```php
// WRONG: Editing Version1000Date20240101000000 after deployment
// CORRECT: Create Version1001Date20240215000000 with the change
class Version1001Date20240215000000 extends SimpleMigrationStep {
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

### E-02: Missing Existence Check

**Symptom**: `Doctrine\DBAL\Exception\TableExistsException` or `column already exists` during migration.

**Cause**: Migration calls `createTable()` or `addColumn()` without checking if the table or column already exists.

**Fix**: ALWAYS wrap creation calls with `hasTable()` / `hasColumn()` guards.

```php
if (!$schema->hasTable('myapp_items')) {
    $table = $schema->createTable('myapp_items');
    // ...
}
// For columns:
$table = $schema->getTable('myapp_items');
if (!$table->hasColumn('new_col')) {
    $table->addColumn('new_col', Types::STRING, ['notnull' => false, 'length' => 255]);
}
```

### E-03: Data Migration in changeSchema()

**Symptom**: Query in `changeSchema()` fails because the new column does not exist yet, or data reads return NULL for newly added columns.

**Cause**: `changeSchema()` defines the schema diff but the actual SQL has NOT been executed yet. Data queries against new columns fail.

**Fix**: ALWAYS use `postSchemaChange()` for data operations.

```php
public function changeSchema(...): ?ISchemaWrapper {
    // Schema changes ONLY — no data queries
    return $schema;
}

public function postSchemaChange(IOutput $output, Closure $schemaClosure, array $options): void {
    // Data operations AFTER schema is applied
    $qb = $this->db->getQueryBuilder();
    $qb->update('myapp_items')->set('new_col', 'old_col')->executeStatement();
}
```

### E-04: Wrong Migration Naming

**Symptom**: Nextcloud logs warnings about migration naming or migrations run in unexpected order.

**Cause**: Migration class name does not follow `Version{MajorMinor}Date{YYYYMMDDHHmmss}` convention.

**Fix**: ALWAYS use the correct naming pattern. Version mapping: `1.0.x => Version1000`, `2.4.x => Version2004`, `24.0.x => Version24000`.

---

## Query Builder Errors

### E-05: Raw SQL Instead of Query Builder

**Symptom**: Query works on MySQL but fails on PostgreSQL, SQLite, or Oracle with syntax errors.

**Cause**: Raw SQL uses MySQL-specific syntax (backtick quoting, `LIMIT` syntax, `IFNULL`).

**Fix**: NEVER use raw SQL. ALWAYS use the query builder for cross-database portability.

```php
// WRONG
$this->db->executeQuery("SELECT * FROM oc_myapp_items WHERE user_id = '$userId'");

// CORRECT
$qb = $this->db->getQueryBuilder();
$qb->select('*')
    ->from('myapp_items')
    ->where($qb->expr()->eq('user_id', $qb->createNamedParameter($userId)));
$result = $qb->executeQuery();
```

### E-06: String Concatenation in Queries

**Symptom**: SQL injection vulnerability. Unexpected query results or database corruption.

**Cause**: User input concatenated directly into query strings instead of using named parameters.

**Fix**: ALWAYS use `$qb->createNamedParameter()` for ALL query values.

```php
// WRONG — SQL injection
$qb->where("user_id = '$userId'");
$qb->where($qb->expr()->eq('user_id', "'$userId'"));

// CORRECT
$qb->where($qb->expr()->eq('user_id', $qb->createNamedParameter($userId)));
```

### E-07: Unclosed Result Cursors

**Symptom**: Database connection pool exhaustion. "Too many connections" errors. Memory leaks during long-running operations.

**Cause**: `closeCursor()` not called after processing query results. Open cursors hold database connections.

**Fix**: ALWAYS call `$result->closeCursor()` after processing. Note: `QBMapper::findEntity()` and `findEntities()` close cursors automatically.

```php
$result = $qb->executeQuery();
$rows = $result->fetchAll();
$result->closeCursor(); // NEVER forget this
return $rows;
```

### E-08: Unescaped LIKE Parameters

**Symptom**: LIKE query returns unexpected results when user input contains `%` or `_` characters.

**Cause**: SQL wildcards in user input are not escaped before use in LIKE expressions.

**Fix**: ALWAYS use `$this->db->escapeLikeParameter()` for user input in LIKE queries.

```php
// WRONG
$qb->andWhere($qb->expr()->like('name', $qb->createNamedParameter('%' . $userInput . '%')));

// CORRECT
$qb->andWhere($qb->expr()->iLike('name',
    $qb->createNamedParameter('%' . $this->db->escapeLikeParameter($userInput) . '%')));
```

---

## Entity Mapping Errors

### E-09: Missing addType() in Entity

**Symptom**: Entity property typed as `?int` returns string `"5"` instead of integer `5`. Boolean property returns `"1"` instead of `true`.

**Cause**: The `addType()` call is missing in the entity constructor. Without it, all database values are returned as strings.

**Fix**: ALWAYS call `addType()` for every non-string property in the entity constructor.

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

### E-10: CamelCase/snake_case Mismatch

**Symptom**: `Column not found` error when loading entities. Entity properties are NULL despite data existing in the database.

**Cause**: Entity property name does not match the expected column mapping. Nextcloud auto-converts `camelCase` properties to `snake_case` columns (`phoneNumber` maps to `phone_number`).

**Fix**: ALWAYS verify that entity property names in camelCase match the database column names in snake_case. Override `columnToProperty()` / `propertyToColumn()` only for non-standard mappings.

### E-11: oc_ Prefix Included in Table Name

**Symptom**: `Table not found: oc_oc_myapp_items`. The prefix is doubled.

**Cause**: The `oc_` prefix was manually included when passing the table name to QBMapper or query builder. The prefix is added automatically.

**Fix**: NEVER include the `oc_` prefix in table names passed to QBMapper constructors or query builder `from()` calls.

```php
// WRONG
parent::__construct($db, 'oc_myapp_items', Item::class);

// CORRECT
parent::__construct($db, 'myapp_items', Item::class);
```

---

## Oracle Constraint Errors

### E-12: Table Name Exceeds 23 Characters

**Symptom**: `ORA-00972: identifier is too long` during migration on Oracle.

**Cause**: Table name exceeds 23 characters. With the `oc_` prefix (4 chars), the total exceeds Oracle's 30-character identifier limit.

**Fix**: ALWAYS keep table names at 23 characters or fewer.

```php
// WRONG: 'myapp_project_collaborators' = 28 chars → oc_ prefix = 32
// CORRECT: 'myapp_proj_collabs' = 18 chars → oc_ prefix = 22
```

### E-13: NOT NULL Boolean Column

**Symptom**: `ORA-01400: cannot insert NULL` when inserting rows with boolean columns on Oracle.

**Cause**: Boolean column declared as `NOT NULL`. Oracle does not support NOT NULL constraints on boolean columns.

**Fix**: NEVER use `'notnull' => true` on boolean columns.

```php
// WRONG
$table->addColumn('is_active', Types::BOOLEAN, ['notnull' => true, 'default' => false]);

// CORRECT
$table->addColumn('is_active', Types::BOOLEAN, ['notnull' => false, 'default' => false]);
```

### E-14: NOT NULL String with Empty Default

**Symptom**: `ORA-01400: cannot insert NULL` when inserting rows with empty string values on Oracle.

**Cause**: String column declared as `NOT NULL` with `'default' => ''`. Oracle treats empty strings as NULL, causing a constraint violation.

**Fix**: NEVER combine `NOT NULL` with an empty string default on string columns.

```php
// WRONG
$table->addColumn('label', Types::STRING, ['notnull' => true, 'default' => '', 'length' => 255]);

// CORRECT
$table->addColumn('label', Types::STRING, ['notnull' => false, 'default' => null, 'length' => 255]);
```

### E-15: Identifier Exceeds 30 Characters

**Symptom**: `ORA-00972: identifier is too long` for column names, index names, or foreign key names.

**Cause**: Identifier exceeds Oracle's 30-character limit.

**Fix**: ALWAYS keep column, index, and foreign key names at 30 characters or fewer.

### E-16: String Exceeds 4000 Characters

**Symptom**: `ORA-01461: can bind a LONG value only for insert` when storing long strings.

**Cause**: String column value exceeds Oracle's 4,000-character VARCHAR2 limit.

**Fix**: Use `Types::TEXT` (CLOB) instead of `Types::STRING` for columns that may contain more than 4,000 characters.

---

## Galera Cluster Errors

### E-17: Table Without Primary Key

**Symptom**: Data written on one cluster node does not appear on other nodes. Replication fails silently.

**Cause**: Table created without a primary key. Galera Cluster uses row-based replication and requires primary keys on ALL tables.

**Fix**: ALWAYS define a primary key on every table. ALWAYS include an auto-incremented `id BIGINT` column.

```php
$table = $schema->createTable('myapp_logs');
$table->addColumn('id', Types::BIGINT, ['autoincrement' => true, 'notnull' => true]);
$table->addColumn('message', Types::TEXT, ['notnull' => false]);
$table->setPrimaryKey(['id']); // NEVER omit this
```

---

## Index Errors

### E-18: Non-Unique Index Names

**Symptom**: `Index already exists` error during migration. Another app uses the same index name.

**Cause**: Index name is too generic (e.g., `user_id_idx`). Index names must be unique across the entire database.

**Fix**: ALWAYS prefix index names with your app name: `{appname}_{table}_{columns}_idx`.

```php
// WRONG
$table->addIndex(['user_id'], 'user_id_idx');

// CORRECT
$table->addIndex(['user_id'], 'myapp_items_uid_idx');
```

---

## Transaction Errors

### E-19: Missing Transaction Rollback

**Symptom**: Partial data committed after an error. Database in inconsistent state.

**Cause**: Manual `beginTransaction()` / `commit()` without try/catch and `rollBack()`.

**Fix**: ALWAYS use the `TTransactional` trait instead of manual transaction management.

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

### E-20: Slow Operations Inside Transaction

**Symptom**: Lock timeouts, deadlocks, or degraded performance under load.

**Cause**: Long-running operations (HTTP calls, file I/O, heavy computation) executed inside a database transaction, holding locks.

**Fix**: ALWAYS perform slow operations OUTSIDE the transaction. Only database reads/writes belong inside `$this->atomic()`.

---

## Oracle/Galera Constraint Quick Reference

| Constraint | Limit | Error If Violated |
|------------|-------|-------------------|
| Table name | Max 23 chars | `ORA-00972` |
| Column name | Max 30 chars | `ORA-00972` |
| Index name | Max 30 chars | `ORA-00972` |
| FK name | Max 30 chars | `ORA-00972` |
| String column length | Max 4,000 chars | `ORA-01461` |
| Boolean NOT NULL | NOT allowed | `ORA-01400` |
| String NOT NULL + empty default | NOT allowed | `ORA-01400` |
| Primary key | REQUIRED on every table | Galera silent replication failure |

---

## Reference Links

- [references/methods.md](references/methods.md) -- Database error types, constraint violations, diagnostic queries
- [references/examples.md](references/examples.md) -- Error scenarios with complete fix walkthroughs
- [references/anti-patterns.md](references/anti-patterns.md) -- Database mistakes ranked by severity

### Official Sources

- https://docs.nextcloud.com/server/latest/developer_manual/digging_deeper/database.html
- https://docs.nextcloud.com/server/latest/developer_manual/basics/storage/database.html
