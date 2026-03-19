# Database Layer — Examples

## Migration Examples

### Example 1: Create Table with Multiple Column Types

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

        if (!$schema->hasTable('myapp_projects')) {
            $table = $schema->createTable('myapp_projects');
            $table->addColumn('id', Types::BIGINT, [
                'autoincrement' => true,
                'notnull' => true,
            ]);
            $table->addColumn('user_id', Types::STRING, [
                'notnull' => true,
                'length' => 64,
            ]);
            $table->addColumn('name', Types::STRING, [
                'notnull' => true,
                'length' => 255,
            ]);
            $table->addColumn('description', Types::TEXT, [
                'notnull' => false,
                'default' => null,
            ]);
            $table->addColumn('status', Types::INTEGER, [
                'notnull' => true,
                'default' => 0,
            ]);
            $table->addColumn('metadata', Types::JSON, [
                'notnull' => false,
                'default' => null,
            ]);
            $table->addColumn('is_public', Types::BOOLEAN, [
                'notnull' => false,
                'default' => false,
            ]);
            $table->addColumn('created_at', Types::DATETIME, [
                'notnull' => true,
            ]);
            $table->addColumn('updated_at', Types::DATETIME, [
                'notnull' => false,
            ]);

            $table->setPrimaryKey(['id']);
            $table->addIndex(['user_id'], 'myapp_proj_uid_idx');
            $table->addIndex(['status'], 'myapp_proj_status_idx');
            $table->addUniqueIndex(['user_id', 'name'], 'myapp_proj_uid_name');
        }

        return $schema;
    }
}
```

### Example 2: Add Column to Existing Table

```php
<?php
namespace OCA\MyApp\Migration;

use Closure;
use OCP\DB\ISchemaWrapper;
use OCP\DB\Types;
use OCP\Migration\IOutput;
use OCP\Migration\SimpleMigrationStep;

class Version1001Date20240215000000 extends SimpleMigrationStep {

    public function changeSchema(IOutput $output, Closure $schemaClosure, array $options): ?ISchemaWrapper {
        /** @var ISchemaWrapper $schema */
        $schema = $schemaClosure();

        $table = $schema->getTable('myapp_projects');

        if (!$table->hasColumn('priority')) {
            $table->addColumn('priority', Types::INTEGER, [
                'notnull' => true,
                'default' => 0,
            ]);
        }

        return $schema;
    }
}
```

### Example 3: Rename Column (Three-Step Pattern)

Column renames require three separate migration classes to maintain data integrity:

**Step 1: Add the new column**
```php
class Version1002Date20240301000000 extends SimpleMigrationStep {

    public function changeSchema(IOutput $output, Closure $schemaClosure, array $options): ?ISchemaWrapper {
        $schema = $schemaClosure();
        $table = $schema->getTable('myapp_projects');

        if (!$table->hasColumn('owner_id')) {
            $table->addColumn('owner_id', Types::STRING, [
                'notnull' => false,
                'length' => 64,
            ]);
        }

        return $schema;
    }
}
```

**Step 2: Copy data from old to new column**
```php
class Version1002Date20240301000001 extends SimpleMigrationStep {

    public function __construct(private IDBConnection $db) {}

    public function postSchemaChange(IOutput $output, Closure $schemaClosure, array $options): void {
        $qb = $this->db->getQueryBuilder();
        $qb->update('myapp_projects')
            ->set('owner_id', 'user_id')
            ->executeStatement();
    }
}
```

**Step 3: Drop the old column and add NOT NULL**
```php
class Version1002Date20240301000002 extends SimpleMigrationStep {

    public function changeSchema(IOutput $output, Closure $schemaClosure, array $options): ?ISchemaWrapper {
        $schema = $schemaClosure();
        $table = $schema->getTable('myapp_projects');

        if ($table->hasColumn('user_id')) {
            $table->dropColumn('user_id');
        }

        $table->changeColumn('owner_id', [
            'notnull' => true,
        ]);

        return $schema;
    }
}
```

### Example 4: Migration with Metadata Attributes (NC 30+)

```php
<?php
namespace OCA\MyApp\Migration;

use Closure;
use OCP\DB\ISchemaWrapper;
use OCP\DB\Types;
use OCP\Migration\Attributes\AddColumn;
use OCP\Migration\Attributes\AddIndex;
use OCP\Migration\Attributes\ColumnType;
use OCP\Migration\IOutput;
use OCP\Migration\SimpleMigrationStep;

#[AddColumn(table: 'myapp_projects', name: 'archived_at', type: ColumnType::DATETIME)]
#[AddIndex(table: 'myapp_projects', name: 'myapp_proj_archive_idx')]
class Version1003Date20240401000000 extends SimpleMigrationStep {

    public function changeSchema(IOutput $output, Closure $schemaClosure, array $options): ?ISchemaWrapper {
        $schema = $schemaClosure();
        $table = $schema->getTable('myapp_projects');

        if (!$table->hasColumn('archived_at')) {
            $table->addColumn('archived_at', Types::DATETIME, [
                'notnull' => false,
                'default' => null,
            ]);
            $table->addIndex(['archived_at'], 'myapp_proj_archive_idx');
        }

        return $schema;
    }
}
```

---

## Entity Examples

### Example 5: Entity with All Common Types

```php
<?php
namespace OCA\MyApp\Db;

use OCP\AppFramework\Db\Entity;

class Project extends Entity {
    protected ?string $userId = null;
    protected ?string $name = null;
    protected ?string $description = null;
    protected ?int $status = null;
    protected ?bool $isPublic = null;
    protected ?float $budget = null;
    protected ?array $metadata = null;
    protected ?\DateTime $createdAt = null;
    protected ?\DateTime $updatedAt = null;

    public function __construct() {
        $this->addType('status', 'integer');
        $this->addType('isPublic', 'boolean');
        $this->addType('budget', 'float');
        $this->addType('metadata', 'json');
        $this->addType('createdAt', 'datetime');
        $this->addType('updatedAt', 'datetime');
    }
}
```

**Auto-generated methods** (examples):
- `$project->getUserId()` / `$project->setUserId('admin')`
- `$project->getIsPublic()` / `$project->setIsPublic(true)`
- `$project->getMetadata()` / `$project->setMetadata(['key' => 'value'])`

**Column mapping**:
- `$userId` maps to column `user_id`
- `$isPublic` maps to column `is_public`
- `$createdAt` maps to column `created_at`

### Example 6: Entity with Custom Column Mapping

```php
<?php
namespace OCA\MyApp\Db;

use OCP\AppFramework\Db\Entity;

class LegacyItem extends Entity {
    protected ?string $itemTitle = null;

    public function columnToProperty(string $columnName): string {
        if ($columnName === 'item_name') {
            return 'itemTitle';
        }
        return parent::columnToProperty($columnName);
    }

    public function propertyToColumn(string $property): string {
        if ($property === 'itemTitle') {
            return 'item_name';
        }
        return parent::propertyToColumn($property);
    }
}
```

---

## QBMapper Examples

### Example 7: Mapper with Filtered Queries

```php
<?php
namespace OCA\MyApp\Db;

use OCP\AppFramework\Db\DoesNotExistException;
use OCP\AppFramework\Db\MultipleObjectsReturnedException;
use OCP\AppFramework\Db\QBMapper;
use OCP\DB\QueryBuilder\IQueryBuilder;
use OCP\IDBConnection;

class ProjectMapper extends QBMapper {

    public function __construct(IDBConnection $db) {
        parent::__construct($db, 'myapp_projects', Project::class);
    }

    /**
     * @throws DoesNotExistException
     * @throws MultipleObjectsReturnedException
     */
    public function find(int $id, string $userId): Project {
        $qb = $this->db->getQueryBuilder();
        $qb->select('*')
            ->from($this->getTableName())
            ->where($qb->expr()->eq('id', $qb->createNamedParameter($id, IQueryBuilder::PARAM_INT)))
            ->andWhere($qb->expr()->eq('user_id', $qb->createNamedParameter($userId)));
        return $this->findEntity($qb);
    }

    /**
     * @return Project[]
     */
    public function findByStatus(string $userId, int $status): array {
        $qb = $this->db->getQueryBuilder();
        $qb->select('*')
            ->from($this->getTableName())
            ->where($qb->expr()->eq('user_id', $qb->createNamedParameter($userId)))
            ->andWhere($qb->expr()->eq('status', $qb->createNamedParameter($status, IQueryBuilder::PARAM_INT)))
            ->orderBy('created_at', 'DESC');
        return $this->findEntities($qb);
    }

    /**
     * @return Project[]
     */
    public function findPublicProjects(int $limit = 20, int $offset = 0): array {
        $qb = $this->db->getQueryBuilder();
        $qb->select('*')
            ->from($this->getTableName())
            ->where($qb->expr()->eq('is_public', $qb->createNamedParameter(true, IQueryBuilder::PARAM_BOOL)))
            ->orderBy('created_at', 'DESC')
            ->setMaxResults($limit)
            ->setFirstResult($offset);
        return $this->findEntities($qb);
    }

    /**
     * Search by name with LIKE
     * @return Project[]
     */
    public function search(string $userId, string $term): array {
        $qb = $this->db->getQueryBuilder();
        $qb->select('*')
            ->from($this->getTableName())
            ->where($qb->expr()->eq('user_id', $qb->createNamedParameter($userId)))
            ->andWhere($qb->expr()->iLike('name',
                $qb->createNamedParameter('%' . $this->db->escapeLikeParameter($term) . '%')))
            ->orderBy('name', 'ASC');
        return $this->findEntities($qb);
    }
}
```

### Example 8: Service Layer with Mapper

```php
<?php
namespace OCA\MyApp\Service;

use OCA\MyApp\Db\Project;
use OCA\MyApp\Db\ProjectMapper;
use OCP\AppFramework\Db\DoesNotExistException;
use OCP\AppFramework\Db\MultipleObjectsReturnedException;

class ProjectService {

    public function __construct(private ProjectMapper $mapper) {}

    /**
     * @throws NotFoundException
     */
    public function find(int $id, string $userId): Project {
        try {
            return $this->mapper->find($id, $userId);
        } catch (DoesNotExistException | MultipleObjectsReturnedException $e) {
            throw new NotFoundException($e->getMessage());
        }
    }

    public function create(string $name, string $userId): Project {
        $project = new Project();
        $project->setName($name);
        $project->setUserId($userId);
        $project->setStatus(0);
        $project->setCreatedAt(new \DateTime());
        return $this->mapper->insert($project);
    }

    public function update(int $id, string $name, string $userId): Project {
        $project = $this->mapper->find($id, $userId);
        $project->setName($name);
        $project->setUpdatedAt(new \DateTime());
        return $this->mapper->update($project);
    }

    public function delete(int $id, string $userId): Project {
        $project = $this->mapper->find($id, $userId);
        return $this->mapper->delete($project);
    }
}
```

---

## Query Builder Examples

### Example 9: JOIN with Aggregation

```php
$qb = $this->db->getQueryBuilder();
$qb->select('p.user_id')
    ->selectAlias($qb->func()->count('t.id'), 'task_count')
    ->from('myapp_projects', 'p')
    ->leftJoin('p', 'myapp_tasks', 't',
        $qb->expr()->eq('p.id', 't.project_id'))
    ->where($qb->expr()->eq('p.status', $qb->createNamedParameter(1, IQueryBuilder::PARAM_INT)))
    ->groupBy('p.user_id')
    ->having($qb->expr()->gt($qb->func()->count('t.id'), $qb->createNamedParameter(5, IQueryBuilder::PARAM_INT)))
    ->orderBy('task_count', 'DESC');

$result = $qb->executeQuery();
$rows = $result->fetchAll();
$result->closeCursor();
```

### Example 10: IN Clause with Array Parameter

```php
$qb = $this->db->getQueryBuilder();
$qb->select('*')
    ->from('myapp_projects')
    ->where($qb->expr()->in('status',
        $qb->createNamedParameter([1, 2, 3], IQueryBuilder::PARAM_INT_ARRAY)))
    ->andWhere($qb->expr()->in('user_id',
        $qb->createNamedParameter(['alice', 'bob'], IQueryBuilder::PARAM_STR_ARRAY)));

$result = $qb->executeQuery();
$rows = $result->fetchAll();
$result->closeCursor();
```

### Example 11: Subquery Pattern

```php
$subQuery = $this->db->getQueryBuilder();
$subQuery->select('project_id')
    ->from('myapp_tasks')
    ->where($subQuery->expr()->eq('status', $subQuery->createNamedParameter('done')));

$qb = $this->db->getQueryBuilder();
$qb->select('*')
    ->from('myapp_projects')
    ->where($qb->expr()->in('id', $qb->createFunction($subQuery->getSQL())));

$result = $qb->executeQuery();
$rows = $result->fetchAll();
$result->closeCursor();
```

### Example 12: Batch INSERT with Query Builder

```php
$qb = $this->db->getQueryBuilder();
$qb->insert('myapp_tasks')
    ->values([
        'project_id' => $qb->createParameter('projectId'),
        'title' => $qb->createParameter('title'),
        'created_at' => $qb->createParameter('createdAt'),
    ]);

foreach ($tasks as $task) {
    $qb->setParameter('projectId', $task['projectId'], IQueryBuilder::PARAM_INT);
    $qb->setParameter('title', $task['title']);
    $qb->setParameter('createdAt', new \DateTime(), IQueryBuilder::PARAM_DATE);
    $qb->executeStatement();
}
```

### Example 13: UPDATE with Expressions

```php
$qb = $this->db->getQueryBuilder();
$qb->update('myapp_projects')
    ->set('status', $qb->createNamedParameter(2, IQueryBuilder::PARAM_INT))
    ->set('updated_at', $qb->createNamedParameter(new \DateTime(), IQueryBuilder::PARAM_DATE))
    ->where($qb->expr()->eq('user_id', $qb->createNamedParameter($userId)))
    ->andWhere($qb->expr()->lt('created_at', $qb->createNamedParameter($cutoffDate, IQueryBuilder::PARAM_DATE)));

$affectedRows = $qb->executeStatement();
```

### Example 14: DELETE with Conditions

```php
$qb = $this->db->getQueryBuilder();
$qb->delete('myapp_tasks')
    ->where($qb->expr()->eq('project_id', $qb->createNamedParameter($projectId, IQueryBuilder::PARAM_INT)))
    ->andWhere($qb->expr()->eq('status', $qb->createNamedParameter('cancelled')));

$deletedCount = $qb->executeStatement();
```

---

## Transaction Examples

### Example 15: TTransactional with Return Value

```php
<?php
namespace OCA\MyApp\Service;

use OCA\MyApp\Db\Project;
use OCA\MyApp\Db\ProjectMapper;
use OCA\MyApp\Db\TaskMapper;
use OCP\DB\TTransactional;
use OCP\IDBConnection;

class ProjectService {
    use TTransactional;

    public function __construct(
        private ProjectMapper $projectMapper,
        private TaskMapper $taskMapper,
        private IDBConnection $db,
    ) {}

    public function createProjectWithTasks(string $name, array $taskTitles, string $userId): Project {
        return $this->atomic(function () use ($name, $taskTitles, $userId) {
            $project = new Project();
            $project->setName($name);
            $project->setUserId($userId);
            $project->setCreatedAt(new \DateTime());
            $project = $this->projectMapper->insert($project);

            foreach ($taskTitles as $title) {
                $task = new Task();
                $task->setProjectId($project->getId());
                $task->setTitle($title);
                $this->taskMapper->insert($task);
            }

            return $project;
        }, $this->db);
    }

    public function deleteProjectCascade(int $projectId, string $userId): void {
        $this->atomic(function () use ($projectId, $userId) {
            // Delete all tasks first
            $qb = $this->db->getQueryBuilder();
            $qb->delete('myapp_tasks')
                ->where($qb->expr()->eq('project_id', $qb->createNamedParameter($projectId)))
                ->executeStatement();

            // Then delete the project
            $project = $this->projectMapper->find($projectId, $userId);
            $this->projectMapper->delete($project);
        }, $this->db);
    }
}
```

---

## Index Management Examples

### Example 16: AddMissingIndicesEvent with replaceIndex (NC 29+)

```php
<?php
namespace OCA\MyApp\Listener;

use OCP\DB\Events\AddMissingIndicesEvent;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;

class DatabaseIndicesListener implements IEventListener {

    public function handle(Event $event): void {
        if (!$event instanceof AddMissingIndicesEvent) {
            return;
        }

        // Add a simple missing index
        $event->addMissingIndex(
            'myapp_projects',
            'myapp_proj_created_idx',
            ['created_at']
        );

        // Replace multiple old indices with one combined index
        $event->replaceIndex(
            'myapp_tasks',
            ['myapp_task_proj_idx', 'myapp_task_status_idx'],
            'myapp_task_proj_status_idx',
            ['project_id', 'status'],
            false  // not unique
        );
    }
}
```

Registration in `Application::register()`:
```php
$context->registerEventListener(
    AddMissingIndicesEvent::class,
    DatabaseIndicesListener::class
);
```
