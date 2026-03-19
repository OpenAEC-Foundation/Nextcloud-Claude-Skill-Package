# Database Anti-Patterns — Ranked by Severity

## Critical (Data Loss / Security Risk)

### AP-C1: SQL Injection via String Concatenation

**Severity**: CRITICAL — Security vulnerability
**NEVER** concatenate user input into SQL queries. ALWAYS use `$qb->createNamedParameter()`.

```php
// DANGEROUS — SQL injection
$qb->where("user_id = '$userId'");
$qb->where($qb->expr()->eq('user_id', "'$userId'"));

// SAFE
$qb->where($qb->expr()->eq('user_id', $qb->createNamedParameter($userId)));
```

### AP-C2: Transaction Without Rollback

**Severity**: CRITICAL — Data corruption
**NEVER** use manual `beginTransaction()` without try/catch/rollBack. ALWAYS use `TTransactional` trait.

```php
// DANGEROUS — partial commit on error
$this->db->beginTransaction();
$this->mapper->insert($entity1);
$this->mapper->insert($entity2); // If this fails, entity1 is committed alone
$this->db->commit();

// SAFE
$this->atomic(function () {
    $this->mapper->insert($entity1);
    $this->mapper->insert($entity2);
}, $this->db);
```

### AP-C3: Modifying Deployed Migrations

**Severity**: CRITICAL — Schema divergence between users
**NEVER** edit a migration file after it has been released. ALWAYS create a new migration class.

Existing users who already ran the migration will have a different schema than new users. This causes unpredictable errors that are extremely difficult to diagnose.

---

## High (Functionality Broken on Some Databases)

### AP-H1: Table Name Exceeds 23 Characters

**Severity**: HIGH — Breaks Oracle installations
**NEVER** use table names longer than 23 characters. The `oc_` prefix adds 4 characters, reaching Oracle's 30-character identifier limit.

| Name | Length | With `oc_` | Oracle? |
|------|--------|-----------|---------|
| `myapp_proj_collabs` | 19 | 23 | OK |
| `myapp_items` | 12 | 16 | OK |
| `myapp_project_collaborators` | 28 | 32 | FAILS |
| `myapp_notification_preferences` | 31 | 35 | FAILS |

### AP-H2: NOT NULL Boolean Column

**Severity**: HIGH — Breaks Oracle installations
**NEVER** use `'notnull' => true` on boolean columns. Oracle does not support NOT NULL constraints on boolean types.

### AP-H3: NOT NULL String with Empty Default

**Severity**: HIGH — Breaks Oracle installations
**NEVER** combine `'notnull' => true` with `'default' => ''` on string columns. Oracle treats empty strings as NULL, causing constraint violations.

### AP-H4: String Column Exceeds 4,000 Characters

**Severity**: HIGH — Breaks Oracle installations
**NEVER** use `Types::STRING` for content that may exceed 4,000 characters. Use `Types::TEXT` (CLOB) instead.

### AP-H5: Identifier Names Exceeding 30 Characters

**Severity**: HIGH — Breaks Oracle installations
**NEVER** use column, index, or foreign key names longer than 30 characters.

### AP-H6: Table Without Primary Key

**Severity**: HIGH — Breaks Galera Cluster replication
**NEVER** create a table without a primary key. ALWAYS include an auto-incremented `id BIGINT` column with `setPrimaryKey(['id'])`.

### AP-H7: Raw SQL Queries

**Severity**: HIGH — Breaks portability across databases
**NEVER** use raw SQL strings. ALWAYS use the query builder. Raw SQL with MySQL syntax will fail on PostgreSQL, SQLite, or Oracle.

---

## Medium (Resource Leaks / Subtle Bugs)

### AP-M1: Unclosed Result Cursors

**Severity**: MEDIUM — Connection pool exhaustion under load
**NEVER** forget to call `$result->closeCursor()` after processing query results. Open cursors hold database connections.

**Exception**: `QBMapper::findEntity()` and `findEntities()` close cursors automatically.

### AP-M2: Missing addType() in Entity

**Severity**: MEDIUM — Type mismatches in application logic
**NEVER** omit `addType()` for non-string properties. Without it, integers return as `"5"` (string) and booleans return as `"1"` (string).

### AP-M3: Data Migration in changeSchema()

**Severity**: MEDIUM — Data operation fails silently or with confusing error
**NEVER** run data queries in `changeSchema()`. The schema change has not been applied yet. Use `postSchemaChange()` instead.

### AP-M4: Missing Existence Checks in Migrations

**Severity**: MEDIUM — Crashes on re-run or during development
**NEVER** call `createTable()` or `addColumn()` without checking `hasTable()` / `hasColumn()` first.

### AP-M5: Non-Unique Index Names

**Severity**: MEDIUM — Collision with other apps
**NEVER** use generic index names like `user_id_idx`. ALWAYS prefix with app name: `myapp_items_uid_idx`.

### AP-M6: Unescaped LIKE Parameters

**Severity**: MEDIUM — Unexpected query results
**NEVER** pass user input directly into LIKE patterns. ALWAYS use `$this->db->escapeLikeParameter()`.

### AP-M7: Including oc_ Prefix in Table Names

**Severity**: MEDIUM — Table not found (doubled prefix)
**NEVER** include the `oc_` prefix when passing table names to QBMapper or query builder. The prefix is added automatically.

### AP-M8: Long-Running Operations Inside Transactions

**Severity**: MEDIUM — Lock contention and timeouts
**NEVER** perform HTTP calls, file I/O, or heavy computation inside `$this->atomic()`. Do slow work outside, then wrap only the database writes in a transaction.

---

## Low (Maintainability / Best Practice)

### AP-L1: Wrong Migration Naming Convention

**Severity**: LOW — Confusing ordering, possible tooling issues
**ALWAYS** use the pattern `Version{MajorMinor}Date{YYYYMMDDHHmmss}`. Example: `Version1000Date20240315143022`.

### AP-L2: Missing Entity Type Declarations

**Severity**: LOW — Code clarity
**ALWAYS** declare property types (`protected ?int`, `protected ?bool`) alongside `addType()` calls for IDE support and type safety.

### AP-L3: Manual Transaction Management

**Severity**: LOW — Error-prone compared to `TTransactional`
**ALWAYS** prefer `TTransactional` trait over manual `beginTransaction()` / `commit()` / `rollBack()`. The trait handles exceptions, rollback, and nested transactions (savepoints) automatically.

---

## Anti-Pattern Decision Matrix

When reviewing database code, check these in order:

| Check | If Found | Action |
|-------|----------|--------|
| String concatenation in queries | SQL injection risk | Replace with `createNamedParameter()` immediately |
| Raw SQL (`executeQuery($sql)`) | Portability broken | Rewrite using query builder |
| Modified existing migration | Schema divergence | Create new migration, revert old |
| `notnull: true` on boolean | Oracle breaks | Change to `notnull: false` |
| Table name > 23 chars | Oracle breaks | Shorten name |
| No `closeCursor()` after query | Connection leak | Add `closeCursor()` call |
| No `addType()` for int/bool | Type bugs | Add `addType()` in constructor |
| No `hasTable()` / `hasColumn()` guard | Crash on re-run | Add existence check |
| No primary key on table | Galera breaks | Add `setPrimaryKey()` |
| Generic index name | Name collision | Add app prefix |
| Slow ops in transaction | Lock timeouts | Move outside `atomic()` |
