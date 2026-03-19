# Database Error Types & Constraint Violations

## Exception Types

### Doctrine DBAL Exceptions

| Exception | Cause | Typical Fix |
|-----------|-------|-------------|
| `Doctrine\DBAL\Exception\TableExistsException` | `createTable()` called for existing table | Add `$schema->hasTable()` guard |
| `Doctrine\DBAL\Exception\TableNotFoundException` | Query references non-existent table | Check table name, remove `oc_` prefix duplication |
| `Doctrine\DBAL\Exception\UniqueConstraintViolationException` | Duplicate value on unique column/index | Check for existing row before insert, or use `insertOrUpdate()` |
| `Doctrine\DBAL\Exception\ForeignKeyConstraintViolationException` | FK reference to non-existent parent row | Verify parent record exists before inserting child |
| `Doctrine\DBAL\Exception\NotNullConstraintViolationException` | NULL inserted into NOT NULL column | Provide default value or make column nullable |
| `Doctrine\DBAL\Exception\InvalidFieldNameException` | Column does not exist in table | Check column name spelling, verify migration ran |
| `Doctrine\DBAL\Exception\SyntaxErrorException` | Invalid SQL generated | Stop using raw SQL, use query builder instead |
| `Doctrine\DBAL\Exception\ConnectionException` | Database unreachable or credentials wrong | Check `config.php` database settings |
| `Doctrine\DBAL\Exception\LockWaitTimeoutException` | Transaction held lock too long | Move slow operations outside transaction |
| `Doctrine\DBAL\Exception\DeadlockException` | Circular lock dependency between transactions | Reduce transaction scope, retry with backoff |

### Nextcloud App Framework Exceptions

| Exception | Thrown By | Cause |
|-----------|----------|-------|
| `OCP\AppFramework\Db\DoesNotExistException` | `QBMapper::findEntity()` | Query returned 0 rows |
| `OCP\AppFramework\Db\MultipleObjectsReturnedException` | `QBMapper::findEntity()` | Query returned 2+ rows |

### Oracle-Specific Errors

| Error Code | Message | Cause | Fix |
|------------|---------|-------|-----|
| `ORA-00972` | identifier is too long | Table/column/index/FK name exceeds 30 chars | Shorten name (table max 23, others max 30) |
| `ORA-01400` | cannot insert NULL | NOT NULL constraint on boolean or empty-string default | Remove NOT NULL from boolean; use NULL default for strings |
| `ORA-01461` | can bind a LONG value only for insert | String value exceeds 4,000 chars in VARCHAR2 | Use `Types::TEXT` (CLOB) for long content |
| `ORA-00942` | table or view does not exist | Table name too long and was silently truncated | Keep table name within 23 characters |

### PostgreSQL-Specific Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `column "X" does not exist` | Case-sensitive column names in raw SQL | Use query builder (handles quoting automatically) |
| `operator does not exist: integer = character varying` | Type mismatch in comparison | Use `createNamedParameter()` with correct type constant |

---

## Migration Tracking

### How Nextcloud Tracks Migrations

Nextcloud stores executed migration records in the `oc_migrations` table:

| Column | Type | Purpose |
|--------|------|---------|
| `app` | VARCHAR | App ID |
| `version` | VARCHAR | Full migration class name |

**Key behavior**:
- Migrations are executed in alphabetical order by class name
- Once a migration class name appears in `oc_migrations`, it NEVER runs again
- Modifying an executed migration has NO effect on existing installations
- Deleting a row from `oc_migrations` will cause the migration to re-run (development only, NEVER in production)

### Diagnostic: Check Migration Status

```bash
# Via occ command
sudo -u www-data php occ migrations:status myapp

# Via database query (for debugging only)
SELECT * FROM oc_migrations WHERE app = 'myapp' ORDER BY version;
```

---

## Constraint Violation Matrix

### Oracle Constraints

| Data Type | `notnull: true` | `notnull: false` | `default: ''` | `default: null` |
|-----------|----------------|------------------|---------------|-----------------|
| `Types::STRING` | OK (if default is non-empty) | OK | FAILS (empty = NULL) | OK |
| `Types::BOOLEAN` | FAILS | OK | N/A | OK |
| `Types::INTEGER` | OK | OK | N/A | OK |
| `Types::BIGINT` | OK | OK | N/A | OK |
| `Types::TEXT` | OK | OK | FAILS | OK |

### Identifier Length Limits

| Identifier | Oracle Limit | Effective Limit | Reason |
|------------|-------------|-----------------|--------|
| Table name | 30 chars total | 23 chars (app provides) | `oc_` prefix adds 4 chars, leave margin |
| Column name | 30 chars | 30 chars | No prefix added |
| Index name | 30 chars | 30 chars | No prefix added |
| FK constraint name | 30 chars | 30 chars | No prefix added |
| Sequence name | 30 chars | 30 chars | Auto-generated for autoincrement |

### Galera Cluster Requirements

| Requirement | Consequence If Missing |
|-------------|----------------------|
| Primary key on every table | Rows cannot be identified for replication; writes on one node may not appear on others |
| No MyISAM tables | Galera only replicates InnoDB; MyISAM changes are lost |
| No explicit table locking | `LOCK TABLES` causes cluster-wide issues; use `TTransactional` instead |

---

## Query Builder Type Constants

ALWAYS use the correct type constant when creating named parameters to avoid type mismatch errors:

| Constant | Use For | Example |
|----------|---------|---------|
| `IQueryBuilder::PARAM_STR` | String values (default) | `createNamedParameter('hello')` |
| `IQueryBuilder::PARAM_INT` | Integer values | `createNamedParameter(42, IQueryBuilder::PARAM_INT)` |
| `IQueryBuilder::PARAM_BOOL` | Boolean values | `createNamedParameter(true, IQueryBuilder::PARAM_BOOL)` |
| `IQueryBuilder::PARAM_DATE` | DateTime objects | `createNamedParameter($date, IQueryBuilder::PARAM_DATE)` |
| `IQueryBuilder::PARAM_STR_ARRAY` | String arrays (IN clause) | `createNamedParameter(['a','b'], IQueryBuilder::PARAM_STR_ARRAY)` |
| `IQueryBuilder::PARAM_INT_ARRAY` | Integer arrays (IN clause) | `createNamedParameter([1,2], IQueryBuilder::PARAM_INT_ARRAY)` |

**Common mistake**: Omitting the type parameter for non-string values causes PostgreSQL type mismatch errors. MySQL is more lenient with implicit type casting, so this bug often goes unnoticed until testing on PostgreSQL.

---

## Error Resolution Flowchart

```
Database error occurred
├── Exception contains "migration"?
│   ├── "already exists" → Add hasTable()/hasColumn() guard (E-02)
│   ├── "does not exist" in changeSchema → Move data query to postSchemaChange (E-03)
│   └── Schema not applied on upgrade → Check if migration was modified (E-01)
├── Exception contains "ORA-"?
│   ├── ORA-00972 → Shorten identifier name (E-12, E-15)
│   ├── ORA-01400 → Fix NOT NULL constraint (E-13, E-14)
│   └── ORA-01461 → Use Types::TEXT instead of Types::STRING (E-16)
├── Exception is DoesNotExistException?
│   └── Query returned 0 rows → Check query parameters and data existence
├── Exception is MultipleObjectsReturnedException?
│   └── Query returned 2+ rows → Add more specific WHERE conditions
├── "Too many connections"?
│   └── Missing closeCursor() calls (E-07)
└── "Table not found: oc_oc_"?
    └── Remove oc_ prefix from table name parameter (E-11)
```
