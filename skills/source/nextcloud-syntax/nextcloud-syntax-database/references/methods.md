# Database Layer — API Reference

## Migration API

### SimpleMigrationStep

Base class: `OCP\Migration\SimpleMigrationStep`

| Method | Phase | Purpose |
|--------|-------|---------|
| `preSchemaChange(IOutput $output, Closure $schemaClosure, array $options)` | Before schema | Data backup before destructive schema changes |
| `changeSchema(IOutput $output, Closure $schemaClosure, array $options): ?ISchemaWrapper` | Schema | Create/modify/drop tables and columns. MUST return `$schema` or `null` |
| `postSchemaChange(IOutput $output, Closure $schemaClosure, array $options)` | After schema | Data migration, seeding, transformation |

**Constructor injection**: Migrations support DI. Inject `IDBConnection` for data operations in `postSchemaChange()`.

```php
class Version1000Date20240101000000 extends SimpleMigrationStep {
    public function __construct(private IDBConnection $db) {}
}
```

### ISchemaWrapper Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `hasTable(string $name)` | bool | Check if table exists (without `oc_` prefix) |
| `createTable(string $name)` | Table | Create new table |
| `getTable(string $name)` | Table | Get existing table for modification |
| `dropTable(string $name)` | void | Drop table |
| `getTableNames()` | string[] | List all table names |

### Table Methods (Doctrine DBAL Table)

| Method | Description |
|--------|-------------|
| `addColumn(string $name, string $type, array $options)` | Add column |
| `changeColumn(string $name, array $options)` | Modify column options |
| `dropColumn(string $name)` | Remove column |
| `hasColumn(string $name)` | Check column existence |
| `setPrimaryKey(array $columns)` | Define primary key |
| `addIndex(array $columns, string $name)` | Add index |
| `addUniqueIndex(array $columns, string $name)` | Add unique index |
| `dropIndex(string $name)` | Remove index |
| `hasIndex(string $name)` | Check index existence |

### Column Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `notnull` | bool | true | NOT NULL constraint |
| `length` | int | -- | Max length (STRING type) |
| `default` | mixed | -- | Default value |
| `autoincrement` | bool | false | Auto-increment (BIGINT id columns) |
| `unsigned` | bool | false | Unsigned integer |
| `precision` | int | -- | Decimal precision |
| `scale` | int | -- | Decimal scale |

### Migration Metadata Attributes (NC 30+)

Descriptive attributes on migration classes for tooling and documentation:

```php
use OCP\Migration\Attributes\CreateTable;
use OCP\Migration\Attributes\AddColumn;
use OCP\Migration\Attributes\ModifyColumn;
use OCP\Migration\Attributes\DropColumn;
use OCP\Migration\Attributes\AddIndex;
use OCP\Migration\Attributes\DropIndex;
use OCP\Migration\Attributes\DropTable;
use OCP\Migration\Attributes\ColumnType;

#[CreateTable(table: 'myapp_items', description: 'Stores user items')]
#[AddColumn(table: 'myapp_items', name: 'priority', type: ColumnType::INTEGER)]
class Version30000Date20240729185117 extends SimpleMigrationStep {}
```

---

## Entity API

### Base Class: `OCP\AppFramework\Db\Entity`

#### Auto-Generated Methods

For every `protected` property, Entity generates:
- `get{PropertyName}()` -- getter
- `set{PropertyName}($value)` -- setter (marks field as updated)
- `is{PropertyName}()` -- boolean getter (for bool properties)

#### Core Methods

| Method | Description |
|--------|-------------|
| `addType(string $property, string $type)` | Register type cast for a property |
| `getId()` | Get entity ID (inherited) |
| `setId(int $id)` | Set entity ID (inherited) |
| `getUpdatedFields()` | Get array of modified field names |
| `resetUpdatedFields()` | Clear modification tracking |
| `columnToProperty(string $column)` | Convert `snake_case` column to `camelCase` property |
| `propertyToColumn(string $property)` | Convert `camelCase` property to `snake_case` column |

#### Type Cast Values for `addType()`

| Value | PHP Type | Notes |
|-------|----------|-------|
| `'integer'` | int | Integer conversion |
| `'float'` | float | Float conversion |
| `'boolean'` | bool | Boolean conversion |
| `'datetime'` | \DateTime | DateTime from DB timestamp |
| `'json'` | array | JSON decode/encode |
| `'blob'` | resource | Stream resource |

#### Static Factory Method

```php
$entity = Item::fromRow([
    'id' => 1,
    'user_id' => 'admin',
    'title' => 'Test',
]);
```

---

## QBMapper API

### Base Class: `OCP\AppFramework\Db\QBMapper`

#### Constructor

```php
parent::__construct(
    IDBConnection $db,
    string $tableName,       // WITHOUT oc_ prefix
    ?string $entityClass = null  // Entity FQCN for auto-mapping
);
```

#### CRUD Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `insert` | `insert(Entity $entity): Entity` | INSERT and set generated ID on entity |
| `update` | `update(Entity $entity): Entity` | UPDATE only changed fields |
| `delete` | `delete(Entity $entity): Entity` | DELETE by entity ID |
| `insertOrUpdate` | `insertOrUpdate(Entity $entity): Entity` | UPSERT (INSERT or UPDATE on conflict) |

#### Query Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `findEntity` | `findEntity(IQueryBuilder $qb): Entity` | Fetch single entity. Throws `DoesNotExistException` if 0 rows, `MultipleObjectsReturnedException` if 2+ rows |
| `findEntities` | `findEntities(IQueryBuilder $qb): array` | Fetch array of entities. Returns empty array if no matches |

#### Utility Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `getTableName` | `getTableName(): string` | Returns table name (with prefix applied) |
| `mapRowToEntity` | `mapRowToEntity(array $row): Entity` | Convert DB row to Entity instance |

---

## QueryBuilder API

### Obtaining a QueryBuilder

```php
$qb = $this->db->getQueryBuilder();
```

### Select Operations

| Method | Description |
|--------|-------------|
| `select(string ...$columns)` | Select specific columns |
| `selectAlias(string $column, string $alias)` | Select with alias |
| `selectDistinct(string $column)` | Select distinct values |
| `addSelect(string ...$columns)` | Add columns to existing select |
| `from(string $table, ?string $alias)` | Set FROM table (without `oc_` prefix) |

### Join Operations

| Method | Signature |
|--------|-----------|
| `join` | `join(string $fromAlias, string $table, string $alias, string $condition)` |
| `innerJoin` | `innerJoin(string $fromAlias, string $table, string $alias, string $condition)` |
| `leftJoin` | `leftJoin(string $fromAlias, string $table, string $alias, string $condition)` |
| `rightJoin` | `rightJoin(string $fromAlias, string $table, string $alias, string $condition)` |

### WHERE Clause

| Method | Description |
|--------|-------------|
| `where(string $predicate)` | Set WHERE (replaces existing) |
| `andWhere(string $predicate)` | Add AND condition |
| `orWhere(string $predicate)` | Add OR condition |

### Expression Builder (`$qb->expr()`)

| Method | SQL Equivalent |
|--------|---------------|
| `eq($column, $value)` | `column = value` |
| `neq($column, $value)` | `column != value` |
| `gt($column, $value)` | `column > value` |
| `gte($column, $value)` | `column >= value` |
| `lt($column, $value)` | `column < value` |
| `lte($column, $value)` | `column <= value` |
| `isNull($column)` | `column IS NULL` |
| `isNotNull($column)` | `column IS NOT NULL` |
| `like($column, $value)` | `column LIKE value` |
| `iLike($column, $value)` | Case-insensitive LIKE |
| `notLike($column, $value)` | `column NOT LIKE value` |
| `in($column, $value)` | `column IN (...)` |
| `notIn($column, $value)` | `column NOT IN (...)` |
| `andX(...$predicates)` | Combine with AND |
| `orX(...$predicates)` | Combine with OR |
| `literal($value)` | SQL literal value |

### Parameters

| Method | Description |
|--------|-------------|
| `createNamedParameter($value, $type)` | Bind named parameter (SQL injection safe) |
| `createPositionalParameter($value, $type)` | Bind positional parameter |
| `createParameter(string $name)` | Create unbound parameter placeholder |
| `setParameter(string $name, $value, $type)` | Bind value to parameter |

**Parameter types** (`IQueryBuilder` constants):
- `IQueryBuilder::PARAM_STR` -- string (default)
- `IQueryBuilder::PARAM_INT` -- integer
- `IQueryBuilder::PARAM_BOOL` -- boolean
- `IQueryBuilder::PARAM_DATE` -- DateTime
- `IQueryBuilder::PARAM_STR_ARRAY` -- array of strings (for `IN`)
- `IQueryBuilder::PARAM_INT_ARRAY` -- array of integers (for `IN`)

### Ordering and Limiting

| Method | Description |
|--------|-------------|
| `orderBy(string $column, string $direction)` | ORDER BY (ASC/DESC) |
| `addOrderBy(string $column, string $direction)` | Additional ORDER BY |
| `setMaxResults(int $limit)` | LIMIT |
| `setFirstResult(int $offset)` | OFFSET |
| `groupBy(string ...$columns)` | GROUP BY |
| `addGroupBy(string ...$columns)` | Additional GROUP BY |
| `having(string $predicate)` | HAVING clause |

### Write Operations

| Method | Description |
|--------|-------------|
| `insert(string $table)` | INSERT INTO |
| `setValue(string $column, string $value)` | Set column value for INSERT |
| `values(array $values)` | Set all values for INSERT |
| `update(string $table)` | UPDATE |
| `set(string $column, string $value)` | SET column for UPDATE |
| `delete(string $table)` | DELETE FROM |

### Execution

| Method | Returns | Use For |
|--------|---------|---------|
| `executeQuery()` | `IResult` | SELECT queries |
| `executeStatement()` | int (affected rows) | INSERT/UPDATE/DELETE |

### IResult Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `fetch()` | array\|false | Fetch next row as numeric+associative array |
| `fetchAssociative()` | array\|false | Fetch next row as associative array |
| `fetchOne()` | mixed\|false | Fetch single column from next row |
| `fetchAll()` | array | Fetch all rows |
| `closeCursor()` | void | **ALWAYS call after processing results** |

---

## IDBConnection Methods

| Method | Description |
|--------|-------------|
| `getQueryBuilder()` | Get new QueryBuilder instance |
| `beginTransaction()` | Start transaction |
| `commit()` | Commit transaction |
| `rollBack()` | Rollback transaction |
| `getDatabasePlatform()` | Get Doctrine platform for DB-specific logic |
| `insertIfNotExist(string $table, array $input, ?array $compare)` | Conditional insert |

---

## TTransactional Trait

```php
use OCP\DB\TTransactional;

class MyService {
    use TTransactional;

    public function atomicOperation(): mixed {
        return $this->atomic(function () {
            // All DB operations here run in a single transaction
            // Return value is passed through
            // Exceptions trigger automatic rollback
            return $result;
        }, $this->db);
    }
}
```

**Signature**: `atomic(callable $callback, IDBConnection $db): mixed`

- Wraps `$callback` in `beginTransaction()` / `commit()`
- Calls `rollBack()` on any exception, then re-throws
- Supports nested calls (uses savepoints)
