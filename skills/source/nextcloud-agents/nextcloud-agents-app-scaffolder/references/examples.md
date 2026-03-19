# Complete Scaffolded App Example

## Scenario

A user requests: "Create a Nextcloud app called `tasklist` for managing personal tasks with a Vue.js frontend, database storage, and navigation entry."

**Collected inputs:**
- App ID: `tasklist`
- Display name: Task List
- Namespace: `TaskList`
- Description: A personal task management app for Nextcloud
- Author: Jane Developer (jane@example.com)
- License: AGPL-3.0-or-later
- NC range: 28-32
- Category: organization
- Database: yes, entity = Task
- Vue.js frontend: yes
- Navigation entry: yes
- OCS API: no
- Background jobs: no
- Admin settings: no

---

## Generated Files

### appinfo/info.xml

```xml
<?xml version="1.0"?>
<info xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:noNamespaceSchemaLocation="https://apps.nextcloud.com/schema/apps/info.xsd">
    <id>tasklist</id>
    <name>Task List</name>
    <summary>A personal task management app for Nextcloud</summary>
    <description><![CDATA[Manage your personal tasks directly in Nextcloud. Create, edit, and track tasks with a clean Vue.js interface.]]></description>
    <version>0.1.0</version>
    <licence>AGPL-3.0-or-later</licence>
    <author mail="jane@example.com">Jane Developer</author>
    <namespace>TaskList</namespace>
    <category>organization</category>
    <bugs>https://github.com/janedeveloper/tasklist/issues</bugs>
    <dependencies>
        <nextcloud min-version="28" max-version="32"/>
        <php min-version="8.1"/>
    </dependencies>
    <navigations>
        <navigation>
            <name>Task List</name>
            <route>tasklist.page.index</route>
            <icon>app.svg</icon>
            <order>10</order>
        </navigation>
    </navigations>
</info>
```

### appinfo/routes.php

```php
<?php

declare(strict_types=1);

return [
    'routes' => [
        ['name' => 'page#index', 'url' => '/', 'verb' => 'GET'],
        ['name' => 'task#index', 'url' => '/api/tasks', 'verb' => 'GET'],
        ['name' => 'task#show', 'url' => '/api/tasks/{id}', 'verb' => 'GET'],
        ['name' => 'task#create', 'url' => '/api/tasks', 'verb' => 'POST'],
        ['name' => 'task#update', 'url' => '/api/tasks/{id}', 'verb' => 'PUT'],
        ['name' => 'task#destroy', 'url' => '/api/tasks/{id}', 'verb' => 'DELETE'],
    ],
];
```

### lib/AppInfo/Application.php

```php
<?php

declare(strict_types=1);

namespace OCA\TaskList\AppInfo;

use OCP\AppFramework\App;
use OCP\AppFramework\Bootstrap\IBootstrap;
use OCP\AppFramework\Bootstrap\IBootContext;
use OCP\AppFramework\Bootstrap\IRegistrationContext;

class Application extends App implements IBootstrap {
    public const APP_ID = 'tasklist';

    public function __construct() {
        parent::__construct(self::APP_ID);
    }

    public function register(IRegistrationContext $context): void {
    }

    public function boot(IBootContext $context): void {
    }
}
```

### lib/Controller/PageController.php

```php
<?php

declare(strict_types=1);

namespace OCA\TaskList\Controller;

use OCA\TaskList\AppInfo\Application;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http\Attribute\NoAdminRequired;
use OCP\AppFramework\Http\Attribute\NoCSRFRequired;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\IRequest;

class PageController extends Controller {
    public function __construct(IRequest $request) {
        parent::__construct(Application::APP_ID, $request);
    }

    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function index(): TemplateResponse {
        return new TemplateResponse(Application::APP_ID, 'main');
    }
}
```

### lib/Controller/TaskController.php

```php
<?php

declare(strict_types=1);

namespace OCA\TaskList\Controller;

use OCA\TaskList\AppInfo\Application;
use OCA\TaskList\Service\TaskService;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\Attribute\NoAdminRequired;
use OCP\AppFramework\Http\JSONResponse;
use OCP\IRequest;

class TaskController extends Controller {
    public function __construct(
        IRequest $request,
        private TaskService $service,
        private ?string $userId,
    ) {
        parent::__construct(Application::APP_ID, $request);
    }

    #[NoAdminRequired]
    public function index(): JSONResponse {
        return new JSONResponse($this->service->findAll($this->userId));
    }

    #[NoAdminRequired]
    public function show(int $id): JSONResponse {
        return $this->handleNotFound(fn () => $this->service->find($id, $this->userId));
    }

    #[NoAdminRequired]
    public function create(string $title, string $description = '', bool $completed = false): JSONResponse {
        return new JSONResponse(
            $this->service->create($title, $description, $completed, $this->userId),
            Http::STATUS_CREATED
        );
    }

    #[NoAdminRequired]
    public function update(int $id, string $title, string $description = '', bool $completed = false): JSONResponse {
        return $this->handleNotFound(
            fn () => $this->service->update($id, $title, $description, $completed, $this->userId)
        );
    }

    #[NoAdminRequired]
    public function destroy(int $id): JSONResponse {
        return $this->handleNotFound(
            fn () => $this->service->delete($id, $this->userId)
        );
    }

    private function handleNotFound(callable $callback): JSONResponse {
        try {
            return new JSONResponse($callback());
        } catch (\OCP\AppFramework\Db\DoesNotExistException $e) {
            return new JSONResponse([], Http::STATUS_NOT_FOUND);
        }
    }
}
```

### lib/Service/TaskService.php

```php
<?php

declare(strict_types=1);

namespace OCA\TaskList\Service;

use OCA\TaskList\Db\Task;
use OCA\TaskList\Db\TaskMapper;
use OCP\AppFramework\Db\DoesNotExistException;
use Psr\Log\LoggerInterface;

class TaskService {
    public function __construct(
        private TaskMapper $mapper,
        private LoggerInterface $logger,
    ) {
    }

    /** @return Task[] */
    public function findAll(string $userId): array {
        return $this->mapper->findAll($userId);
    }

    /** @throws DoesNotExistException */
    public function find(int $id, string $userId): Task {
        return $this->mapper->find($id, $userId);
    }

    public function create(string $title, string $description, bool $completed, string $userId): Task {
        $task = new Task();
        $task->setTitle($title);
        $task->setDescription($description);
        $task->setCompleted($completed);
        $task->setUserId($userId);
        return $this->mapper->insert($task);
    }

    /** @throws DoesNotExistException */
    public function update(int $id, string $title, string $description, bool $completed, string $userId): Task {
        $task = $this->mapper->find($id, $userId);
        $task->setTitle($title);
        $task->setDescription($description);
        $task->setCompleted($completed);
        return $this->mapper->update($task);
    }

    /** @throws DoesNotExistException */
    public function delete(int $id, string $userId): Task {
        $task = $this->mapper->find($id, $userId);
        $this->mapper->delete($task);
        return $task;
    }
}
```

### lib/Db/Task.php

```php
<?php

declare(strict_types=1);

namespace OCA\TaskList\Db;

use OCP\AppFramework\Db\Entity;

/**
 * @method string getTitle()
 * @method void setTitle(string $title)
 * @method string getDescription()
 * @method void setDescription(string $description)
 * @method bool getCompleted()
 * @method void setCompleted(bool $completed)
 * @method string getUserId()
 * @method void setUserId(string $userId)
 */
class Task extends Entity implements \JsonSerializable {
    protected ?string $title = null;
    protected ?string $description = null;
    protected ?bool $completed = null;
    protected ?string $userId = null;

    public function __construct() {
        $this->addType('id', 'integer');
        $this->addType('completed', 'boolean');
    }

    public function jsonSerialize(): array {
        return [
            'id' => $this->id,
            'title' => $this->title,
            'description' => $this->description,
            'completed' => $this->completed,
            'userId' => $this->userId,
        ];
    }
}
```

### lib/Db/TaskMapper.php

```php
<?php

declare(strict_types=1);

namespace OCA\TaskList\Db;

use OCP\AppFramework\Db\QBMapper;
use OCP\IDBConnection;

/** @extends QBMapper<Task> */
class TaskMapper extends QBMapper {
    public function __construct(IDBConnection $db) {
        parent::__construct($db, 'tasklist_tasks');
    }

    /** @throws \OCP\AppFramework\Db\DoesNotExistException */
    public function find(int $id, string $userId): Task {
        $qb = $this->db->getQueryBuilder();
        $qb->select('*')
            ->from($this->getTableName())
            ->where($qb->expr()->eq('id', $qb->createNamedParameter($id)))
            ->andWhere($qb->expr()->eq('user_id', $qb->createNamedParameter($userId)));
        return $this->findEntity($qb);
    }

    /** @return Task[] */
    public function findAll(string $userId): array {
        $qb = $this->db->getQueryBuilder();
        $qb->select('*')
            ->from($this->getTableName())
            ->where($qb->expr()->eq('user_id', $qb->createNamedParameter($userId)));
        return $this->findEntities($qb);
    }
}
```

### lib/Migration/Version1000Date20260319120000.php

```php
<?php

declare(strict_types=1);

namespace OCA\TaskList\Migration;

use Closure;
use OCP\DB\ISchemaWrapper;
use OCP\DB\Types;
use OCP\Migration\IOutput;
use OCP\Migration\SimpleMigrationStep;

class Version1000Date20260319120000 extends SimpleMigrationStep {
    public function changeSchema(IOutput $output, Closure $schemaClosure, array $options): ?ISchemaWrapper {
        /** @var ISchemaWrapper $schema */
        $schema = $schemaClosure();

        if (!$schema->hasTable('tasklist_tasks')) {
            $table = $schema->createTable('tasklist_tasks');

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
            $table->addColumn('completed', Types::BOOLEAN, [
                'notnull' => false,
                'default' => false,
            ]);
            $table->addColumn('user_id', Types::STRING, [
                'notnull' => true,
                'length' => 64,
            ]);

            $table->setPrimaryKey(['id']);
            $table->addIndex(['user_id'], 'tasklist_task_uid_idx');
        }

        return $schema;
    }
}
```

### src/main.js

```javascript
import Vue from 'vue'
import App from './App.vue'

const appElement = document.getElementById('content')

// eslint-disable-next-line no-new
new Vue({
    el: appElement,
    render: h => h(App),
})
```

### src/App.vue

```vue
<template>
    <NcContent app-name="tasklist">
        <NcAppContent>
            <div class="tasklist-main">
                <div class="tasklist-header">
                    <h2>Tasks</h2>
                    <NcButton type="primary" @click="showNewTaskForm = true">
                        <template #icon>
                            <Plus :size="20" />
                        </template>
                        New Task
                    </NcButton>
                </div>

                <NcEmptyContent v-if="tasks.length === 0 && !loading"
                    name="No tasks yet"
                    description="Create your first task to get started">
                </NcEmptyContent>

                <div v-else class="tasklist-items">
                    <NcListItem v-for="task in tasks"
                        :key="task.id"
                        :name="task.title"
                        :bold="!task.completed"
                        :details="task.completed ? 'Done' : 'Pending'"
                        @click="toggleComplete(task)">
                        <template #actions>
                            <NcActionButton @click="deleteTask(task.id)">
                                Delete
                            </NcActionButton>
                        </template>
                    </NcListItem>
                </div>
            </div>
        </NcAppContent>
    </NcContent>
</template>

<script>
import NcContent from '@nextcloud/vue/components/NcContent'
import NcAppContent from '@nextcloud/vue/components/NcAppContent'
import NcEmptyContent from '@nextcloud/vue/components/NcEmptyContent'
import NcListItem from '@nextcloud/vue/components/NcListItem'
import NcButton from '@nextcloud/vue/components/NcButton'
import NcActionButton from '@nextcloud/vue/components/NcActionButton'
import Plus from 'vue-material-design-icons/Plus.vue'
import axios from '@nextcloud/axios'
import { generateUrl } from '@nextcloud/router'
import { showError, showSuccess } from '@nextcloud/dialogs'
import '@nextcloud/dialogs/style.css'

export default {
    name: 'App',
    components: {
        NcContent,
        NcAppContent,
        NcEmptyContent,
        NcListItem,
        NcButton,
        NcActionButton,
        Plus,
    },
    data() {
        return {
            tasks: [],
            loading: true,
            showNewTaskForm: false,
        }
    },
    async mounted() {
        try {
            const response = await axios.get(generateUrl('/apps/tasklist/api/tasks'))
            this.tasks = response.data
        } catch (e) {
            showError('Could not load tasks')
            console.error(e)
        } finally {
            this.loading = false
        }
    },
    methods: {
        async toggleComplete(task) {
            try {
                const response = await axios.put(
                    generateUrl(`/apps/tasklist/api/tasks/${task.id}`),
                    {
                        title: task.title,
                        description: task.description,
                        completed: !task.completed,
                    },
                )
                const index = this.tasks.findIndex(t => t.id === task.id)
                this.$set(this.tasks, index, response.data)
            } catch (e) {
                showError('Could not update task')
            }
        },
        async deleteTask(id) {
            try {
                await axios.delete(generateUrl(`/apps/tasklist/api/tasks/${id}`))
                this.tasks = this.tasks.filter(t => t.id !== id)
                showSuccess('Task deleted')
            } catch (e) {
                showError('Could not delete task')
            }
        },
    },
}
</script>

<style scoped lang="scss">
.tasklist-main {
    padding: 20px;
    color: var(--color-main-text);
}

.tasklist-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    h2 {
        margin: 0;
    }
}
</style>
```

### templates/main.php

```php
<?php

script('tasklist', 'tasklist-main');
style('tasklist', 'style');
?>

<div id="app-content">
    <div id="content"></div>
</div>
```

### webpack.config.js

```javascript
const webpackConfig = require('@nextcloud/webpack-vue-config')

module.exports = webpackConfig
```

### package.json

```json
{
    "name": "tasklist",
    "version": "0.1.0",
    "private": true,
    "scripts": {
        "build": "webpack --node-env production --progress",
        "dev": "webpack --node-env development --progress",
        "watch": "webpack --node-env development --progress --watch",
        "serve": "webpack --node-env development serve --progress",
        "lint": "eslint --ext .js,.vue src",
        "lint:fix": "eslint --ext .js,.vue src --fix"
    },
    "dependencies": {
        "@nextcloud/axios": "^2.4.0",
        "@nextcloud/dialogs": "^5.0.0",
        "@nextcloud/initial-state": "^2.1.0",
        "@nextcloud/router": "^3.0.0",
        "@nextcloud/vue": "^8.0.0",
        "vue": "^2.7.16",
        "vue-material-design-icons": "^5.3.0"
    },
    "devDependencies": {
        "@nextcloud/eslint-config": "^8.3.0",
        "@nextcloud/webpack-vue-config": "^6.0.0",
        "vue-loader": "^15.11.1"
    }
}
```

### composer.json

```json
{
    "name": "janedeveloper/tasklist",
    "description": "A personal task management app for Nextcloud",
    "type": "project",
    "license": "AGPL-3.0-or-later",
    "require": {
        "php": ">=8.1"
    },
    "require-dev": {
        "phpunit/phpunit": "^10.0",
        "nextcloud/ocp": "dev-master"
    },
    "autoload": {
        "psr-4": {
            "OCA\\TaskList\\": "lib/"
        }
    },
    "autoload-dev": {
        "psr-4": {
            "OCA\\TaskList\\Tests\\": "tests/"
        }
    },
    "config": {
        "optimize-autoloader": true
    }
}
```

### phpunit.xml

```xml
<?xml version="1.0" encoding="utf-8" ?>
<phpunit bootstrap="tests/bootstrap.php"
         colors="true"
         failOnRisky="true"
         failOnWarning="true">
    <testsuites>
        <testsuite name="unit">
            <directory>./tests/Unit</directory>
        </testsuite>
    </testsuites>
    <coverage>
        <include>
            <directory suffix=".php">./lib</directory>
        </include>
    </coverage>
</phpunit>
```

### tests/bootstrap.php

```php
<?php

declare(strict_types=1);

require_once __DIR__ . '/../../../tests/bootstrap.php';
```

### tests/Unit/Service/TaskServiceTest.php

```php
<?php

declare(strict_types=1);

namespace OCA\TaskList\Tests\Unit\Service;

use OCA\TaskList\Db\Task;
use OCA\TaskList\Db\TaskMapper;
use OCA\TaskList\Service\TaskService;
use OCP\AppFramework\Db\DoesNotExistException;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

class TaskServiceTest extends TestCase {
    private TaskService $service;
    private TaskMapper $mapper;

    protected function setUp(): void {
        parent::setUp();

        $this->mapper = $this->createMock(TaskMapper::class);
        $logger = $this->createMock(LoggerInterface::class);
        $this->service = new TaskService($this->mapper, $logger);
    }

    public function testFindAll(): void {
        $userId = 'testuser';

        $this->mapper->expects($this->once())
            ->method('findAll')
            ->with($userId)
            ->willReturn([new Task(), new Task()]);

        $result = $this->service->findAll($userId);
        $this->assertCount(2, $result);
    }

    public function testFind(): void {
        $task = new Task();
        $task->setTitle('Test Task');

        $this->mapper->expects($this->once())
            ->method('find')
            ->with(1, 'testuser')
            ->willReturn($task);

        $result = $this->service->find(1, 'testuser');
        $this->assertEquals('Test Task', $result->getTitle());
    }

    public function testFindNotFound(): void {
        $this->mapper->expects($this->once())
            ->method('find')
            ->willThrowException(new DoesNotExistException(''));

        $this->expectException(DoesNotExistException::class);
        $this->service->find(999, 'testuser');
    }

    public function testCreate(): void {
        $task = new Task();

        $this->mapper->expects($this->once())
            ->method('insert')
            ->willReturn($task);

        $result = $this->service->create('New Task', 'Description', false, 'testuser');
        $this->assertInstanceOf(Task::class, $result);
    }

    public function testDelete(): void {
        $task = new Task();

        $this->mapper->expects($this->once())
            ->method('find')
            ->with(1, 'testuser')
            ->willReturn($task);

        $this->mapper->expects($this->once())
            ->method('delete')
            ->with($task);

        $result = $this->service->delete(1, 'testuser');
        $this->assertInstanceOf(Task::class, $result);
    }
}
```

### css/style.scss

```scss
#app-content {
    .tasklist-main {
        min-height: 100%;
        padding: 20px;
    }
}
```

### img/app.svg

```xml
<svg xmlns="http://www.w3.org/2000/svg" height="16" width="16" viewBox="0 0 16 16">
    <path d="M3 2h10a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1zm4.5 8.5l4-4-1-1-3 3-1.5-1.5-1 1z" fill="#222"/>
</svg>
```

---

## Post-Generation Checklist

After generating all files, the agent MUST verify:

1. `info.xml` `<id>` matches directory name (`tasklist`)
2. `info.xml` `<namespace>` matches PHP namespace (`TaskList`)
3. `info.xml` `<route>` in navigation matches `routes.php` (`tasklist.page.index`)
4. All PHP files have `declare(strict_types=1)`
5. All controller methods have appropriate `#[NoAdminRequired]` attributes
6. Entity properties (camelCase) match migration columns (snake_case)
7. Mapper table name matches migration table name (`tasklist_tasks`)
8. `package.json` includes `@nextcloud/dialogs/style.css` import in components using toasts
9. `webpack.config.js` uses `@nextcloud/webpack-vue-config`
10. Template `script()` call matches webpack entry point name
